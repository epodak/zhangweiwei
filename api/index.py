import os
import json
import logging
import subprocess
from flask import Flask, request, jsonify
from typing import List, Tuple

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

@app.route('/search', methods=['GET'])
def search():
    try:
        query = request.args.get('query', '')
        min_ratio = request.args.get('min_ratio', '50')
        min_similarity = request.args.get('min_similarity', '0.5')
        max_results = request.args.get('max_results', '10')

        query_string = f"query={query}"
        if min_ratio:
            query_string += f"&min_ratio={min_ratio}"
        if min_similarity:
            query_string += f"&min_similarity={min_similarity}"
        if max_results:
            query_string += f"&max_results={max_results}"


        rust_process = subprocess.Popen(
            ['./api/subtitle_search_api'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = rust_process.communicate(input=query_string)

        if rust_process.returncode != 0:
            logging.error(f"Rust process error: {stderr}")
            return jsonify({
                "status": "error",
                "error": stderr
            }), 500

        try:
            result = json.loads(stdout)
            return jsonify(result)
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {e}")
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

application = app

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8000)