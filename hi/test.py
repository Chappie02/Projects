#!/usr/bin/env python3
"""
Test script for AI Assistant components
"""

import sys
import time
from colorama import init, Fore, Style

# Initialize colorama
init()

def test_imports():
    """Test if all modules can be imported"""
    print(f"{Fore.CYAN}🔍 Testing module imports...{Style.RESET_ALL}")
    
    modules = [
        ("config", "config"),
        ("llm_module", "llm_module"),
        ("voice_module", "voice_module"),
        ("object_detection_module", "object_detection_module"),
        ("home_automation_module", "home_automation_module"),
    ]
    
    all_imports_ok = True
    
    for module_name, import_name in modules:
        try:
            __import__(import_name)
            print(f"✅ {module_name}")
        except ImportError as e:
            print(f"❌ {module_name}: {e}")
            all_imports_ok = False
    
    return all_imports_ok

def test_config():
    """Test configuration loading"""
    print(f"\n{Fore.CYAN}⚙️  Testing configuration...{Style.RESET_ALL}")
    
    try:
        from config import Config
        print(f"✅ Configuration loaded successfully")
        print(f"   LLM Model Path: {Config.LLM_MODEL_PATH}")
        print(f"   Camera Index: {Config.CAMERA_INDEX}")
        print(f"   Voice Language: {Config.VOICE_LANGUAGE}")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_llm_module():
    """Test LLM module"""
    print(f"\n{Fore.CYAN}🧠 Testing LLM module...{Style.RESET_ALL}")
    
    try:
        from llm_module import LLMModule
        
        llm = LLMModule()
        print(f"✅ LLM module initialized")
        print(f"   Available: {llm.is_available()}")
        
        if llm.is_available():
            response = llm.generate_response("Hello, how are you?")
            print(f"   Test response: {response[:50]}...")
        else:
            print(f"   Using fallback responses")
        
        return True
    except Exception as e:
        print(f"❌ LLM module error: {e}")
        return False

def test_voice_module():
    """Test voice module"""
    print(f"\n{Fore.CYAN}🎤 Testing voice module...{Style.RESET_ALL}")
    
    try:
        from voice_module import VoiceModule
        
        voice = VoiceModule()
        print(f"✅ Voice module initialized")
        print(f"   Available: {voice.is_voice_available()}")
        
        if voice.is_voice_available():
            print(f"   Speech recognition: Available")
            print(f"   Text-to-speech: Available")
        else:
            print(f"   Voice features not available")
        
        return True
    except Exception as e:
        print(f"❌ Voice module error: {e}")
        return False

def test_object_detection():
    """Test object detection module"""
    print(f"\n{Fore.CYAN}👁️  Testing object detection module...{Style.RESET_ALL}")
    
    try:
        from object_detection_module import ObjectDetectionModule
        
        detection = ObjectDetectionModule()
        print(f"✅ Object detection module initialized")
        print(f"   Available: {detection.is_available()}")
        
        if detection.is_available():
            print(f"   Camera: Available")
            print(f"   YOLO model: {'Available' if detection.model else 'Not available'}")
        else:
            print(f"   Camera not available")
        
        return True
    except Exception as e:
        print(f"❌ Object detection error: {e}")
        return False

def test_home_automation():
    """Test home automation module"""
    print(f"\n{Fore.CYAN}🏠 Testing home automation module...{Style.RESET_ALL}")
    
    try:
        from home_automation_module import HomeAutomationModule
        
        home = HomeAutomationModule()
        print(f"✅ Home automation module initialized")
        print(f"   Available: {home.is_available()}")
        
        if home.is_available():
            devices = home.get_devices()
            print(f"   Connected devices: {len(devices)}")
            for device in devices:
                print(f"     - {device.name} ({device.type}): {device.state}")
        else:
            print(f"   No home automation systems connected")
        
        return True
    except Exception as e:
        print(f"❌ Home automation error: {e}")
        return False

def test_main_assistant():
    """Test main assistant initialization"""
    print(f"\n{Fore.CYAN}🤖 Testing main assistant...{Style.RESET_ALL}")
    
    try:
        from ai_assistant import AIAssistant
        
        print("Initializing AI Assistant...")
        assistant = AIAssistant()
        print(f"✅ AI Assistant initialized successfully")
        print(f"   Current mode: {assistant.current_mode.value}")
        
        # Test mode switching
        print("Testing mode switching...")
        assistant.switch_mode(assistant.current_mode)  # Should do nothing
        print(f"   Mode switching: OK")
        
        return True
    except Exception as e:
        print(f"❌ Main assistant error: {e}")
        return False

def main():
    """Main test function"""
    print(f"{Fore.CYAN}🧪 AI Assistant Test Suite{Style.RESET_ALL}")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Configuration", test_config),
        ("LLM Module", test_llm_module),
        ("Voice Module", test_voice_module),
        ("Object Detection", test_object_detection),
        ("Home Automation", test_home_automation),
        ("Main Assistant", test_main_assistant),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{Fore.CYAN}📊 Test Results Summary{Style.RESET_ALL}")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n{Fore.GREEN}Passed: {passed}/{total}{Style.RESET_ALL}")
    
    if passed == total:
        print(f"{Fore.GREEN}🎉 All tests passed! Your AI Assistant is ready to use.{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}⚠️  Some tests failed. Please check the errors above.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}You may still be able to use the assistant with limited functionality.{Style.RESET_ALL}")

if __name__ == "__main__":
    main() 