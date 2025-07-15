import cv2
from picamera2 import Picamera2
from ultralytics import YOLO
from sentence_transformers import SentenceTransformer, util
import numpy as np

class ObjectDetectionMode:
    def __init__(self):
        # Load pre-trained YOLOv8 Nano model
        self.model = YOLO('yolov8n.pt')
        self.COCO_INSTANCE_CATEGORY_NAMES = [
            '__background__', 'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus',
            'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'N/A', 'stop sign',
            'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
            'elephant', 'bear', 'zebra', 'giraffe', 'N/A', 'backpack', 'umbrella', 'N/A',
            'N/A', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
            'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
            'bottle', 'N/A', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana',
            'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut',
            'cake', 'chair', 'couch', 'potted plant', 'bed', 'N/A', 'dining table', 'N/A',
            'N/A', 'toilet', 'N/A', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
            'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'N/A', 'book', 'clock',
            'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
        ]
        self.intent_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.switch_phrases = [
            'switch to chat mode',
            'go back to chat',
            'chat mode',
            'return to chat',
            'enable chat mode',
        ]

    def detect_objects(self, camera_index=0):
        # Initialize Raspberry Pi camera
        picam2 = Picamera2()
        picam2.configure(picam2.create_preview_configuration(main={"size": (640, 480)}))
        picam2.start()
        print("[ObjectDetectionMode] Press 'q' to stop object detection.")
        
        try:
            while True:
                # Capture frame from Pi camera
                frame = picam2.capture_array()
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # Convert to BGR for OpenCV
                
                # Run YOLOv8 inference
                results = self.model(frame, verbose=False)
                detected = set()
                
                # Process detection results
                for result in results:
                    for box in result.boxes:
                        confidence = box.conf.item()
                        if confidence > 0.5:
                            label = self.COCO_INSTANCE_CATEGORY_NAMES[int(box.cls)]
                            if label != '__background__' and label != 'N/A':
                                detected.add(f"{label} ({confidence:.2f})")
                
                # Print detected objects
                if detected:
                    print(f"Detected objects: {', '.join(detected)}")
                
                # Show the frame with bounding boxes
                annotated_frame = results[0].plot()  # YOLOv8 provides a method to draw boxes
                cv2.imshow('Object Detection', annotated_frame)
                
                # Check for 'q' key to exit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        finally:
            # Clean up
            picam2.stop()
            cv2.destroyAllWindows()

    def detect_intent(self, user_input):
        # Returns 'chat' or None
        embeddings = self.intent_model.encode([user_input] + self.switch_phrases)
        similarities = util.cos_sim(embeddings[0], embeddings[1:])[0]
        max_idx = similarities.argmax().item()
        if similarities[max_idx] > 0.7:
            return 'chat'
        return None
