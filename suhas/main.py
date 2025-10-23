#!/usr/bin/env python3
"""
Raspberry Pi 5 AI Assistant - Main System Controller
Manages mode switching between Chat Mode and Object Detection Mode.
"""

import os
import sys
import logging
import signal
import time
from pathlib import Path
from typing import Optional

# Add modules directory to path
sys.path.insert(0, str(Path(__file__).parent / "modules"))

from modules.utils import ConfigManager, Logger, ProcessManager, SystemMonitor
from modules.chat_mode import ChatMode
from modules.object_detection import ObjectDetectionMode


class AIAssistant:
    """
    Main AI Assistant controller that manages different modes and system resources.
    """
    
    def __init__(self):
        """Initialize the AI Assistant."""
        self.config_manager = ConfigManager()
        self.process_manager = ProcessManager()
        self.system_monitor = SystemMonitor()
        
        # Initialize logging
        Logger.setup_logging(
            log_level=self.config_manager.get("system.log_level", "INFO"),
            log_file="data/assistant.log"
        )
        
        self.logger = logging.getLogger(__name__)
        
        # Mode instances
        self.chat_mode = None
        self.object_detection_mode = None
        self.current_mode = None
        
        # System state
        self.is_running = False
        self.shutdown_requested = False
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        self.logger.info("AI Assistant initialized")
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating shutdown...")
            self.shutdown_requested = True
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _print_banner(self) -> None:
        """Print startup banner."""
        print("\n" + "="*70)
        print("🤖 Raspberry Pi 5 AI Assistant")
        print("="*70)
        print("A modular AI assistant with Chat and Object Detection capabilities")
        print("Built for Raspberry Pi 5 with llama.cpp and YOLOv8")
        print("="*70)
    
    def _print_menu(self) -> None:
        """Print main menu options."""
        print("\n" + "-"*50)
        print("Select Mode:")
        print("  1 - Chat Mode (RAG + llama.cpp)")
        print("  2 - Object Detection Mode (YOLOv8)")
        print("  3 - System Status")
        print("  4 - Configuration")
        print("  5 - Exit")
        print("-"*50)
    
    def _check_system_requirements(self) -> bool:
        """Check if system meets requirements."""
        self.logger.info("Checking system requirements...")
        
        # Check Python version
        if sys.version_info < (3, 11):
            self.logger.error("Python 3.11+ required")
            return False
        
        # Check available memory
        memory_info = self.system_monitor.get_memory_usage()
        if memory_info['total'] < 2.0:  # Less than 2GB
            self.logger.warning("Low memory detected. Performance may be affected.")
        
        # Check disk space
        disk_usage = self.system_monitor.get_disk_usage()
        if disk_usage['percent'] > 90:
            self.logger.warning("Low disk space detected.")
        
        # Check model files
        llama_model = self.config_manager.get("llama_cpp.model_path")
        yolo_model = self.config_manager.get("yolo.model_path")
        
        if not Path(llama_model).exists():
            self.logger.warning(f"LLaMA model not found: {llama_model}")
            print(f"Warning: LLaMA model not found at {llama_model}")
            print("Chat mode will not work until a model is downloaded.")
        
        if not Path(yolo_model).exists():
            self.logger.info(f"YOLO model not found: {yolo_model}")
            print(f"Info: YOLO model not found at {yolo_model}")
            print("YOLOv8n will be downloaded automatically on first use.")
        
        self.logger.info("System requirements check completed")
        return True
    
    def _initialize_modes(self) -> bool:
        """Initialize mode instances."""
        try:
            self.logger.info("Initializing modes...")
            
            # Initialize chat mode
            self.chat_mode = ChatMode(self.config_manager)
            
            # Initialize object detection mode
            self.object_detection_mode = ObjectDetectionMode(self.config_manager)
            
            self.logger.info("Modes initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize modes: {e}")
            return False
    
    def _stop_current_mode(self) -> None:
        """Stop the currently active mode."""
        if self.current_mode == "chat" and self.chat_mode:
            self.logger.info("Stopping chat mode...")
            self.chat_mode.stop()
        elif self.current_mode == "object_detection" and self.object_detection_mode:
            self.logger.info("Stopping object detection mode...")
            self.object_detection_mode.stop()
        
        self.current_mode = None
    
    def _start_chat_mode(self) -> bool:
        """Start chat mode."""
        if self.current_mode == "chat":
            print("Chat mode is already running.")
            return True
        
        self._stop_current_mode()
        
        if not self.chat_mode:
            print("Chat mode not initialized.")
            return False
        
        print("Starting Chat Mode...")
        if self.chat_mode.start():
            self.current_mode = "chat"
            self.chat_mode.run_interactive()
            return True
        else:
            print("Failed to start chat mode.")
            return False
    
    def _start_object_detection_mode(self) -> bool:
        """Start object detection mode."""
        if self.current_mode == "object_detection":
            print("Object detection mode is already running.")
            return True
        
        self._stop_current_mode()
        
        if not self.object_detection_mode:
            print("Object detection mode not initialized.")
            return False
        
        print("Starting Object Detection Mode...")
        if self.object_detection_mode.start():
            self.current_mode = "object_detection"
            self.object_detection_mode.run_interactive()
            return True
        else:
            print("Failed to start object detection mode.")
            return False
    
    def _show_system_status(self) -> None:
        """Show system status information."""
        print("\n" + "="*50)
        print("📊 System Status")
        print("="*50)
        
        # System health
        health = self.system_monitor.check_system_health()
        print(f"CPU Usage: {health['cpu_usage']:.1f}%")
        print(f"Memory Usage: {health['memory']['percent']:.1f}% ({health['memory']['used']:.1f}GB / {health['memory']['total']:.1f}GB)")
        
        if health['temperature']:
            print(f"Temperature: {health['temperature']:.1f}°C")
        
        # Current mode
        if self.current_mode:
            print(f"Current Mode: {self.current_mode.title()}")
        else:
            print("Current Mode: None")
        
        # Model status
        llama_model = self.config_manager.get("llama_cpp.model_path")
        yolo_model = self.config_manager.get("yolo.model_path")
        
        print(f"\nModel Status:")
        print(f"LLaMA Model: {'✓' if Path(llama_model).exists() else '✗'} {llama_model}")
        print(f"YOLO Model: {'✓' if Path(yolo_model).exists() else '✗'} {yolo_model}")
        
        # Knowledge base status
        if self.chat_mode and self.chat_mode.rag_engine:
            kb_stats = self.chat_mode.rag_engine.get_collection_stats()
            print(f"\nKnowledge Base:")
            print(f"Documents: {kb_stats['total_documents']}")
            print(f"Sources: {kb_stats['unique_sources']}")
        
        print("="*50)
    
    def _show_configuration(self) -> None:
        """Show and manage configuration."""
        print("\n" + "="*50)
        print("⚙️ Configuration")
        print("="*50)
        
        while True:
            print("\nConfiguration Options:")
            print("  1 - View current configuration")
            print("  2 - Update LLaMA settings")
            print("  3 - Update YOLO settings")
            print("  4 - Update RAG settings")
            print("  5 - Update camera settings")
            print("  6 - Back to main menu")
            
            try:
                choice = input("\nSelect option (1-6): ").strip()
                
                if choice == "1":
                    self._view_configuration()
                elif choice == "2":
                    self._update_llama_config()
                elif choice == "3":
                    self._update_yolo_config()
                elif choice == "4":
                    self._update_rag_config()
                elif choice == "5":
                    self._update_camera_config()
                elif choice == "6":
                    break
                else:
                    print("Invalid option. Please try again.")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def _view_configuration(self) -> None:
        """View current configuration."""
        print("\nCurrent Configuration:")
        print("-" * 30)
        
        # LLaMA settings
        print("LLaMA Settings:")
        print(f"  Model Path: {self.config_manager.get('llama_cpp.model_path')}")
        print(f"  Context Size: {self.config_manager.get('llama_cpp.n_ctx')}")
        print(f"  Threads: {self.config_manager.get('llama_cpp.n_threads')}")
        print(f"  Temperature: {self.config_manager.get('llama_cpp.temperature')}")
        
        # YOLO settings
        print("\nYOLO Settings:")
        print(f"  Model Path: {self.config_manager.get('yolo.model_path')}")
        print(f"  Confidence: {self.config_manager.get('yolo.confidence_threshold')}")
        print(f"  IoU Threshold: {self.config_manager.get('yolo.iou_threshold')}")
        
        # RAG settings
        print("\nRAG Settings:")
        print(f"  Embedding Model: {self.config_manager.get('rag.embedding_model')}")
        print(f"  Chunk Size: {self.config_manager.get('rag.chunk_size')}")
        print(f"  Top K: {self.config_manager.get('rag.top_k')}")
        
        # Camera settings
        print("\nCamera Settings:")
        print(f"  Resolution: {self.config_manager.get('camera.resolution')}")
        print(f"  FPS: {self.config_manager.get('camera.fps')}")
        print(f"  Rotation: {self.config_manager.get('camera.rotation')}")
    
    def _update_llama_config(self) -> None:
        """Update LLaMA configuration."""
        print("\nUpdate LLaMA Configuration:")
        print("(Press Enter to keep current value)")
        
        current_path = self.config_manager.get('llama_cpp.model_path')
        new_path = input(f"Model Path [{current_path}]: ").strip()
        if new_path:
            self.config_manager.set('llama_cpp.model_path', new_path)
        
        current_ctx = self.config_manager.get('llama_cpp.n_ctx')
        new_ctx = input(f"Context Size [{current_ctx}]: ").strip()
        if new_ctx:
            try:
                self.config_manager.set('llama_cpp.n_ctx', int(new_ctx))
            except ValueError:
                print("Invalid context size, keeping current value")
        
        current_threads = self.config_manager.get('llama_cpp.n_threads')
        new_threads = input(f"Threads [{current_threads}]: ").strip()
        if new_threads:
            try:
                self.config_manager.set('llama_cpp.n_threads', int(new_threads))
            except ValueError:
                print("Invalid thread count, keeping current value")
        
        print("LLaMA configuration updated.")
    
    def _update_yolo_config(self) -> None:
        """Update YOLO configuration."""
        print("\nUpdate YOLO Configuration:")
        print("(Press Enter to keep current value)")
        
        current_path = self.config_manager.get('yolo.model_path')
        new_path = input(f"Model Path [{current_path}]: ").strip()
        if new_path:
            self.config_manager.set('yolo.model_path', new_path)
        
        current_conf = self.config_manager.get('yolo.confidence_threshold')
        new_conf = input(f"Confidence Threshold [{current_conf}]: ").strip()
        if new_conf:
            try:
                self.config_manager.set('yolo.confidence_threshold', float(new_conf))
            except ValueError:
                print("Invalid confidence threshold, keeping current value")
        
        print("YOLO configuration updated.")
    
    def _update_rag_config(self) -> None:
        """Update RAG configuration."""
        print("\nUpdate RAG Configuration:")
        print("(Press Enter to keep current value)")
        
        current_model = self.config_manager.get('rag.embedding_model')
        new_model = input(f"Embedding Model [{current_model}]: ").strip()
        if new_model:
            self.config_manager.set('rag.embedding_model', new_model)
        
        current_chunk = self.config_manager.get('rag.chunk_size')
        new_chunk = input(f"Chunk Size [{current_chunk}]: ").strip()
        if new_chunk:
            try:
                self.config_manager.set('rag.chunk_size', int(new_chunk))
            except ValueError:
                print("Invalid chunk size, keeping current value")
        
        current_topk = self.config_manager.get('rag.top_k')
        new_topk = input(f"Top K [{current_topk}]: ").strip()
        if new_topk:
            try:
                self.config_manager.set('rag.top_k', int(new_topk))
            except ValueError:
                print("Invalid top K value, keeping current value")
        
        print("RAG configuration updated.")
    
    def _update_camera_config(self) -> None:
        """Update camera configuration."""
        print("\nUpdate Camera Configuration:")
        print("(Press Enter to keep current value)")
        
        current_res = self.config_manager.get('camera.resolution')
        new_res = input(f"Resolution (width,height) [{current_res}]: ").strip()
        if new_res:
            try:
                res = [int(x.strip()) for x in new_res.split(',')]
                if len(res) == 2:
                    self.config_manager.set('camera.resolution', res)
                else:
                    print("Invalid resolution format, keeping current value")
            except ValueError:
                print("Invalid resolution format, keeping current value")
        
        current_fps = self.config_manager.get('camera.fps')
        new_fps = input(f"FPS [{current_fps}]: ").strip()
        if new_fps:
            try:
                self.config_manager.set('camera.fps', int(new_fps))
            except ValueError:
                print("Invalid FPS value, keeping current value")
        
        print("Camera configuration updated.")
    
    def _ingest_knowledge_base(self) -> None:
        """Ingest documents into knowledge base."""
        if not self.chat_mode or not self.chat_mode.rag_engine:
            print("Chat mode not initialized. Cannot ingest knowledge base.")
            return
        
        print("\nIngesting knowledge base...")
        kb_path = input("Enter knowledge base directory path [knowledge_base]: ").strip()
        if not kb_path:
            kb_path = "knowledge_base"
        
        if not Path(kb_path).exists():
            print(f"Directory not found: {kb_path}")
            return
        
        count = self.chat_mode.ingest_knowledge_base(kb_path)
        print(f"Ingested {count} documents from {kb_path}")
    
    def run(self) -> None:
        """Run the main AI Assistant loop."""
        self._print_banner()
        
        # Check system requirements
        if not self._check_system_requirements():
            print("System requirements not met. Please check the logs.")
            return
        
        # Initialize modes
        if not self._initialize_modes():
            print("Failed to initialize modes. Please check the logs.")
            return
        
        self.is_running = True
        self.logger.info("AI Assistant started")
        
        try:
            while self.is_running and not self.shutdown_requested:
                self._print_menu()
                
                try:
                    choice = input("Select option (1-5): ").strip()
                    
                    if choice == "1":
                        self._start_chat_mode()
                    elif choice == "2":
                        self._start_object_detection_mode()
                    elif choice == "3":
                        self._show_system_status()
                    elif choice == "4":
                        self._show_configuration()
                    elif choice == "5":
                        break
                    else:
                        print("Invalid option. Please try again.")
                
                except KeyboardInterrupt:
                    print("\n\nShutdown requested by user")
                    break
                except Exception as e:
                    self.logger.error(f"Error in main loop: {e}")
                    print(f"Error: {e}")
        
        finally:
            self.shutdown()
    
    def shutdown(self) -> None:
        """Shutdown the AI Assistant and cleanup resources."""
        self.logger.info("Shutting down AI Assistant...")
        
        # Stop current mode
        self._stop_current_mode()
        
        # Terminate all processes
        self.process_manager.terminate_all()
        
        self.is_running = False
        self.logger.info("AI Assistant shutdown complete")
        print("\nGoodbye! 👋")


def main():
    """Main entry point."""
    try:
        assistant = AIAssistant()
        assistant.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        logging.getLogger(__name__).error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
