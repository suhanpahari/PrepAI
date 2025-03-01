import cv2
import mediapipe as mp

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh()

cap = cv2.VideoCapture(0)

# Variables to store previous positions
prev_nose_x = None
movement_threshold = 2  # Adjust based on your needs

# Indices for left and right eye landmarks
LEFT_EYE_INDICES = [33, 133]  # Example indices for left eye corners
RIGHT_EYE_INDICES = [362, 263]  # Example indices for right eye corners

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)
    
    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            # Get coordinates for nose and left/right eye landmarks
            nose = face_landmarks.landmark[1]  # Nose tip
            nose_x = int(nose.x * frame.shape[1])
            
            # Check for horizontal movement
            if prev_nose_x is not None:
                movement = abs(nose_x - prev_nose_x)
                if movement > movement_threshold:
                    cv2.putText(frame, "Movement Detected!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                                1, (0, 0, 255), 2, cv2.LINE_AA)
            
            # Update previous position
            prev_nose_x = nose_x
            
            # Draw nose point for reference
            cv2.circle(frame, (nose_x, int(nose.y * frame.shape[0])), 5, (0, 255, 0), -1)
            
            # Draw left eye landmarks
            for idx in LEFT_EYE_INDICES:
                landmark = face_landmarks.landmark[idx]
                x = int(landmark.x * frame.shape[1])
                y = int(landmark.y * frame.shape[0])
                cv2.circle(frame, (x, y), 5, (255, 0, 0), -1)
            
            # Draw right eye landmarks
            for idx in RIGHT_EYE_INDICES:
                landmark = face_landmarks.landmark[idx]
                x = int(landmark.x * frame.shape[1])
                y = int(landmark.y * frame.shape[0])
                cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
    
    cv2.imshow("Eye and Head Movement Tracking", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()