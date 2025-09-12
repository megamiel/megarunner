from flask import Flask, request, jsonify
import subprocess
import sys
import uuid
import os
import psycopg2
import json

# --- Vercel Postgres への接続 ---
DATABASE_URL = os.environ.get('POSTGRES_URL')
# --- 接続設定ここまで ---

# Flaskアプリケーションを初期化
app = Flask(__name__)


# エンドポイント1: スクリプトをアップロード（デプロイ）する
@app.route('/api/upload', methods=['POST'])
def upload_and_save_code():
    # ファイルがリクエストに含まれているかチェック
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    uploaded_file = request.files['file']
    
    # ファイル名が空でないか、.pyで終わるかチェック
    if uploaded_file.filename == '' or not uploaded_file.filename.endswith('.py'):
        return jsonify({'error': 'Please upload a valid .py file'}), 400

    conn = None
    try:
        # ファイルの内容を読み取り、ユニークIDを生成
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

        # 常に本番のURLをベースにする
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
        # 処理が成功しても失敗しても、必ずデータベース接続を閉じる
        if conn:
            conn.close()


# エンドポイント2: 保存されたスクリプトを実行する
@app.route('/api/run/<string:script_id>', methods=['GET', 'POST'])
def run_saved_code(script_id):
    conn = None
    try:
        # データベースに接続し、IDに基づいてコードを取得
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT code FROM scripts WHERE id = %s", (script_id,))
        result = cursor.fetchone()
        cursor.close()

        if not result:
            return jsonify({'error': 'Script with the given ID not found'}), 404
            
        code_to_run = result[0]

        # GET/POSTリクエストから引数データを辞書として取得
        request_data = {}
        if request.method == 'GET':
            request_data = request.args.to_dict()
        elif request.method == 'POST':
            # silent=TrueでJSONでないリクエストでもエラーにならないようにする
            request_data = request.get_json(silent=True) or {}
        
        # 辞書をJSON文字列に変換
        args_as_json_string = json.dumps(request_data)

        # 実行エンジン `executor.py` を呼び出し、
        # ユーザーコードと引数JSONを標準入力で渡す
        process = subprocess.run(
            [sys.executable, 'executor.py'],
            input=f"{code_to_run}\n{args_as_json_string}", # 2行の文字列として渡す
            capture_output=True,
            text=True,
            timeout=10,
            check=False
        )

        # executor.py から返ってきたJSON形式の実行結果をパースする
        try:
            # executor.pyが正常終了した場合、stdoutはJSON文字列のはず
            final_result = json.loads(process.stdout)
            return jsonify(final_result)
        except json.JSONDecodeError:
            # executor.py自体でエラーが起きた場合（JSONを返せなかった場合）
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

