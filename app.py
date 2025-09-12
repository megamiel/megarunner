from flask import Flask, request, jsonify
import subprocess
import sys

# Flaskアプリケーションを初期化
app = Flask(__name__)

@app.route('/api/execute', methods=['POST'])
def execute_code():
    # POSTリクエストからJSONデータを取得
    data = request.get_json()
    if not data or 'code' not in data:
        return jsonify({'error': 'No code provided'}), 400

    code = data['code']

    try:
        # ユーザーコードを安全に実行するための準備
        process = subprocess.run(
            [sys.executable, '-c', code],
            capture_output=True,
            text=True,
            timeout=10,
            check=False
        )

        # 実行結果を返す
        return jsonify({
            'stdout': process.stdout,
            'stderr': process.stderr,
            'returncode': process.returncode
        })

    except subprocess.TimeoutExpired:
        return jsonify({
            'error': 'Execution timed out (10 seconds limit)',
            'stdout': '',
            'stderr': 'TimeoutExpired: The code took too long to execute.'
        }), 408
        
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

# Vercelがこの 'app' をWSGIエントリーポイントとして認識します