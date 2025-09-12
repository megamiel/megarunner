from flask import Flask, request, jsonify
import subprocess
import sys
import uuid
import os
import psycopg2
import json
import base64 # Base64エンコードのためにインポート

# --- Vercel Postgres への接続 ---
DATABASE_URL = os.environ.get('POSTGRES_URL')
# --- 接続設定ここまで ---

# Flaskアプリケーションを初期化
app = Flask(__name__)


# エンドポイント1: スクリプトをアップロード（デプロイ）する
@app.route('/api/upload', methods=['POST'])
def upload_and_save_code():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    uploaded_file = request.files['file']
    
    if uploaded_file.filename == '' or not uploaded_file.filename.endswith('.py'):
        return jsonify({'error': 'Please upload a valid .py file'}), 400

    conn = None
    try:
        code_content = uploaded_file.read().decode('utf-8')
        script_id = str(uuid.uuid4())
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO scripts (id, code) VALUES (%s, %s)",
            (script_id, code_content)
        )
        conn.commit()
        cursor.close()

        base_url = "https://megarunner.vercel.app"
        execution_url = f"{base_url}/api/run/{script_id}"
        
        return jsonify({
            'message': 'Script uploaded successfully!',
            'script_id': script_id,
            'execution_url': execution_url
        }), 201

    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()


# エンドポイント2: 保存されたスクリプトを実行する
@app.route('/api/run/<string:script_id>', methods=['GET', 'POST'])
def run_saved_code(script_id):
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT code FROM scripts WHERE id = %s", (script_id,))
        result = cursor.fetchone()
        cursor.close()

        if not result:
            return jsonify({'error': 'Script with the given ID not found'}), 404
            
        code_to_run = result[0]

        request_data = {}
        if request.method == 'GET':
            request_data = request.args.to_dict()
        elif request.method == 'POST':
            request_data = request.get_json(silent=True) or {}
        
        args_as_json_string = json.dumps(request_data)

        # ★ 変更点 ★
        # ユーザーコードをBase64にエンコードして、改行などの問題を回避しながら
        # 安全に `executor.py` に渡せるようにします。
        code_b64 = base64.b64encode(code_to_run.encode('utf-8')).decode('utf-8')

        # 実行エンジン `executor.py` を呼び出し、
        # エンコードしたユーザーコードと引数JSONを標準入力で渡します。
        process = subprocess.run(
            [sys.executable, 'executor.py'],
            input=f"{code_b64}\n{args_as_json_string}",
            capture_output=True,
            text=True,
            timeout=10,
            check=False
        )
        
        try:
            # executor.pyから返ってきたJSONをパースします
            final_result = json.loads(process.stdout)
            return jsonify(final_result)
        except json.JSONDecodeError:
            # executor.py自体でエラーが起きた場合
            return jsonify({
                'error': 'Execution engine failed to produce valid JSON.',
                'raw_stdout': process.stdout,
                'raw_stderr': process.stderr
            }), 500

    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred in Flask app: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

