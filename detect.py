import torch
import cv2
import numpy as np

# Load YOLOv5 model (nano version for speed)
model = torch.hub.load('ultralytics/yolov5', 'yolov5n', pretrained=True)

# Open the Raspberry Pi camera
cap = cv2.VideoCapture(0)  # 0 is the default camera

if not cap.isOpened():
    print("Cannot open camera")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break

    # Inference
    results = model(frame)

    # Render results on the frame
    annotated_frame = np.squeeze(results.render())

    # Show the frame
    cv2.imshow('YOLOv5 Live Detection', annotated_frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()