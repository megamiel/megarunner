from flask import Flask, request, jsonify
import subprocess
import sys
import uuid
import os
import psycopg2
import json # JSONを扱うためにインポート

# --- Vercel Postgres への接続 ---
# Vercelが自動的に設定してくれる環境変数からデータベースの接続URLを取得
DATABASE_URL = os.environ.get('POSTGRES_URL')
# --- 接続設定ここまで ---


# Flaskアプリケーションを初期化
app = Flask(__name__)


# エンドポイント1: ファイルをアップロードして実行URLを生成
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
            'message': 'File uploaded and script created successfully!',
            'script_id': script_id,
            'execution_url': execution_url
        }), 201

    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()


# エンドポイント2: 保存されたコードを実行（名前付き引数に対応）
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

        # --- ★ 引数を「辞書」として取得するロジック ---
        request_data = {}
        if request.method == 'GET':
            # ?key=value 形式の全クエリパラメータを辞書に変換
            request_data = request.args.to_dict()
        elif request.method == 'POST':
            # POSTされたJSONボディをそのまま辞書として使用
            # もしJSONでなければ空の辞書にする
            request_data = request.get_json(silent=True) or {}
        
        # 辞書をJSON文字列に変換して、スクリプトに渡す準備
        args_as_json_string = json.dumps(request_data)
        # --- 引数取得ロジックここまで ---

        # 実行コマンドを組み立てる
        # [ "python", "-c", "スクリプトコード", "引数辞書のJSON文字列" ]
        command = [sys.executable, '-c', code_to_run, args_as_json_string]

        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
            check=False
        )

        return jsonify({
            'stdout': process.stdout,
            'stderr': process.stderr,
            'returncode': process.returncode
        })
        
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

