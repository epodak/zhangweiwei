from FaceRec import FaceRecognizer
from CutSubtitle import SubtitleExtractor
import os
import shutil


def clean_frames_folder(frames_output):
    """清理帧输出文件夹中的所有文件"""
    if os.path.exists(frames_output):
        for file in os.listdir(frames_output):
            file_path = os.path.join(frames_output, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error: {e}")


def process_video(video_path, features_file, frames_output, subtitle_output):
    """处理单个视频并生成字幕"""
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


def process_videos_in_folder(videos_folder, features_file, frames_output, subtitle_output):
    """处理文件夹中的所有视频"""
    # 确保输出目录存在
    os.makedirs(frames_output, exist_ok=True)
    os.makedirs(subtitle_output, exist_ok=True)

    # 获取所有视频文件
    video_extensions = ('.mp4', '.avi', '.mkv', '.mov')
    video_files = [f for f in os.listdir(videos_folder)
                   if os.path.isfile(os.path.join(videos_folder, f))
                   and f.lower().endswith(video_extensions)]

    print(f"Found {len(video_files)} videos to process")

    # 处理每个视频
    for i, video_file in enumerate(video_files, 1):
        video_path = os.path.join(videos_folder, video_file)
        print(f"\nProcessing video {i}/{len(video_files)}: {video_file}")

        try:
            # 处理视频
            process_video(video_path, features_file, frames_output, subtitle_output)

            # 清理帧文件
            clean_frames_folder(frames_output)
            print(f"Cleaned frames for {video_file}")

        except Exception as e:
            print(f"Error processing {video_file}: {e}")
            continue

    print("\nAll videos processed successfully!")


if __name__ == "__main__":
    # 配置路径
    videos_folder = "Videos"  # 包含所有视频的文件夹
    features_file = "face_features.npz"  # 预计算的特征向量文件
    frames_output = "output_frames"
    subtitle_output = "subtitle"

    process_videos_in_folder(
        videos_folder=videos_folder,
        features_file=features_file,
        frames_output=frames_output,
        subtitle_output=subtitle_output
    )