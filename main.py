#from FaceRec import FaceRecognizer
from FaceRec_insightface import FaceRecognizer
#from CutSubtitle import SubtitleExtractor
from CutSubtitle_paddleocr import SubtitleExtractor
import os
import traceback
import re

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


def get_video_progress(video_title, frames_output):
    """获取视频处理进度"""
    if not os.path.exists(frames_output):
        return None
        
    frame_files = [f for f in os.listdir(frames_output) 
                   if f.startswith(video_title + "_")]
    if not frame_files:
        return None
        
    # 从文件名中提取时间戳
    timestamps = []
    for f in frame_files:
        match = re.match(r'.*_(\d+)m(\d+)s_.*', f)
        if match:
            minutes, seconds = map(int, match.groups())
            timestamps.append(minutes * 60 + seconds)
    
    return max(timestamps) if timestamps else None

def process_videos_in_folder(videos_folder, features_file, frames_output, subtitle_output):
    """处理文件夹中的所有视频"""
    # 确保输出目录存在
    os.makedirs(frames_output, exist_ok=True)
    os.makedirs(subtitle_output, exist_ok=True)
    
    # 获取已经生成字幕的视频
    completed_videos = {
        os.path.splitext(f)[0] 
        for f in os.listdir(subtitle_output) 
        if f.endswith('.json')
    }
    
    while True:
        # 获取所有视频文件
        video_extensions = ('.mp4', '.avi', '.mkv', '.mov')
        video_files = [
            f for f in os.listdir(videos_folder)
            if os.path.isfile(os.path.join(videos_folder, f))
            and f.lower().endswith(video_extensions)
            and os.path.splitext(f)[0] not in completed_videos  # 排除已完成字幕的视频
        ]

        if not video_files:
            print("\nAll videos processed successfully!")
            break

        print(f"Found {len(video_files)} videos to process")

        # 处理每个视频
        for i, video_file in enumerate(video_files, 1):
            video_title = os.path.splitext(video_file)[0]
            video_path = os.path.join(videos_folder, video_file)
            print(f"\nProcessing video {i}/{len(video_files)}: {video_file}")
            
            try:
                # 检查是否有处理进度
                progress = get_video_progress(video_title, frames_output)
                if progress is not None:
                    print(f"Resuming from timestamp: {progress//60}m{progress%60}s")
                
                # 处理视频
                face_recognizer = FaceRecognizer(features_file)
                face_recognizer.process_video_with_params(
                    video_path=video_path,
                    output_folder=frames_output,
                    fps=1,
                    start_time=progress  # 添加起始时间参数
                )
                
                # 处理字幕
                subtitle_extractor = SubtitleExtractor()
                subtitle_extractor.process_frames(
                    input_folder=frames_output,
                    output_folder=subtitle_output
                )
                
                # 添加到已完成列表
                completed_videos.add(video_title)
                
                # 清理帧文件
                clean_frames_folder(frames_output)
                print(f"Cleaned frames for {video_file}")

            except Exception:
                print(f"Error processing {video_file}")
                traceback.print_exc()
                continue


if __name__ == "__main__":
    # 配置路径
    videos_folder = "Videos"  # 包含所有视频的文件夹
    #features_file = "face_features.npz"  # 预计算的特征向量文件
    features_file = "face_features_insightface.npz"  # 预计算的特征向量文件
    frames_output = "output_frames"
    subtitle_output = "subtitle"

    process_videos_in_folder(
        videos_folder=videos_folder,
        features_file=features_file,
        frames_output=frames_output,
        subtitle_output=subtitle_output
    )