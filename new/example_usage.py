#!/usr/bin/env python3
"""
Example usage of Raspberry Pi 5 AI Assistant components
Demonstrates how to use the modules programmatically
"""

import asyncio
import time
from typing import List, Dict

# Import our modules
from llm_interface import SyncLLMInterface
from camera_handler import create_camera_handler
from object_detection import create_object_detector, create_detection_processor
from utils import print_status, handle_error

def example_chat_mode():
    """Example of using chat mode"""
    print("=== Chat Mode Example ===")
    
    # Initialize LLM interface
    llm = SyncLLMInterface()
    
    if not llm.check_ollama_status():
        print("❌ Ollama not running. Please start Ollama first.")
        return
    
    # Example conversation
    messages = [
        "Hello! What can you help me with?",
        "Tell me a joke",
        "What's the weather like?",
        "How do I make coffee?"
    ]
    
    for message in messages:
        print(f"\nYou: {message}")
        print_status("Generating response...", "info")
        
        try:
            response = llm.chat_response(message)
            print(f"Assistant: {response}")
        except Exception as e:
            handle_error(e, "chat_example")
            print("Failed to generate response")

def example_object_detection():
    """Example of using object detection mode"""
    print("\n=== Object Detection Example ===")
    
    # Initialize components
    camera = create_camera_handler(use_mock=True)  # Use mock camera for demo
    detector = create_object_detector(model_size="n")
    processor = create_detection_processor(detector)
    
    # Initialize models
    if not detector.initialize_model():
        print("❌ Failed to initialize object detection model")
        return
    
    if not camera.test_camera():
        print("❌ Camera test failed")
        return
    
    print("✅ Components initialized successfully")
    
    # Start camera capture
    if not camera.start_capture():
        print("❌ Failed to start camera capture")
        return
    
    try:
        print("📷 Capturing frames for 10 seconds...")
        start_time = time.time()
        
        while time.time() - start_time < 10:
            # Get frame
            frame = camera.get_frame()
            if frame is None:
                continue
            
            # Process frame
            detections, annotated_frame = processor.process_frame(frame)
            
            # Add to history
            processor.add_to_history(detections)
            
            # Show results
            if detections:
                unique_objects = detector.get_unique_objects(detections)
                print(f"Detected: {', '.join(unique_objects)}")
            
            time.sleep(1)  # Process every second
        
        # Show statistics
        stats = processor.get_detection_stats()
        print(f"\n📊 Detection Statistics:")
        print(f"Total detections: {stats['total_detections']}")
        print(f"Unique objects: {', '.join(stats['unique_objects'])}")
        print(f"Average objects per frame: {stats['avg_objects_per_frame']:.1f}")
        
    finally:
        camera.stop_capture()

def example_object_analysis():
    """Example of analyzing detected objects with LLM"""
    print("\n=== Object Analysis Example ===")
    
    # Initialize LLM interface
    llm = SyncLLMInterface()
    
    if not llm.check_ollama_status():
        print("❌ Ollama not running. Please start Ollama first.")
        return
    
    # Example objects to analyze
    objects_to_analyze = [
        "coffee mug",
        "laptop",
        "cat",
        "car",
        "book"
    ]
    
    for obj_name in objects_to_analyze:
        print(f"\n🤖 Analyzing: {obj_name}")
        print_status("Generating analysis...", "info")
        
        try:
            analysis = llm.analyze_object(obj_name)
            print(f"Analysis: {analysis}")
        except Exception as e:
            handle_error(e, "object_analysis_example")
            print(f"Failed to analyze {obj_name}")
        
        time.sleep(1)  # Brief pause between analyses

