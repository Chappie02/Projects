#!/usr/bin/env python3
"""
Test script for Raspberry Pi 5 AI Assistant
Verifies all components are working correctly
"""

import sys
import time
import subprocess
import importlib
from typing import Dict, List, Tuple

def test_python_version() -> bool:
    """Test Python version compatibility"""
    print("🐍 Testing Python version...")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False

def test_imports() -> Dict[str, bool]:
    """Test if all required packages can be imported"""
    print("\n📦 Testing package imports...")
    
    required_packages = [
        "cv2",
        "numpy", 
        "requests",
        "ultralytics",
        "PIL",
        "aiohttp",
        "asyncio"
    ]
    
    results = {}
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} - Imported successfully")
            results[package] = True
        except ImportError as e:
            print(f"❌ {package} - Import failed: {e}")
            results[package] = False
    
    return results

def test_ollama_connection() -> bool:
    """Test Ollama connection"""
    print("\n🤖 Testing Ollama connection...")
    
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            if models:
                print(f"✅ Ollama connected - {len(models)} model(s) available")
                for model in models[:3]:  # Show first 3 models
                    print(f"   - {model.get('name', 'Unknown')}")
                return True
            else:
                print("⚠️  Ollama connected but no models found")
                return False
        else:
            print(f"❌ Ollama connection failed: HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Ollama not running or not accessible")
        print("   Run: sudo systemctl start ollama")
        return False
    except Exception as e:
        print(f"❌ Ollama test failed: {e}")
        return False

def test_camera_access() -> bool:
    """Test camera access"""
    print("\n📷 Testing camera access...")
    
    try:
        # Prefer Picamera2 when available
        try:
            from picamera2 import Picamera2  # type: ignore
            picam = Picamera2()
            picam.configure(picam.create_still_configuration())
            picam.start()
            array = picam.capture_array()
            h, w = array.shape[:2]
            print(f"✅ Picamera2 accessible - {w}x{h}")
            picam.stop()
            return True
        except Exception:
            pass

        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            # Get camera info
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            
            print(f"✅ Camera accessible - {width}x{height} @ {fps}fps")
            
            # Try to capture a frame
            ret, frame = cap.read()
            if ret:
                print("✅ Frame capture successful")
                cap.release()
                return True
            else:
                print("❌ Frame capture failed")
                cap.release()
                return False
        else:
            print("❌ Camera not accessible")
            return False
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False

def test_yolo_model() -> bool:
    """Test YOLO model loading"""
    print("\n🎯 Testing YOLO model...")
    
    try:
        from ultralytics import YOLO
        
        print("   Loading YOLOv8n model...")
        model = YOLO("yolov8n.pt")
        
        # Test with a dummy image
        import numpy as np
        dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        print("   Running inference test...")
        results = model(dummy_image, conf=0.5)
        
        print("✅ YOLO model loaded and inference successful")
        return True
        
    except Exception as e:
        print(f"❌ YOLO test failed: {e}")
        return False

def test_system_resources() -> Dict[str, any]:
    """Test system resources"""
    print("\n💻 Testing system resources...")
    
    try:
        import psutil
        
        # CPU info
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory info
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        memory_available_gb = memory.available / (1024**3)
        
        # Disk info
        disk = psutil.disk_usage('/')
        disk_gb = disk.total / (1024**3)
        disk_free_gb = disk.free / (1024**3)
        
        print(f"✅ CPU: {cpu_count} cores, {cpu_percent:.1f}% usage")
        print(f"✅ Memory: {memory_gb:.1f}GB total, {memory_available_gb:.1f}GB available")
        print(f"✅ Disk: {disk_gb:.1f}GB total, {disk_free_gb:.1f}GB free")
        
        # Check if resources are sufficient
        warnings = []
        if memory_gb < 4:
            warnings.append("Low memory - 4GB+ recommended")
        if disk_free_gb < 5:
            warnings.append("Low disk space - 5GB+ recommended")
        if cpu_count < 4:
            warnings.append("Low CPU cores - 4+ recommended")
        
        if warnings:
            print("⚠️  Resource warnings:")
            for warning in warnings:
                print(f"   - {warning}")
        
        return {
            "cpu_count": cpu_count,
            "cpu_percent": cpu_percent,
            "memory_gb": memory_gb,
            "memory_available_gb": memory_available_gb,
            "disk_gb": disk_gb,
            "disk_free_gb": disk_free_gb,
            "warnings": warnings
        }
        
    except ImportError:
        print("⚠️  psutil not available - skipping resource check")
        return {}
    except Exception as e:
        print(f"❌ Resource check failed: {e}")
        return {}

