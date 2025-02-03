import cv2

def list_available_cameras(max_cameras=10):
    available_cameras = []
    for index in range(max_cameras):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            available_cameras.append(index)
            cap.release()
    return available_cameras

cameras = list_available_cameras()

if cameras:
    print(f"Available cameras: {cameras}")
else:
    print("No cameras detected.")