def example_camera_operations():
    """Example of camera operations"""
    print("\n=== Camera Operations Example ===")
    
    # Create camera handler
    camera = create_camera_handler(use_mock=True)
    
    # Test camera
    if camera.test_camera():
        print("✅ Camera test successful")
        
        # Get camera info
        info = camera.get_camera_info()
        print(f"Camera info: {info}")
        
        # Start capture
        if camera.start_capture():
            print("✅ Camera capture started")
            
            # Capture a few frames
            for i in range(5):
                frame = camera.get_frame()
                if frame is not None:
                    height, width = frame.shape[:2]
                    print(f"Frame {i+1}: {width}x{height}")
                time.sleep(0.5)
            
            camera.stop_capture()
            print("✅ Camera capture stopped")
        else:
            print("❌ Failed to start camera capture")
    else:
        print("❌ Camera test failed")

def example_llm_operations():
    """Example of LLM operations"""
    print("\n=== LLM Operations Example ===")
    
    # Initialize LLM interface
    llm = SyncLLMInterface()
    
    if not llm.check_ollama_status():
        print("❌ Ollama not running. Please start Ollama first.")
        return
    
    # Get available models
    models = llm.get_available_models()
    print(f"Available models: {', '.join(models)}")
    
    # Get model info
    if models:
        model_info = llm.get_model_info()
        print(f"Current model info: {model_info}")
    
    # Test different prompts
    test_prompts = [
        "What is the capital of France?",
        "Write a haiku about programming",
        "Explain quantum computing in simple terms"
    ]
    
    for prompt in test_prompts:
        print(f"\nPrompt: {prompt}")
        try:
            response = llm.generate_response(prompt)
            print(f"Response: {response[:100]}...")  # Show first 100 chars
        except Exception as e:
            handle_error(e, "llm_operations_example")

def run_all_examples():
    """Run all examples"""
    print("🚀 Raspberry Pi 5 AI Assistant - Example Usage")
    print("=" * 60)
    
    try:
        # Run examples
        example_llm_operations()
        example_camera_operations()
        example_chat_mode()
        example_object_detection()
        example_object_analysis()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Examples interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Examples failed: {e}")
        handle_error(e, "run_all_examples")

def interactive_demo():
    """Interactive demo mode"""
    print("🎮 Interactive Demo Mode")
    print("=" * 40)
    
    # Initialize components
    llm = SyncLLMInterface()
    camera = create_camera_handler(use_mock=True)
    detector = create_object_detector(model_size="n")
    
    if not llm.check_ollama_status():
        print("❌ Ollama not running. Cannot start demo.")
        return
    
    if not detector.initialize_model():
        print("❌ Object detection model failed to load.")
        return
    
    print("✅ Components ready for demo")
    print("\nCommands:")
    print("  chat <message> - Send a chat message")
    print("  detect - Run object detection on camera")
    print("  analyze <object> - Analyze a specific object")
    print("  quit - Exit demo")
    
    while True:
        try:
            command = input("\nDemo> ").strip()
            
            if command.lower() == 'quit':
                break
            elif command.lower().startswith('chat '):
                message = command[5:]  # Remove 'chat ' prefix
                print(f"🤖 Generating response for: {message}")
                response = llm.chat_response(message)
                print(f"Assistant: {response}")
            elif command.lower() == 'detect':
                print("📷 Running object detection...")
                if camera.start_capture():
                    frame = camera.get_frame()
                    if frame is not None:
                        detections = detector.detect_objects(frame)
                        if detections:
                            objects = detector.get_unique_objects(detections)
                            print(f"Detected: {', '.join(objects)}")
                        else:
                            print("No objects detected")
                    camera.stop_capture()
                else:
                    print("❌ Failed to start camera")
            elif command.lower().startswith('analyze '):
                obj_name = command[8:]  # Remove 'analyze ' prefix
                print(f"🤖 Analyzing: {obj_name}")
                analysis = llm.analyze_object(obj_name)
                print(f"Analysis: {analysis}")
            else:
                print("❌ Unknown command. Use: chat, detect, analyze, or quit")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            handle_error(e, "interactive_demo")
            print("❌ Error occurred, please try again")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_demo()
    else:
        run_all_examples()
