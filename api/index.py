import os
import json
import logging
import subprocess
from flask import Flask, request, jsonify, send_file
from typing import List, Tuple

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)


@app.route('/search', methods=['GET'])
def search():
    try:
        query = request.args.get('query', '')
        min_ratio = request.args.get('min_ratio', '50')
        min_similarity = request.args.get('min_similarity', '0.5')

        query_string = f"query={query}"
        query_string += f"&min_ratio={min_ratio}"
        query_string += f"&min_similarity={min_similarity}"

        def generate():
            rust_process = subprocess.Popen(
                ['./api/subtitle_search_api'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            rust_process.stdin.write(query_string + '\n')
            rust_process.stdin.flush()
            
            first_item = True
            while True:
                line = rust_process.stdout.readline()
                if not line:
                    break
                    
                if not first_item:
                    yield '\n'
                first_item = False
                
                yield line.strip()
            
            rust_process.terminate()

        return app.response_class(generate(), mimetype='application/json')

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


application = app

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8000)
