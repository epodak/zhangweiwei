import os
import json
import logging
from flask import Flask, request, jsonify
from typing import List, Tuple

# 设置日志配置
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

def partial_ratio(str1: str, str2: str) -> float:
    """计算两个字符串的模糊匹配比率"""
    str1 = str1.lower()
    str2 = str2.lower()

    if str1 == str2:
        return 100

    if str1 in str2 or str2 in str1:
        return 100

    if len(str1) > len(str2):
        str1, str2 = str2, str1

    len1 = len(str1)
    len2 = len(str2)

    max_ratio = 0

    for i in range(len2 - len1 + 1):
        matches = sum(1 for j in range(len1) if str1[j] == str2[i + j])
        ratio = (matches / len1) * 100
        if ratio > max_ratio:
            max_ratio = ratio
            if max_ratio == 100:
                break

    return max_ratio

def search_json_files(folder_path: str, query: str, min_ratio: float = 50.0, 
                     min_similarity: float = 0.0, max_results: int = None) -> List[
    Tuple[str, str, float, str, float]]:
    """搜索文件夹中所有JSON文件，返回匹配结果"""
    results = []
    query = query.lower()

    # 打印当前目录及上级目录的文件夹内容
    current_directory = os.getcwd()
    logging.debug(f"当前工作目录: {current_directory}")
    current_directory_folders = [f for f in os.listdir(current_directory) if os.path.isdir(os.path.join(current_directory, f))]
    logging.debug(f"当前目录的所有文件夹: {current_directory_folders}")

    parent_directory = os.path.dirname(current_directory)
    parent_directory_folders = [f for f in os.listdir(parent_directory) if os.path.isdir(os.path.join(parent_directory, f))]
    logging.debug(f"上级目录: {parent_directory}")
    logging.debug(f"上级目录的所有文件夹: {parent_directory_folders}")

    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            try:
                logging.debug(f"处理文件: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for item in data:
                    timestamp = item.get('timestamp', '')
                    similarity = float(item.get('similarity', 0.0))
                    text = item.get('text', '')

                    if similarity < min_similarity:
                        continue

                    exact_match = query in text.lower()
                    match_ratio = 100 if exact_match else partial_ratio(query, text)

                    if match_ratio >= min_ratio:
                        results.append((filename, timestamp, similarity, text, match_ratio))

            except Exception as e:
                logging.error(f"处理文件 {filename} 时出错: {str(e)}")
                continue

    results.sort(key=lambda x: (-x[4], not (query in x[3].lower())))

    if max_results is not None and len(results) > max_results:
        results = results[:max_results]

    return results

@app.route('/search', methods=['GET'])
def search():
    try:
        default_folder = 'subtitle'

        # 打印当前文件夹路径并检查其存在
        logging.debug(f"正在检查文件夹: {default_folder}")
        if not os.path.isdir(default_folder):
            logging.error(f"默认的'subtitle'文件夹不存在: {default_folder}")
            return jsonify({
                'status': 'error',
                'message': f"默认的'subtitle'文件夹不存在: {default_folder}"
            }), 400

        # 打印请求参数
        query = request.args.get('query', '')
        min_ratio = request.args.get('min_ratio', default=50, type=float)
        min_similarity = request.args.get('min_similarity', default=0, type=float)
        max_results = request.args.get('max_results', default=None, type=int)

        logging.debug(f"请求参数: query={query}, min_ratio={min_ratio}, min_similarity={min_similarity}, max_results={max_results}")

        if not query:
            return jsonify({
                'status': 'error',
                'message': '搜索关键词不能为空'
            }), 400

        if not (0 <= min_ratio <= 100):
            return jsonify({
                'status': 'error',
                'message': '最小匹配率必须在0-100之间'
            }), 400

        if not (0 <= min_similarity <= 1):
            return jsonify({
                'status': 'error',
                'message': '最小原始相似度必须在0-1之间'
            }), 400

        if max_results is not None and max_results <= 0:
            return jsonify({
                'status': 'error',
                'message': '最大返回结果数量必须大于0'
            }), 400

        results = search_json_files(default_folder, query, min_ratio, min_similarity, max_results)

        if results:
            formatted_results = [
                {
                    'filename': filename,
                    'timestamp': timestamp,
                    'similarity': similarity,
                    'text': text,
                    'match_ratio': match_ratio,
                    'exact_match': query in text.lower()
                }
                for filename, timestamp, similarity, text, match_ratio in results
            ]
            return jsonify({
                'status': 'success',
                'data': formatted_results,
                'count': len(results),
                'folder': default_folder,
                'max_results': max_results if max_results is not None else 'unlimited'
            })
        else:
            return jsonify({
                'status': 'success',
                'data': [],
                'count': 0,
                'folder': default_folder,
                'max_results': max_results if max_results is not None else 'unlimited',
                'message': f"未找到与 '{query}' 匹配的结果",
                'suggestions': [
                    '检查输入是否正确',
                    f'尝试降低最小匹配率（当前：{min_ratio}%）',
                    f'尝试降低最小原始相似度（当前：{min_similarity}）',
                    '尝试使用更简短的关键词'
                ]
            })

    except Exception as e:
        logging.error(f"发生错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"发生错误: {str(e)}"
        }), 500

# 直接使用 Flask 的 WSGI 应用作为入口
application = app

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8000)