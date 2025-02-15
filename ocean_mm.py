import os
import glob
from oceanai.modules.lab.build import Run

_b5 = Run(
    lang='en',
    color_simple='#333',
    color_info='#1776D2',
    color_err='#FF0000',
    color_true='#008001',
    bold_text=True,
    num_to_df_display=30,
    text_runtime='Runtime',
    metadata=True
)

res_load_av_models_b5 = _b5.load_av_models_b5(
    show_summary=False,
    out=True,
    runtime=True,
    run=True
)

# Set the directory where models are saved
_b5.path_to_save_ = './models'
_b5.chunk_size_ = 2000000

# Function to get the latest model file based on modification time
def get_latest_model(path, keyword):
    """Finds the latest model file in the given directory matching a keyword."""
    files = glob.glob(os.path.join(path, f"*{keyword}*"))
    if not files:
        raise FileNotFoundError(f"No model found for {keyword}")
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

# Dynamically find the latest saved model weights
latest_openness = get_latest_model(_b5.path_to_save_, "openness")
latest_conscientiousness = get_latest_model(_b5.path_to_save_, "conscientiousness")
latest_extraversion = get_latest_model(_b5.path_to_save_, "extraversion")
latest_agreeableness = get_latest_model(_b5.path_to_save_, "agreeableness")
latest_non_neuroticism = get_latest_model(_b5.path_to_save_, "non_neuroticism")

# Load the latest available models instead of downloading
res_load_av_models_weights_b5 = _b5.load_av_models_weights_b5(
    url_openness=latest_openness,
    url_conscientiousness=latest_conscientiousness,
    url_extraversion=latest_extraversion,
    url_agreeableness=latest_agreeableness,
    url_non_neuroticism=latest_non_neuroticism,
    force_reload=False,  # Avoid unnecessary reloading
    out=True,
    runtime=True,
    run=True
)

_b5.av_models_b5_['openness']

# Application to process video and predict personality traits
def analyze_video(video_path):
    res_predict_av_b5 = _b5.predict_av_b5(
        path=video_path,
        num_threads=6,
        out=True,
        runtime=True,
        run=True
    )
    return res_predict_av_b5

if __name__ == "__main__":
    video_file = "sample_video.mp4"
    result = analyze_video(video_file)
    print("Predicted Personality Traits:", result)