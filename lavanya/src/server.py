"""
FastAPI server with WebSocket support for real-time speaker isolation system.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .config import config
from .audio_stream import AudioStreamer, AudioChunk
from .separation import RealTimeSpeechSeparator, SeparatedAudio
from .speaker_id import SpeakerIdentifier, SpeakerMatch
from .transcription import RealTimeTranscriber, TranscriptionResult

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.speaker_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str = None):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if session_id:
            self.speaker_sessions[session_id] = {
                "websocket": websocket,
                "connected_at": datetime.now(),
                "active_speakers": [],
                "transcripts": {}
            }
        
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Clean up session data
        sessions_to_remove = []
        for session_id, session_data in self.speaker_sessions.items():
            if session_data["websocket"] == websocket:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.speaker_sessions[session_id]
        
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific WebSocket connection."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected WebSockets."""
        if not self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_speaker_update(self, session_id: str, update_data: Dict[str, Any]):
        """Send speaker update to specific session."""
        if session_id in self.speaker_sessions:
            session = self.speaker_sessions[session_id]
            websocket = session["websocket"]
            
            message = {
                "type": "speaker_update",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "data": update_data
            }
            
            await self.send_personal_message(json.dumps(message), websocket)


class SpeakerIsolationServer:
    """Main server class for speaker isolation system."""
    
    def __init__(self):
        """Initialize server components."""
        self.app = FastAPI(
            title="Real-Time Speaker Isolation & Identification",
            description="API for real-time speaker separation, identification, and transcription",
            version="1.0.0"
        )
        
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Connection manager
        self.manager = ConnectionManager()
        
        # Core components
        self.audio_streamer = None
        self.speech_separator = None
        self.speaker_identifier = None
        self.transcriber = None
        
        # Processing state
        self.is_processing = False
        self.current_session = None
        
        # Setup routes
        self._setup_routes()
        
        logger.info("Speaker isolation server initialized")
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/")
        async def root():
            """Root endpoint with API information."""
            return {
                "message": "Real-Time Speaker Isolation & Identification API",
                "version": "1.0.0",
                "endpoints": {
                    "websocket": "/ws",
                    "start_session": "/api/sessions/start",
                    "stop_session": "/api/sessions/stop",
                    "enroll_speaker": "/api/speakers/enroll",
                    "list_speakers": "/api/speakers",
                    "get_transcripts": "/api/transcripts"
                }
            }
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            session_id = str(uuid.uuid4())
            await self.manager.connect(websocket, session_id)
            
            try:
                while True:
                    # Keep connection alive and handle incoming messages
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    if message.get("type") == "ping":
                        await self.manager.send_personal_message(
                            json.dumps({"type": "pong"}), 
                            websocket
                        )
                    
            except WebSocketDisconnect:
                self.manager.disconnect(websocket)
        
        @self.app.post("/api/sessions/start")
        async def start_session():
            """Start new speaker isolation session."""
            if self.is_processing:
                raise HTTPException(status_code=400, detail="Session already active")
            
            try:
                await self._start_processing()
                session_id = str(uuid.uuid4())
                self.current_session = session_id
                
                return {
                    "session_id": session_id,
                    "status": "started",
                    "message": "Speaker isolation session started"
                }
                
            except Exception as e:
                logger.error(f"Error starting session: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/sessions/stop")
        async def stop_session():
            """Stop current speaker isolation session."""
            if not self.is_processing:
                raise HTTPException(status_code=400, detail="No active session")
            
            try:
                await self._stop_processing()
                session_id = self.current_session
                self.current_session = None
                
                return {
                    "session_id": session_id,
                    "status": "stopped",
                    "message": "Speaker isolation session stopped"
                }
                
            except Exception as e:
                logger.error(f"Error stopping session: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/sessions/status")
        async def get_session_status():
            """Get current session status."""
            return {
                "is_processing": self.is_processing,
                "session_id": self.current_session,
                "active_speakers": self._get_active_speakers(),
                "total_connections": len(self.manager.active_connections)
            }
        
        @self.app.post("/api/speakers/enroll")
        async def enroll_speaker(
            name: str,
            audio_file: UploadFile = File(...)
        ):
            """Enroll new speaker with audio file."""
            try:
                # Read audio file
                audio_data = await audio_file.read()
                
                # Convert to numpy array (assuming WAV format)
                import soundfile as sf
                import io
                
                audio_array, sample_rate = sf.read(io.BytesIO(audio_data))
                
                # Enroll speaker
                speaker_id = str(uuid.uuid4())
                success = self.speaker_identifier.enroll_speaker(
                    speaker_id, name, audio_array, sample_rate
                )
                
                if success:
                    return {
                        "speaker_id": speaker_id,
                        "name": name,
                        "status": "enrolled",
                        "message": f"Speaker {name} enrolled successfully"
                    }
                else:
                    raise HTTPException(status_code=400, detail="Failed to enroll speaker")
                    
            except Exception as e:
                logger.error(f"Error enrolling speaker: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/speakers")
        async def list_speakers():
            """List all enrolled speakers."""
            try:
                speakers = self.speaker_identifier.database.list_speakers()
                speaker_list = []
                
                for speaker in speakers:
                    speaker_list.append({
                        "speaker_id": speaker.speaker_id,
                        "name": speaker.name,
                        "created_at": speaker.created_at,
                        "sample_count": speaker.sample_count
                    })
                
                return {
                    "speakers": speaker_list,
                    "total_count": len(speaker_list)
                }
                
            except Exception as e:
                logger.error(f"Error listing speakers: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/transcripts")
        async def get_transcripts():
            """Get current transcripts for all speakers."""
            try:
                transcripts = self.transcriber.get_all_transcripts()
                return {
                    "transcripts": transcripts,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error getting transcripts: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "audio_streamer": self.audio_streamer is not None,
                    "speech_separator": self.speech_separator is not None,
                    "speaker_identifier": self.speaker_identifier is not None,
                    "transcriber": self.transcriber is not None
                }
            }
    
    async def _start_processing(self):
        """Start the speaker isolation processing pipeline."""
        try:
            # Initialize components if not already done
            if not self.audio_streamer:
                self.audio_streamer = AudioStreamer()
            
            if not self.speech_separator:
                self.speech_separator = RealTimeSpeechSeparator()
            
            if not self.speaker_identifier:
                self.speaker_identifier = SpeakerIdentifier()
            
            if not self.transcriber:
                self.transcriber = RealTimeTranscriber()
            
            # Setup callbacks
            self.speech_separator.add_separation_callback(self._on_separated_audio)
            self.speaker_identifier.add_identification_callback(self._on_speaker_identified)
            self.transcriber.add_transcription_callback(self._on_transcription_complete)
            
            # Start audio streaming
            success = self.audio_streamer.start_streaming()
            if not success:
                raise RuntimeError("Failed to start audio streaming")
            
            # Start processing pipeline
            self.speech_separator.process_audio_stream(self.audio_streamer)
            
            self.is_processing = True
            logger.info("Speaker isolation processing started")
            
        except Exception as e:
            logger.error(f"Error starting processing: {e}")
            await self._stop_processing()
            raise
    
    async def _stop_processing(self):
        """Stop the speaker isolation processing pipeline."""
        try:
            # Stop audio streaming
            if self.audio_streamer:
                self.audio_streamer.stop_streaming()
            
            # Stop transcription
            if self.transcriber:
                self.transcriber.stop()
            
            self.is_processing = False
            logger.info("Speaker isolation processing stopped")
            
        except Exception as e:
            logger.error(f"Error stopping processing: {e}")
    
    def _on_separated_audio(self, separated_audio: SeparatedAudio):
        """Callback for separated audio."""
        try:
            # Identify speakers
            speaker_matches = self.speaker_identifier.identify_speakers(separated_audio)
            
            # Transcribe audio
            self.transcriber.transcribe_separated_audio(separated_audio, speaker_matches)
            
            # Send update to WebSocket clients
            asyncio.create_task(self._send_separation_update(separated_audio, speaker_matches))
            
        except Exception as e:
            logger.error(f"Error processing separated audio: {e}")
    
    def _on_speaker_identified(self, separated_audio: SeparatedAudio, speaker_matches: List[SpeakerMatch]):
        """Callback for speaker identification."""
        try:
            # Send speaker identification update
            asyncio.create_task(self._send_speaker_update(speaker_matches))
            
        except Exception as e:
            logger.error(f"Error processing speaker identification: {e}")
    
    def _on_transcription_complete(self, result: TranscriptionResult):
        """Callback for transcription completion."""
        try:
            # Send transcription update
            asyncio.create_task(self._send_transcription_update(result))
            
        except Exception as e:
            logger.error(f"Error processing transcription: {e}")
    
    async def _send_separation_update(self, separated_audio: SeparatedAudio, speaker_matches: List[SpeakerMatch]):
        """Send separation update to WebSocket clients."""
        update_data = {
            "type": "separation",
            "num_speakers": separated_audio.num_speakers,
            "confidence_scores": separated_audio.confidence_scores,
            "speaker_matches": [
                {
                    "speaker_id": match.speaker_id,
                    "name": match.name,
                    "confidence": match.confidence,
                    "is_unknown": match.is_unknown
                }
                for match in speaker_matches
            ]
        }
        
        await self.manager.broadcast(json.dumps(update_data))
    
    async def _send_speaker_update(self, speaker_matches: List[SpeakerMatch]):
        """Send speaker update to WebSocket clients."""
        update_data = {
            "type": "speakers",
            "active_speakers": [
                {
                    "speaker_id": match.speaker_id,
                    "name": match.name,
                    "confidence": match.confidence,
                    "is_unknown": match.is_unknown
                }
                for match in speaker_matches if not match.is_unknown
            ]
        }
        
        await self.manager.broadcast(json.dumps(update_data))
    
    async def _send_transcription_update(self, result: TranscriptionResult):
        """Send transcription update to WebSocket clients."""
        update_data = {
            "type": "transcription",
            "speaker_id": result.speaker_id,
            "speaker_name": result.speaker_name,
            "text": result.text,
            "confidence": result.confidence,
            "timestamp": result.timestamp,
            "is_final": result.is_final
        }
        
        await self.manager.broadcast(json.dumps(update_data))
    
    def _get_active_speakers(self) -> List[str]:
        """Get list of currently active speakers."""
        if self.speaker_identifier:
            return self.speaker_identifier.get_active_speakers()
        return []
    
    def run(self, host: str = None, port: int = None, websocket_port: int = None):
        """Run the FastAPI server."""
        host = host or config.get("server.host", "localhost")
        port = port or config.get("server.port", 8000)
        
        logger.info(f"Starting server on {host}:{port}")
        
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )


def create_server() -> SpeakerIsolationServer:
    """Create and configure the speaker isolation server."""
    return SpeakerIsolationServer()


def run_server(host: str = "localhost", port: int = 8000):
    """Run the speaker isolation server."""
    server = create_server()
    server.run(host=host, port=port)
