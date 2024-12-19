from FaceRec import FaceRecognizer
from CutSubtitle import SubtitleExtractor
import os

def process_video(video_path, features_file, frames_output, subtitle_output):
    """
    处理视频并生成字幕

    Args:
        video_path (str): 视频文件路径
        features_file (str): 预计算的特征向量文件路径 (.npz)
        frames_output (str): 帧输出文件夹路径
        subtitle_output (str): 字幕输出文件夹路径
    """
    # 步骤 1: 人脸识别和帧提取
    face_recognizer = FaceRecognizer(features_file)
    face_recognizer.process_video_with_params(
        video_path=video_path,
        output_folder=frames_output,
        fps=1
    )

    # 步骤 2: 字幕提取
    subtitle_extractor = SubtitleExtractor()
    subtitle_extractor.process_frames(
        input_folder=frames_output,
        output_folder=subtitle_output
    )


if __name__ == "__main__":
    # 示例使用
    video_path = "Videos/[P003]3 测试.mp4"
    features_file = "face_features.npz"  # 预计算的特征向量文件
    frames_output = "output_frames"
    subtitle_output = "subtitle"

    process_video(
        video_path=video_path,
        features_file=features_file,
        frames_output=frames_output,
        subtitle_output=subtitle_output
    )