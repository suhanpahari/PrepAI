import os
from oceanai.modules.lab.build import Run

class VideoAnalyzer:
    def __init__(self):
        self._b5 = Run(
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
        self._b5.path_to_save_ = './models'
        self._b5.chunk_size_ = 2000000
        self.load_model()
        self.download_weights()

    def load_model(self):
        print("\n[INFO] Loading video model architecture...")
        self._b5.load_video_model_hc(
            lang='en',
            show_summary=False,
            out=True,
            runtime=True,
            run=True
        )
        print("[SUCCESS] Model architecture loaded.")

    def download_weights(self):
        url = self._b5.weights_for_big5_['video']['fi']['hc']['googledisk']
        print("\n[INFO] Checking and downloading model weights...")
        self._b5.load_video_model_weights_hc(
            url=url,
            force_reload=False,
            out=True,
            runtime=True,
            run=True
        )
        print("[SUCCESS] Model weights loaded.")

    def analyze_video(self, video_path):
        if not os.path.exists(video_path):
            print("[ERROR] Video file not found.")
            return None
            
        print(f"\n[INFO] Analyzing video: {video_path}...")
        results = self._b5.get_video_union_predictions(
            video_paths=[video_path],
            out=True,
            runtime=True,
            run=True
        )
        print("\n[RESULTS] Personality Predictions:")
        return results

# Usage
if __name__ == "__main__":
    video_analyzer = VideoAnalyzer()
    video_path = "sample_video.mp4"
    predictions = video_analyzer.analyze_video(video_path)  # Call analyze_video instead
    if predictions:
        print(predictions)