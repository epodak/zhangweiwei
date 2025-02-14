from create_db import create_subtitle_database
from import_subtitles import import_subtitles
from search_subtitles import search_subtitles

def main():
    # 1. 创建数据库
    print("正在创建数据库...")
    create_subtitle_database()
    
    # 2. 导入字幕数据
    print("正在导入字幕数据...")
    subtitle_dir = "subtitle"  # 你的字幕目录路径
    import_subtitles(subtitle_dir)
    
    # 3. 进行搜索
    while True:
        query = input("\n请输入要搜索的文本（输入 'q' 退出）: ")
        if query.lower() == 'q':
            break
            
        results = search_subtitles(query)
        
        if not results:
            print("未找到匹配结果")
            continue
            
        print(f"\n找到 {len(results)} 条结果：")
        for result in results:
            print("\n-------------------")
            print(f"剧集：{result['episode_title']}")
            print(f"时间戳：{result['timestamp']}")
            print(f"相似度：{result['similarity']}")
            print(f"文本：{result['text']}")
            print(f"匹配率：{result['match_ratio']}%")

if __name__ == "__main__":
    main()
