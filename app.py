from flask import Flask, request, jsonify
import subprocess
import sys
import uuid
import os
import psycopg2 # PostgreSQLに接続するためのライブラリ

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

    conn = None # 接続オブジェクトを初期化
    try:
        code_content = uploaded_file.read().decode('utf-8')
        script_id = str(uuid.uuid4())
        
        # データベースに接続
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # SQLクエリを実行して、Postgresにコードを保存
        cursor.execute(
            "INSERT INTO scripts (id, code) VALUES (%s, %s)",
            (script_id, code_content)
        )
        # 変更を確定
        conn.commit()
        
        cursor.close()

        # ★★★ 変更点 ★★★
        # プレビューURLではなく、常に本番の公開URLを返すように固定
        base_url = "https://megarunner.vercel.app"

        # 実行用のURLを生成
        execution_url = f"{base_url}/api/run/{script_id}"
        
        return jsonify({
            'message': 'File uploaded and script created successfully!',
            'script_id': script_id,
            'execution_url': execution_url
        }), 201

    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500
    finally:
        # 処理が成功しても失敗しても、必ずデータベース接続を閉じる
        if conn:
            conn.close()


# エンドポイント2: 保存されたコードを実行
@app.route('/api/run/<string:script_id>', methods=['GET'])
def run_saved_code(script_id):
    conn = None
    try:
        # データベースに接続
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # IDに基づいてPostgresからコードを取得
        cursor.execute("SELECT code FROM scripts WHERE id = %s", (script_id,))
        result = cursor.fetchone() # 結果を1行取得
        
        cursor.close()

        if not result:
            return jsonify({'error': 'Script with the given ID not found'}), 404
            
        code_to_run = result[0]

        # --- 以下は以前のコードと同じ実行ロジック ---
        process = subprocess.run(
            [sys.executable, '-c', code_to_run],
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

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Execution timed out (10 seconds limit)'}), 408
        
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

