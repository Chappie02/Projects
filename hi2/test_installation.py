#!/usr/bin/env python3
"""
Test script for RPi5 Multi-Modal AI Assistant
This script tests all components to ensure they're working correctly
"""

import sys
import importlib
import subprocess
import requests
import cv2
import speech_recognition as sr
import pyttsx3

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing module imports...")
    
    modules = [
        'speech_recognition',
        'pyttsx3', 
        'sounddevice',
        'cv2',
        'ultralytics',
        'requests',
        'numpy',
        'configparser'
    ]
    
    failed_imports = []
    for module in modules:
        try:
            importlib.import_module(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\nFailed to import: {', '.join(failed_imports)}")
        return False
    else:
        print("All modules imported successfully!")
        return True

def test_ollama():
    """Test Ollama connection"""
    print("\nTesting Ollama connection...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✓ Ollama is running and accessible")
            return True
        else:
            print(f"✗ Ollama returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Could not connect to Ollama: {e}")
        return False

def test_camera():
    """Test camera access"""
    print("\nTesting camera...")
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"✓ Camera working (frame size: {frame.shape})")
                cap.release()
                return True
            else:
                print("✗ Could not capture frame from camera")
                cap.release()
                return False
        else:
            print("✗ Could not open camera")
            return False
    except Exception as e:
        print(f"✗ Camera test failed: {e}")
        return False

def test_speech_recognition():
    """Test speech recognition"""
    print("\nTesting speech recognition...")
    try:
        recognizer = sr.Recognizer()
        print("✓ Speech recognition initialized")
        return True
    except Exception as e:
        print(f"✗ Speech recognition test failed: {e}")
        return False

def test_text_to_speech():
    """Test text-to-speech"""
    print("\nTesting text-to-speech...")
    try:
        engine = pyttsx3.init()
        print("✓ Text-to-speech initialized")
        return True
    except Exception as e:
        print(f"✗ Text-to-speech test failed: {e}")
        return False

def test_yolo():
    """Test YOLO model loading"""
    print("\nTesting YOLO model...")
    try:
        from ultralytics import YOLO
        model = YOLO('yolov8n.pt')
        print("✓ YOLO model loaded successfully")
        return True
    except Exception as e:
        print(f"✗ YOLO test failed: {e}")
        return False

def test_audio_devices():
    """Test audio devices"""
    print("\nTesting audio devices...")
    
    # Test microphone
    try:
        with sr.Microphone() as source:
            print("✓ Microphone detected")
    except Exception as e:
        print(f"✗ Microphone test failed: {e}")
        return False
    
    # Test speaker
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        print(f"✓ Speaker detected ({len(voices)} voices available)")
        return True
    except Exception as e:
        print(f"✗ Speaker test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("RPi5 Multi-Modal AI Assistant - Installation Test")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Ollama Connection", test_ollama),
        ("Camera", test_camera),
        ("Speech Recognition", test_speech_recognition),
        ("Text-to-Speech", test_text_to_speech),
        ("YOLO Model", test_yolo),
        ("Audio Devices", test_audio_devices)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Your AI Assistant is ready to use.")
        print("\nTo start the assistant:")
        print("1. Activate virtual environment: source ai_assistant_env/bin/activate")
        print("2. Run: python main.py")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        print("\nCommon solutions:")
        print("- Make sure all dependencies are installed: pip install -r requirements.txt")
        print("- Check if Ollama is running: sudo systemctl status ollama")
        print("- Verify camera and audio devices are connected")
        print("- See README.md for detailed troubleshooting")

if __name__ == "__main__":
    main() 