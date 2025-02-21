import os
from PIL import Image
# 添加 ANTIALIAS 兼容性处理
Image.ANTIALIAS = Image.Resampling.LANCZOS

import numpy as np
import json
import re
from collections import defaultdict
from paddleocr import PaddleOCR
import traceback
import logging

class SubtitleExtractor:
    def __init__(self):
        logging.getLogger("ppocr").setLevel(logging.ERROR)
        try:
            self.ocr = PaddleOCR(
                use_angle_cls=False,
                lang="ch",
                det_model_dir="ch_PP-OCRv4_det_infer",
                rec_model_dir="ch_PP-OCRv4_rec_infer",
                cls_model_dir="ch_PP-OCRv4_cls_infer",
                show_log=False,
                use_gpu=True,
                gpu_mem=500,
                enable_mkldnn=True
            )
        except Exception as e:
            print(f"GPU 初始化失败；回退到 CPU 模式：{str(e)}")
            self.ocr = PaddleOCR(
                use_angle_cls=False,
                lang="ch",
                det_model_dir="ch_PP-OCRv4_det_infer",
                rec_model_dir="ch_PP-OCRv4_rec_infer",
                cls_model_dir="ch_PP-OCRv4_cls_infer",
                show_log=False,
                use_gpu=False,
                enable_mkldnn=True
            )
        
        self.subtitle_area = (235, 900, 235 + 1200, 900 + 90)
        
        # 正则表达式模式
        self.pattern = r'([^_]+)_(\d+m\d+s)_sim_(\d+\.\d+)'
        
        # 存储字幕的字典
        self.subtitles_dict = defaultdict(list)

    def parse_timestamp(self, timestamp):
        """将时间戳 (如 "2m28s") 转换为总秒数"""
        match = re.match(r'(\d+)m(\d+)s', timestamp)
        if match:
            minutes, seconds = map(int, match.groups())
            return minutes * 60 + seconds
        return 0

    def process_image(self, img_path):
        try:
            img = Image.open(img_path)
            
            if img.size != (1920, 1080):
                raise ValueError("Incorrect image size")
            
            # 将PIL Image转换为numpy数组
            img_array = np.array(img)
            
            # OCR识别整张图片
            result = self.ocr.ocr(img_array, cls=True)
            
            # 释放 img 和 img_array
            img.close()
            del img, img_array
            
            if result and result[0]:
                texts = []
                for line in result[0]:
                    box = line[0]
                    box_in_area = all(
                        self.subtitle_area[0] <= point[0] <= self.subtitle_area[2] and
                        self.subtitle_area[1] <= point[1] <= self.subtitle_area[3]
                        for point in box
                    )
                    
                    if box_in_area and line[1][1] > 0.8:
                        texts.append(line[1][0])
                
                return ' '.join(texts).strip()
            return None
            
        except Exception as e:
            print(f"Error processing image {img_path}:")
            traceback.print_exc()
            return None

    def process_frames(self, input_folder, output_folder):
        """处理文件夹中的所有帧并生成字幕"""
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        for filename in sorted(os.listdir(input_folder)):
            if not filename.endswith(('.jpg', '.png')):
                continue
            
            match = re.match(self.pattern, filename)
            if not match:
                 continue
            
            title, timestamp, similarity = match.groups()
            video_title = f"{title}"
            print(f"处理文件: {filename}")
            
            img_path = os.path.join(input_folder, filename)
            text = self.process_image(img_path)
            
            if not text:
                continue

            print(f"识别到文本: {text}")
            
            # 检查重复
            subtitles = self.subtitles_dict[video_title]
            if subtitles and subtitles[-1]["text"] == text:
                continue
            
            # 添加字幕
            self.subtitles_dict[video_title].append({
                "timestamp": timestamp,
                "similarity": float(similarity),
                "text": text
            })

        # 保存字幕文件
        for video_title, subtitles in self.subtitles_dict.items():
            sorted_subtitles = sorted(subtitles, key=lambda x: self.parse_timestamp(x["timestamp"]))
            output_json = os.path.join(output_folder, f"{video_title}.json")
            
            try:
                with open(output_json, 'w', encoding='utf-8') as f:
                    json.dump(sorted_subtitles, f, ensure_ascii=False, indent=4)
                print(f"成功保存 {video_title} 的字幕")
            except Exception as e:
                print(f"保存文件时出错: {str(e)}")

        print("\n处理完成")