from flask import Flask, request, jsonify
import subprocess
import sys
import uuid
import os
import psycopg2

# --- Vercel Postgres への接続 ---
DATABASE_URL = os.environ.get('POSTGRS_URL') # Vercelが自動で設定
# --- 接続設定ここまで ---


# Flaskアプリケーションを初期化
app = Flask(__name__)


# エンドポイント1: ファイルをアップロードして実行URLを生成 (変更なし)
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


# エンドポイント2: 保存されたコードを実行 (★ ここからが変更点 ★)
@app.route('/api/run/<string:script_id>', methods=['GET', 'POST']) # POSTも受け付けるように
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

        # --- ★ 引数を取得するロジック ---
        # GETリクエストの場合はクエリパラメータから、POSTリクエストの場合はJSONボディから引数を取得
        if request.method == 'GET':
            # URLの ?args=... から引数をリストとして取得
            args = request.args.getlist('args')
        elif request.method == 'POST':
            # リクエストボディのJSONから 'args' をリストとして取得
            post_data = request.get_json()
            args = post_data.get('args', []) if post_data else []
        else:
            args = []
        # --- 引数取得ロジックここまで ---


        # 実行するコマンドを組み立てる
        # [ "python", "-c", "スクリプトコード", "引数1", "引数2", ... ]
        command = [sys.executable, '-c', code_to_run] + args

        process = subprocess.run(
            command, # ★ 変更点: 引数を含むコマンドを実行
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
# ```

# ### 変更のポイント
# 1.  **引数の受け取り:**
#     * `/api/run/...` のエンドポイントが `GET` と `POST` の両方のリクエストを受け付けるようにしました。
#     * **GET** の場合: `request.args.getlist('args')` を使って、URLの末尾の `?args=...&args=...` から引数をリストとして取得します。
#     * **POST** の場合: `request.get_json()` を使って、リクエストのボディに含まれるJSONから引数のリストを取得します。
# 2.  **コマンドの組み立て:**
#     * `subprocess.run` に渡すコマンドを `[sys.executable, '-c', code_to_run] + args` のように変更しました。これにより、取得した引数がPythonスクリプトに渡されます。

# ---

# ### 新しいテスト方法

# **1. 引数を受け取る`test.py`を作成**
#    あなたのPythonスクリプト側で、渡された引数を受け取るには `sys.argv` を使います。
#    以下のような新しい`test.py`を作成してください。

#    **`test.py` の中身:**
#    ```python
#    import sys

#    print("--- Script Start ---")
#    print(f"Received {len(sys.argv) - 1} argument(s).")
   
#    # sys.argv[0] はスクリプト名(-c)なので、[1]からが引数
#    for i, arg in enumerate(sys.argv[1:]):
#        print(f"Argument {i+1}: {arg}")

#    print("--- Script End ---")
#    ```

# **2. 新しい`test.py`をアップロード**
#    まず、この新しいスクリプトをアップロードして、実行URLを取得します。

#    ```bash
#    # (test.pyがあるフォルダで実行)
#    curl -X POST -F "file=@test.py" https://megarunner.vercel.app/api/upload
#    ```
#    (返ってきた`execution_url`をコピーしておきます)

# **3. 引数を渡して実行！ (GETの場合)**
#    コピーしたURLの末尾に `?args=...` を付けて実行します。

#    ```bash
#    # URLの '...' の部分は、あなたが受け取ったIDに置き換えてください
#    curl "https://megarunner.vercel.app/api/run/...?args=Hello&args=Vercel&args=API"
#    ```
#    *(注意: `&` がターミナルで特別な意味を持つことがあるので、URL全体をダブルクォーテーション `"` で囲むのが安全です)*

# **期待される結果:**
# ```json
# {
#   "returncode": 0,
#   "stderr": "",
#   "stdout": "--- Script Start ---\nReceived 3 argument(s).\nArgument 1: Hello\nArgument 2: Vercel\nArgument 3: API\n--- Script End ---\n"
# }

