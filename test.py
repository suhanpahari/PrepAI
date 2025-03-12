import cv2

def record_video(output_file='output.avi', duration=10, fps=20.0):
    cap = cv2.VideoCapture(0)  # Open default webcam
    
    if not cap.isOpened():
        print("Error: Could not open video device.")
        return
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
    
    print("Recording... Press 'q' to stop early.")
    
    frame_count = 0
    max_frames = duration * fps
    
    while frame_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        
        out.write(frame)
        cv2.imshow('Recording', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        frame_count += 1
    
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print("Recording saved as", output_file)

if __name__ == "__main__":
    record_video()
