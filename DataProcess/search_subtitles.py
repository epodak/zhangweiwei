import sqlite3
from fuzzywuzzy import fuzz

def search_subtitles(query, min_ratio=60):
    conn = sqlite3.connect('subtitles.db')
    cursor = conn.cursor()
    
    # 检查是否包含空格
    if ' ' in query:
        # 严格搜索模式：分割关键词
        keywords = query.split()
        cursor.execute('''
        SELECT episode_title, timestamp, similarity, text
        FROM subtitles
        ''')
        
        all_results = cursor.fetchall()
        matched_results = []
        
        for row in all_results:
            # 检查所有关键词是否都在文本中
            if all(keyword in row[3] for keyword in keywords):
                matched_results.append({
                    'episode_title': row[0],
                    'timestamp': row[1],
                    'similarity': row[2],
                    'text': row[3],
                    'match_ratio': 100  # 严格匹配时设为100%
                })
    else:
        # 模糊搜索模式
        cursor.execute('''
        SELECT episode_title, timestamp, similarity, text
        FROM subtitles
        ''')
        
        all_results = cursor.fetchall()
        matched_results = []
        
        for row in all_results:
            ratio = fuzz.partial_ratio(query, row[3])
            if ratio >= min_ratio:
                matched_results.append({
                    'episode_title': row[0],
                    'timestamp': row[1],
                    'similarity': row[2],
                    'text': row[3],
                    'match_ratio': ratio
                })
    
    conn.close()
    return sorted(matched_results, key=lambda x: x['match_ratio'], reverse=True)
