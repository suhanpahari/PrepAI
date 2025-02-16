from oceanai.modules.lab.build import Run

_b5 = Run(
    lang = 'en', 
    color_simple = '#333', 
    color_info = '#1776D2', 
    color_err = '#FF0000', 
    color_true = '#008001', 
    bold_text = True, # Bold text
    num_to_df_display = 30,
    text_runtime = 'Runtime', 
    metadata = True
)

res_load_video_model_hc = _b5.load_video_model_hc(
    lang = 'en', 
    show_summary = False, 
    out = True, # Display
    runtime = True, 
    run = True 
)

_b5.video_model_hc_

_b5.video_model_hc_['openness']

# Application to process video and predict personality traits
def analyze_video(video_path):
    res_load_video_model_hc = _b5.video_model_hc_(
        path=video_path,
        num_threads=6,
        out=True,
        runtime=True,
        run=True
    )
    return res_load_video_model_hc

if __name__ == "__main__":
    video_file = "sample_video.mp4"
    result = analyze_video(video_file)
    print("Predicted Personality Traits:", result)