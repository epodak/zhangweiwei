import json
import os
import gzip
import base64
from pathlib import Path

def optimize_subtitle_database():
    subtitle_dir = Path("subtitle")
    output_file = Path("subtitle_db.gz")
    
    if not subtitle_dir.exists():
        return
    output_file.parent.mkdir(exist_ok=True)
    all_subtitles = []
    
    for json_file in subtitle_dir.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            filename = json_file.name
            episode_match = filename.split("]")[0].replace("[P", "")
            episode_num = int(episode_match) if episode_match.isdigit() else 0
 
            for item in data:
                all_subtitles.append({
                    "e": episode_num,               
                    "f": filename,                 
                    "t": item.get("timestamp", ""),  
                    "s": item.get("similarity", 0),  
                    "x": item.get("text", "")
                })
            
        except Exception as e:
            print(e)
    
    json_data = json.dumps(all_subtitles, ensure_ascii=False)
    compressed_data = gzip.compress(json_data.encode('utf-8'), compresslevel=9)
    
    with open(output_file, "wb") as f:
        f.write(compressed_data)

if __name__ == "__main__":
    optimize_subtitle_database() 