def test_our_modules() -> Dict[str, bool]:
    """Test our custom modules"""
    print("\n🔧 Testing custom modules...")
    
    modules = [
        "utils",
        "llm_interface", 
        "camera_handler",
        "object_detection",
        "config"
    ]
    
    results = {}
    
    for module in modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module} - Imported successfully")
            results[module] = True
        except ImportError as e:
            print(f"❌ {module} - Import failed: {e}")
            results[module] = False
    
    return results

def run_comprehensive_test() -> Dict[str, any]:
    """Run comprehensive system test"""
    print("🚀 Starting Raspberry Pi 5 AI Assistant Installation Test")
    print("=" * 60)
    
    results = {
        "python_version": test_python_version(),
        "imports": test_imports(),
        "ollama": test_ollama_connection(),
        "camera": test_camera_access(),
        "yolo": test_yolo_model(),
        "resources": test_system_resources(),
        "modules": test_our_modules()
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    
    # Check Python version
    if results["python_version"]:
        print("✅ Python version: Compatible")
    else:
        print("❌ Python version: Incompatible")
        all_passed = False
    
    # Check imports
    import_failures = [pkg for pkg, success in results["imports"].items() if not success]
    if not import_failures:
        print("✅ Package imports: All successful")
    else:
        print(f"❌ Package imports: {len(import_failures)} failed")
        all_passed = False
    
    # Check Ollama
    if results["ollama"]:
        print("✅ Ollama connection: Successful")
    else:
        print("❌ Ollama connection: Failed")
        all_passed = False
    
    # Check camera
    if results["camera"]:
        print("✅ Camera access: Successful")
    else:
        print("⚠️  Camera access: Failed (may work with mock mode)")
    
    # Check YOLO
    if results["yolo"]:
        print("✅ YOLO model: Loaded successfully")
    else:
        print("❌ YOLO model: Failed to load")
        all_passed = False
    
    # Check modules
    module_failures = [mod for mod, success in results["modules"].items() if not success]
    if not module_failures:
        print("✅ Custom modules: All imported")
    else:
        print(f"❌ Custom modules: {len(module_failures)} failed")
        all_passed = False
    
    # Final result
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Your AI Assistant is ready to use.")
        print("   Run: python main.py")
    else:
        print("⚠️  SOME TESTS FAILED. Please check the issues above.")
        print("   You may still be able to run with limited functionality.")
    
    print("=" * 60)
    
    return results

def print_installation_guide():
    """Print installation guide if tests fail"""
    print("\n📖 INSTALLATION GUIDE")
    print("=" * 60)
    print("If tests failed, follow these steps:")
    print()
    print("1. Install Ollama:")
    print("   curl -fsSL https://ollama.ai/install.sh | sh")
    print("   sudo systemctl enable ollama")
    print("   sudo systemctl start ollama")
    print()
    print("2. Download a model:")
    print("   ollama pull gemma2:2b")
    print()
    print("3. Install Python packages:")
    print("   pip install -r requirements.txt")
    print()
    print("4. Enable camera (if using real camera):")
    print("   sudo raspi-config")
    print("   Navigate to: Interface Options > Camera > Enable")
    print()
    print("5. Test camera:")
    print("   vcgencmd get_camera")
    print("   raspistill -o test.jpg")
    print()
    print("6. Run the assistant:")
    print("   python main.py")
    print("   # Or with mock camera:")
    print("   python main.py --mock")

if __name__ == "__main__":
    try:
        results = run_comprehensive_test()
        
        # If any critical tests failed, show installation guide
        critical_failures = (
            not results["python_version"] or
            not results["ollama"] or
            not results["yolo"] or
            any(not success for success in results["modules"].values())
        )
        
        if critical_failures:
            print_installation_guide()
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test script failed: {e}")
        print_installation_guide()
