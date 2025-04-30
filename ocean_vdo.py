import os
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.losses import MeanSquaredError
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.applications.resnet50 import preprocess_input

# Load the trained model
model = load_model("vdo.h5", compile=False)
model.compile(optimizer="adam", loss=MeanSquaredError(), metrics=["mae"])
print("✅ Model loaded and compiled successfully!")

# Load the pre-trained ResNet50 model (excluding the top classification layer)
resnet = ResNet50(weights="imagenet", include_top=False, pooling="avg")

def extract_features(video_path):
    """Extract features from a video using ResNet50."""
    if not os.path.exists(video_path):
        print(f"❌ Error: Video file not found at {video_path}")
        return None

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"⚠️ Error opening video: {video_path}")
        return None

    frame_features = []
    frame_count = 0

    while cap.isOpened() and frame_count < 10:  # Extract up to 10 frames
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (224, 224))  # Resize to ResNet50 input size
        frame = preprocess_input(frame.astype(np.float32))  # Preprocess
        frame_features.append(frame)
        frame_count += 1

    cap.release()

    if frame_features:
        frame_features = np.array(frame_features)  # Convert to NumPy array
        video_features = resnet.predict(frame_features)  # Extract CNN features
        video_feature_vector = np.mean(video_features, axis=0)  # Aggregate features
        return video_feature_vector
    else:
        return None

# Path to the new video
new_video_path = "interview_recording.webm"  # Update this with the actual path

# Extract features
video_features = extract_features(new_video_path)

if video_features is not None:
    video_features = video_features.reshape(1, -1)  # Reshape for model input
    prediction = model.predict(video_features)
    print("Predicted OCEAN traits:", prediction)
else:
    print("❌ Feature extraction failed.")
