import cv2
import mediapipe as mp
import numpy as np

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Define the indices for the iris and eye corner landmarks in the MediaPipe Face Mesh
LEFT_IRIS_INDICES = [474, 475, 476, 477]
RIGHT_IRIS_INDICES = [469, 470, 471, 472]
LEFT_EYE_CORNERS = [33, 133]  # Left eye outer and inner corners
RIGHT_EYE_CORNERS = [362, 263]  # Right eye outer and inner corners

# Threshold distance for warning (normalized coordinates)
WARNING_THRESHOLD = 0.1

# Function to calculate the iris center
def calculate_iris_center(landmarks, iris_indices):
    iris_points = np.array([(landmarks[idx].x, landmarks[idx].y) for idx in iris_indices])
    iris_center = np.mean(iris_points, axis=0)
    return iris_center

# Function to calculate Euclidean distance between two points
def euclidean_distance(point1, point2):
    return np.linalg.norm(np.array(point1) - np.array(point2))

# Initialize webcam
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Convert the frame to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process the frame with MediaPipe Face Mesh
    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            # Get the iris centers
            left_iris_center = calculate_iris_center(face_landmarks.landmark, LEFT_IRIS_INDICES)
            right_iris_center = calculate_iris_center(face_landmarks.landmark, RIGHT_IRIS_INDICES)

            # Get the eye corners
            left_eye_corners = [(face_landmarks.landmark[idx].x, face_landmarks.landmark[idx].y) for idx in LEFT_EYE_CORNERS]
            right_eye_corners = [(face_landmarks.landmark[idx].x, face_landmarks.landmark[idx].y) for idx in RIGHT_EYE_CORNERS]

            # Convert normalized coordinates to pixel coordinates
            h, w, _ = frame.shape
            left_iris_center_px = (int(left_iris_center[0] * w), int(left_iris_center[1] * h))
            right_iris_center_px = (int(right_iris_center[0] * w), int(right_iris_center[1] * h))

            # Draw circles at the iris centers
            cv2.circle(frame, left_iris_center_px, 5, (0, 255, 0), -1)
            cv2.circle(frame, right_iris_center_px, 5, (0, 255, 0), -1)

            # Draw circles at the eye corners
            for corner in left_eye_corners:
                corner_px = (int(corner[0] * w), int(corner[1] * h))
                cv2.circle(frame, corner_px, 5, (255, 0, 0), -1)
            for corner in right_eye_corners:
                corner_px = (int(corner[0] * w), int(corner[1] * h))
                cv2.circle(frame, corner_px, 5, (255, 0, 0), -1)

            # Check distances for left eye
            for corner in left_eye_corners:
                distance = euclidean_distance(left_iris_center, corner)
                if distance < WARNING_THRESHOLD:
                    cv2.putText(frame, "WARNING: Left iris too close to corner!", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # Check distances for right eye
            for corner in right_eye_corners:
                distance = euclidean_distance(right_iris_center, corner)
                if distance < WARNING_THRESHOLD:
                    cv2.putText(frame, "WARNING: Right iris too close to corner!", (10, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # Display the frame
    cv2.imshow('Iris Tracking with Warnings', frame)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()