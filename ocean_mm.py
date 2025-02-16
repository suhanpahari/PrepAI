import os
import glob

def get_latest_model(base_path, keyword):
    """Finds the latest model file in the given directory or subdirectories."""
    files = glob.glob(os.path.join(base_path, "**", f"*{keyword}*"), recursive=True)
    if not files:
        raise FileNotFoundError(f"No model found for {keyword}")
    latest_file = max(files, key=os.path.getmtime)  # Get the latest file by modification time
    return latest_file

model_path = "./models"
latest_openness = get_latest_model(model_path, "openness")
print("Latest openness model found at:", latest_openness)
