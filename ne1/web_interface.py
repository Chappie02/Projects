from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import logging
import threading
import time
import cv2
import base64
from config import Config
from main_system import MainSystem

app = Flask(__name__)
app.config['SECRET_KEY'] = 'raspberry_pi_5_llm_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

class WebInterface:
    def __init__(self, main_system):
        self.main_system = main_system
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.is_streaming = False
        
        # Setup routes
        self._setup_routes()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @app.route('/')
        def index():
            return render_template('index.html')
        
        @app.route('/api/status')
        def get_status():
            """Get current system status"""
            try:
                status = {
                    'mode': self.main_system.llm.get_current_mode(),
                    'is_running': self.main_system.is_running,
                    'devices': self.main_system.home_automation.get_device_status(),
                    'objects': self.main_system.object_detection.get_current_objects(),
                    'motion_detected': self.main_system.home_automation.get_motion_status(),
                    'audio_level': self.main_system.audio_manager.get_audio_levels()
                }
                return jsonify(status)
            except Exception as e:
                self.logger.error(f"Error getting status: {e}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/control', methods=['POST'])
        def control_device():
            """Control home automation devices"""
            try:
                data = request.get_json()
                device = data.get('device')
                action = data.get('action')
                
                if device and action:
                    result = self.main_system.home_automation.control_device(device, action)
                    return jsonify({'success': True, 'result': result})
                else:
                    return jsonify({'error': 'Missing device or action'}), 400
            except Exception as e:
                self.logger.error(f"Error controlling device: {e}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/voice', methods=['POST'])
        def send_voice_command():
            """Send voice command via web interface"""
            try:
                data = request.get_json()
                command = data.get('command')
                
                if command:
                    # Process command in a separate thread
                    threading.Thread(
                        target=self.main_system.process_voice_command,
                        args=(command,)
                    ).start()
                    return jsonify({'success': True})
                else:
                    return jsonify({'error': 'Missing command'}), 400
            except Exception as e:
                self.logger.error(f"Error processing voice command: {e}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/mode', methods=['POST'])
        def switch_mode():
            """Switch system mode"""
            try:
                data = request.get_json()
                mode = data.get('mode')
                
                if mode:
                    # Force mode switch
                    self.main_system.llm.current_mode = mode
                    return jsonify({'success': True, 'mode': mode})
                else:
                    return jsonify({'error': 'Missing mode'}), 400
            except Exception as e:
                self.logger.error(f"Error switching mode: {e}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/conversation')
        def get_conversation():
            """Get conversation history"""
            try:
                history = self.main_system.llm.get_conversation_history()
                return jsonify({'conversation': history})
            except Exception as e:
                self.logger.error(f"Error getting conversation: {e}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/camera/start')
        def start_camera_stream():
            """Start camera stream"""
            try:
                self.is_streaming = True
                return jsonify({'success': True})
            except Exception as e:
                self.logger.error(f"Error starting camera stream: {e}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/camera/stop')
        def stop_camera_stream():
            """Stop camera stream"""
            try:
                self.is_streaming = False
                return jsonify({'success': True})
            except Exception as e:
                self.logger.error(f"Error stopping camera stream: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _start_background_tasks(self):
        """Start background tasks for real-time updates"""
        
        def status_broadcast():
            """Broadcast system status updates"""
            while True:
                try:
                    if self.main_system.is_running:
                        status = {
                            'mode': self.main_system.llm.get_current_mode(),
                            'devices': self.main_system.home_automation.get_device_status(),
                            'objects': self.main_system.object_detection.get_current_objects(),
                            'motion_detected': self.main_system.home_automation.get_motion_status(),
                            'audio_level': self.main_system.audio_manager.get_audio_levels()
                        }
                        socketio.emit('status_update', status)
                    time.sleep(2)
                except Exception as e:
                    self.logger.error(f"Error in status broadcast: {e}")
                    time.sleep(5)
        
        def camera_stream():
            """Stream camera feed"""
            while True:
                try:
                    if self.is_streaming and self.main_system.object_detection.is_initialized():
                        frame = self.main_system.object_detection.get_camera_frame()
                        if frame is not None:
                            # Convert frame to base64
                            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                            frame_base64 = base64.b64encode(buffer).decode('utf-8')
                            socketio.emit('camera_frame', {'frame': frame_base64})
                    time.sleep(0.1)  # 10 FPS
                except Exception as e:
                    self.logger.error(f"Error in camera stream: {e}")
                    time.sleep(1)
        
        # Start background threads
        status_thread = threading.Thread(target=status_broadcast, daemon=True)
        status_thread.start()
        
        camera_thread = threading.Thread(target=camera_stream, daemon=True)
        camera_thread.start()
    
    def run(self):
        """Run the web interface"""
        try:
            self.logger.info(f"Starting web interface on {self.config.WEB_HOST}:{self.config.WEB_PORT}")
            socketio.run(app, host=self.config.WEB_HOST, port=self.config.WEB_PORT, debug=False)
        except Exception as e:
            self.logger.error(f"Error running web interface: {e}")

# Socket.IO events
@socketio.on('connect')
def handle_connect():
    logging.info('Client connected to web interface')

@socketio.on('disconnect')
def handle_disconnect():
    logging.info('Client disconnected from web interface')

@socketio.on('voice_command')
def handle_voice_command(data):
    """Handle voice command from web interface"""
    try:
        command = data.get('command')
        if command:
            # This would be handled by the main system
            logging.info(f"Received voice command via web: {command}")
    except Exception as e:
        logging.error(f"Error handling voice command: {e}")

if __name__ == '__main__':
    # Create main system instance
    main_system = MainSystem()
    
    # Create and run web interface
    web_interface = WebInterface(main_system)
    web_interface.run() 