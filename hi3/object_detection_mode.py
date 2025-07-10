import cv2
import torch
import torchvision
from sentence_transformers import SentenceTransformer, util
import numpy as np

class ObjectDetectionMode:
    def __init__(self):
        # Load a pre-trained MobileNet SSD model from torchvision
        self.model = torchvision.models.detection.ssdlite320_mobilenet_v3_large(pretrained=True)
        self.model.eval()
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
        cap = cv2.VideoCapture(camera_index)
        print("[ObjectDetectionMode] Press 'q' to stop object detection.")
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[ObjectDetectionMode] Failed to grab frame.")
                break
            # Convert frame to tensor
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = torch.from_numpy(img / 255.).permute(2, 0, 1).float().unsqueeze(0)
            with torch.no_grad():
                preds = self.model(img)[0]
            labels = preds['labels'].numpy()
            scores = preds['scores'].numpy()
            detected = set()
            for label, score in zip(labels, scores):
                if score > 0.5:
                    detected.add(self.COCO_INSTANCE_CATEGORY_NAMES[label])
            if detected:
                print(f"Detected objects: {', '.join(detected)}")
            # Show the frame
            cv2.imshow('Object Detection', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()

    def detect_intent(self, user_input):
        # Returns 'chat' or None
        embeddings = self.intent_model.encode([user_input] + self.switch_phrases)
        similarities = util.cos_sim(embeddings[0], embeddings[1:])[0]
        max_idx = similarities.argmax().item()
        if similarities[max_idx] > 0.7:
            return 'chat'
        return None 