# Real-time Object Detection App

This is a Python application that performs real-time object detection using a webcam and a pre-trained model from Hugging Face. The application uses the DETR (DEtection TRansformer) model with a ResNet-50 backbone, which is capable of detecting various objects in real-time video feed.

## Requirements

- Python 3.7 or higher
- PyTorch
- Transformers library
- Pillow
- NumPy
- OpenCV

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the script:
```bash
python object_detection.py
```

2. The application will:
   - Open your webcam
   - Show the video feed with real-time object detection
   - Display bounding boxes and labels for detected objects
   - Show the current FPS (Frames Per Second)

3. Press 'q' to quit the application

## Features

- Real-time object detection using webcam feed
- Uses the state-of-the-art DETR model for object detection
- Runs completely locally (no internet required after initial model download)
- Displays bounding boxes and confidence scores for detected objects
- Shows real-time FPS counter
- Supports detection of 91 different classes of objects

## Model Information

The application uses the `facebook/detr-resnet-50` model from Hugging Face, which is pre-trained on the COCO dataset. It can detect 91 different classes of objects.

## Note

- The first time you run the application, it will download the model files (approximately 150MB). This only happens once, and subsequent runs will use the cached model files.
- Make sure your webcam is properly connected and accessible before running the application.
- The detection speed may vary depending on your computer's specifications. 