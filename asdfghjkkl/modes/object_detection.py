import cv2
from ultralytics import YOLO
import os

def detect_objects(config):
    model_path = config['object_detection']['model_path']
    camera_index = config['object_detection'].get('camera_index', 0)
    # Capture image from camera
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        return ["[Camera not accessible]"]
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return ["[Failed to capture image]"]
    # Run YOLOv8n detection
    try:
        model = YOLO(model_path)
        results = model(frame)
        labels = set()
        for r in results:
            for c in r.boxes.cls:
                labels.add(model.names[int(c)])
        return list(labels) if labels else ["[No objects detected]"]
    except Exception as e:
        return [f"[YOLO error: {e}]"]

# Placeholder for future voice input expansion
# def handle_voice_input(...):
#     pass 