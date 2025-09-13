#!/usr/bin/env python3
"""
Demo script for the Real-Time Speaker Isolation & Identification system.

This script provides various demo modes for testing the system:
- Microphone input processing
- File-based processing
- Server mode with web interface
- Terminal-based interface
"""

import argparse
import asyncio
import logging
import signal
import sys
import time
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import config
from src.pipeline import create_default_pipeline, run_pipeline_demo
from src.server import create_server
from src.audio_stream import AudioFileStreamer
from src.separation import create_separator
from src.speaker_id import create_speaker_identifier
from src.transcription import create_transcriber
from src.utils import model_manager, performance_monitor

logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('speaker_isolation.log')
        ]
    )


def print_banner():
    """Print application banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║         Real-Time Speaker Isolation & Identification         ║
    ║                                                              ║
    ║  🎤 Advanced AI-powered speaker separation                  ║
    ║  🔍 Real-time speaker identification                        ║
    ║  📝 Live speech transcription                               ║
    ║  🌐 Web dashboard interface                                 ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_system_info():
    """Print system information and configuration."""
    print("\n📊 System Information:")
    print(f"   • Python version: {sys.version}")
    print(f"   • Configuration: {config.config_path}")
    print(f"   • Audio sample rate: {config.get('audio.sample_rate')} Hz")
    print(f"   • Chunk duration: {config.get('audio.chunk_duration')} s")
    print(f"   • Max speakers: {config.get('processing.max_speakers')}")
    print(f"   • Separation model: {config.get('models.separation.model_name')}")
    print(f"   • Speaker model: {config.get('models.speaker_recognition.model_name')}")
    print(f"   • Transcription model: {config.get('models.transcription.model_size')}")


def print_model_status():
    """Print model availability and cache status."""
    print("\n🤖 Model Status:")
    
    models = [
        ("Speech Separation", config.get("models.separation.model_name")),
        ("Speaker Recognition", config.get("models.speaker_recognition.model_name")),
        ("Transcription", f"whisper-{config.get('models.transcription.model_size')}")
    ]
    
    for model_type, model_name in models:
        if model_manager.is_model_cached(model_name):
            status = "✅ Cached"
        else:
            status = "⬇️  Will download"
        print(f"   • {model_type}: {model_name} - {status}")
    
    # Print cache statistics
    stats = model_manager.get_model_stats()
    print(f"\n   📁 Cache: {stats['cached_models']}/{stats['total_models']} models")
    if stats['cache_size_bytes'] > 0:
        size_mb = stats['cache_size_bytes'] / (1024 * 1024)
        print(f"   💾 Cache size: {size_mb:.1f} MB")


class DemoRunner:
    """Main demo runner class."""
    
    def __init__(self):
        """Initialize demo runner."""
        self.pipeline = None
        self.server = None
        self.is_running = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def _setup_pipeline_callbacks(self):
        """Setup pipeline callbacks for demo output."""
        def pipeline_callback(result):
            """Callback for pipeline results."""
            print(f"\n🎯 Pipeline Result:")
            print(f"   • Speakers detected: {result.separated_audio.num_speakers}")
            print(f"   • Processing time: {result.processing_time:.3f}s")
            
            for i, match in enumerate(result.speaker_matches):
                print(f"   • Speaker {i+1}: {match.name} "
                      f"(confidence: {match.confidence:.2f})")
            
            for result in result.transcription_results:
                if result.text.strip():
                    print(f"   📝 {result.speaker_name}: {result.text}")
        
        self.pipeline.add_pipeline_callback(pipeline_callback)
    
    async def run_microphone_demo(self):
        """Run demo with microphone input."""
        print("\n🎤 Starting microphone demo...")
        print("   Speak into your microphone. Press Ctrl+C to stop.")
        
        try:
            # Create and start pipeline
            self.pipeline = create_default_pipeline()
            self._setup_pipeline_callbacks()
            
            if self.pipeline.start():
                self.is_running = True
                print("✅ Pipeline started successfully!")
                
                # Keep running until interrupted
                while self.is_running:
                    await asyncio.sleep(1.0)
                    
                    # Print status every 30 seconds
                    status = self.pipeline.get_status()
                    if status["statistics"]["total_chunks_processed"] % 30 == 0 and \
                       status["statistics"]["total_chunks_processed"] > 0:
                        print(f"\n📊 Status: Processed {status['statistics']['total_chunks_processed']} chunks")
            else:
                print("❌ Failed to start pipeline")
                
        except Exception as e:
            logger.error(f"Error in microphone demo: {e}")
            print(f"❌ Demo error: {e}")
        
        finally:
            self.stop()
    
    async def run_file_demo(self, file_path: str):
        """Run demo with audio file input."""
        print(f"\n📁 Starting file demo with: {file_path}")
        
        try:
            # Create components
            file_streamer = AudioFileStreamer(file_path)
            separator = create_separator()
            speaker_id = create_speaker_identifier()
            transcriber = create_transcriber()
            
            # Process file
            print("🔄 Processing audio file...")
            
            def process_chunk(chunk):
                print(f"   Processing chunk: {chunk.duration:.2f}s")
                
                # Separate speakers
                separated = separator.separate_audio(chunk)
                print(f"   Separated into {separated.num_speakers} streams")
                
                # Identify speakers
                matches = speaker_id.identify_speakers(separated)
                for i, match in enumerate(matches):
                    print(f"   Speaker {i+1}: {match.name} (confidence: {match.confidence:.2f})")
                
                # Transcribe
                for i, stream in enumerate(separated.streams):
                    result = transcriber.transcribe_audio(stream, separated.sample_rate)
                    if result.text.strip():
                        print(f"   📝 Transcript {i+1}: {result.text}")
                
                print()
            
            file_streamer.add_chunk_callback(process_chunk)
            
            # Start processing
            await file_streamer.start_streaming(playback_speed=2.0)  # 2x speed for demo
            
            print("✅ File processing completed!")
            
        except Exception as e:
            logger.error(f"Error in file demo: {e}")
            print(f"❌ Demo error: {e}")
    
    async def run_server_demo(self, host: str = "localhost", port: int = 8000):
        """Run demo with web server."""
        print(f"\n🌐 Starting web server demo...")
        print(f"   Server will be available at: http://{host}:{port}")
        
        try:
            # Create and run server
            self.server = create_server()
            print("✅ Server started successfully!")
            print("   Open your web browser and navigate to the URL above")
            print("   Press Ctrl+C to stop the server")
            
            self.is_running = True
            
            # Run server (this blocks)
            self.server.run(host=host, port=port)
            
        except Exception as e:
            logger.error(f"Error in server demo: {e}")
            print(f"❌ Server error: {e}")
        
        finally:
            self.is_running = False
    
    async def run_terminal_demo(self):
        """Run demo with terminal interface."""
        print("\n💻 Starting terminal demo...")
        print("   This will show real-time updates in the terminal")
        
        try:
            # Create pipeline
            self.pipeline = create_default_pipeline()
            
            def terminal_callback(result):
                """Terminal display callback."""
                # Clear screen (works on most terminals)
                print("\033[2J\033[H", end="")
                
                print("🎤 Real-Time Speaker Isolation & Identification")
                print("=" * 60)
                print(f"Time: {time.strftime('%H:%M:%S')}")
                print(f"Speakers: {result.separated_audio.num_speakers}")
                print(f"Processing: {result.processing_time:.3f}s")
                print()
                
                # Show speakers
                for i, match in enumerate(result.speaker_matches):
                    status = "🔴" if match.is_unknown else "🟢"
                    print(f"{status} Speaker {i+1}: {match.name} "
                          f"({match.confidence:.2f})")
                
                print()
                
                # Show transcripts
                if result.transcription_results:
                    print("📝 Live Transcripts:")
                    for result in result.transcription_results:
                        if result.text.strip():
                            print(f"   {result.speaker_name}: {result.text}")
                
                print("\nPress Ctrl+C to stop...")
            
            self.pipeline.add_pipeline_callback(terminal_callback)
            
            if self.pipeline.start():
                self.is_running = True
                print("✅ Terminal demo started!")
                
                while self.is_running:
                    await asyncio.sleep(0.1)
            else:
                print("❌ Failed to start pipeline")
                
        except Exception as e:
            logger.error(f"Error in terminal demo: {e}")
            print(f"❌ Demo error: {e}")
        
        finally:
            self.stop()
    
    def stop(self):
        """Stop all running components."""
        if self.pipeline:
            self.pipeline.stop()
            self.pipeline = None
        
        if self.server:
            # Server shutdown would be handled by uvicorn
            self.server = None
        
        self.is_running = False
        print("\n🛑 Demo stopped")


async def main():
    """Main demo function."""
    parser = argparse.ArgumentParser(
        description="Real-Time Speaker Isolation & Identification Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_demo.py --mic                    # Use microphone input
  python run_demo.py --file audio.wav        # Process audio file
  python run_demo.py --server                # Start web server
  python run_demo.py --terminal              # Terminal interface
  python run_demo.py --info                  # Show system info only
        """
    )
    
    parser.add_argument("--mic", action="store_true",
                       help="Run demo with microphone input")
    parser.add_argument("--file", type=str, metavar="PATH",
                       help="Run demo with audio file")
    parser.add_argument("--server", action="store_true",
                       help="Run demo with web server")
    parser.add_argument("--terminal", action="store_true",
                       help="Run demo with terminal interface")
    parser.add_argument("--info", action="store_true",
                       help="Show system information and exit")
    parser.add_argument("--host", type=str, default="localhost",
                       help="Server host (default: localhost)")
    parser.add_argument("--port", type=int, default=8000,
                       help="Server port (default: 8000)")
    parser.add_argument("--log-level", type=str, default="INFO",
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Logging level (default: INFO)")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Print banner
    print_banner()
    
    # Show system info if requested or no other options
    if args.info or not any([args.mic, args.file, args.server, args.terminal]):
        print_system_info()
        print_model_status()
        
        if not any([args.mic, args.file, args.server, args.terminal]):
            print("\n💡 Use --help to see available demo modes")
        return
    
    # Create demo runner
    runner = DemoRunner()
    
    try:
        # Run selected demo mode
        if args.mic:
            await runner.run_microphone_demo()
        elif args.file:
            await runner.run_file_demo(args.file)
        elif args.server:
            await runner.run_server_demo(args.host, args.port)
        elif args.terminal:
            await runner.run_terminal_demo()
    
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Unexpected error: {e}")
    
    finally:
        runner.stop()


if __name__ == "__main__":
    asyncio.run(main())
