import sqlite3
import os

def create_subtitle_database():
    # 如果数据库文件存在，先删除它
    if os.path.exists('subtitles.db'):
        os.remove('subtitles.db')
        print("已删除旧的数据库文件")
    
    conn = sqlite3.connect('subtitles.db')
    cursor = conn.cursor()
    
    # 创建字幕表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subtitles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        episode_title TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        similarity REAL,
        text TEXT NOT NULL
    )
    ''')
    
    # 创建全文搜索索引
    cursor.execute('''
    CREATE VIRTUAL TABLE IF NOT EXISTS subtitles_fts USING fts5(
        episode_title,
        timestamp,
        similarity,
        text,
        content='subtitles',
        content_rowid='id'
    )
    ''')
    
    conn.commit()
    conn.close()
    print("已创建新的数据库文件") 