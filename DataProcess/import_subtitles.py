import json
import sqlite3
import os

def import_subtitles(subtitle_dir):
    conn = sqlite3.connect('subtitles.db')
    cursor = conn.cursor()
    
    for filename in os.listdir(subtitle_dir):
        if filename.endswith('.json'):
            episode_title = os.path.splitext(filename)[0]
            
            with open(os.path.join(subtitle_dir, filename), 'r', encoding='utf-8') as f:
                subtitles = json.load(f)
                
            for subtitle in subtitles:
                # 插入到主表
                cursor.execute('''
                INSERT INTO subtitles (episode_title, timestamp, similarity, text)
                VALUES (?, ?, ?, ?)
                ''', (episode_title, subtitle['timestamp'], subtitle['similarity'], subtitle['text']))
                
                # 同步插入到全文搜索表
                cursor.execute('''
                INSERT INTO subtitles_fts (episode_title, timestamp, similarity, text)
                VALUES (?, ?, ?, ?)
                ''', (episode_title, subtitle['timestamp'], subtitle['similarity'], subtitle['text']))
    
    conn.commit()
    conn.close() 