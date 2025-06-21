import torch
from transformers import AutoImageProcessor, AutoModelForObjectDetection
from PIL import Image
import numpy as np
import cv2
import time

class ObjectDetector:
    def __init__(self):
        # Initialize the model and processor
        self.processor = AutoImageProcessor.from_pretrained("microsoft/table-transformer-detection")
        self.model = AutoModelForObjectDetection.from_pretrained("microsoft/table-transformer-detection")
        
    def detect_objects(self, image):
        # Convert OpenCV image (BGR) to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # Convert to PIL Image
        pil_image = Image.fromarray(image_rgb)
        
        # Process the image
        inputs = self.processor(images=pil_image, return_tensors="pt")
        
        # Perform object detection
        outputs = self.model(**inputs)
        
        # Convert outputs to COCO API format
        target_sizes = torch.tensor([pil_image.size[::-1]])
        results = self.processor.post_process_object_detection(
            outputs, target_sizes=target_sizes, threshold=0.7
        )[0]
        
        # Process and return results
        detections = []
        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            detections.append({
                "label": self.model.config.id2label[label.item()],
                "score": round(score.item(), 3),
                "box": box.tolist()
            })
        
        return detections

def draw_detections(image, detections):
    for detection in detections:
        box = detection["box"]
        label = detection["label"]
        score = detection["score"]
        
        # Convert box coordinates to integers
        x1, y1, x2, y2 = map(int, box)
        
        # Draw bounding box
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Prepare label text
        label_text = f"{label}: {score:.2f}"
        
        # Draw label background
        (text_width, text_height), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
        cv2.rectangle(image, (x1, y1 - text_height - 10), (x1 + text_width, y1), (0, 255, 0), -1)
        
        # Draw label text
        cv2.putText(image, label_text, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    
    return image

def main():
    # Initialize the detector
    detector = ObjectDetector()
    
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return
    
    print("Press 'q' to quit")
    
    # Variables for FPS calculation
    frame_count = 0
    start_time = time.time()
    fps = 0
    
    while True:
        # Read frame from webcam
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame")
            break
        
        # Calculate FPS
        frame_count += 1
        if frame_count >= 30:  # Update FPS every 30 frames
            end_time = time.time()
            fps = frame_count / (end_time - start_time)
            frame_count = 0
            start_time = time.time()
        
        # Perform object detection
        detections = detector.detect_objects(frame)
        
        # Draw detections on frame
        frame = draw_detections(frame, detections)
        
        # Display FPS
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Display the frame
        cv2.imshow("Object Detection", frame)
        
        # Break loop on 'q' press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main() 