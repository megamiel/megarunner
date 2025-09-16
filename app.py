from flask import Flask, request, jsonify
import sys
import uuid
import os
import pg8000.dbapi
import ssl
import json
from dotenv import load_dotenv
from urllib.parse import urlparse
import inspect
import io
import contextlib

# --- 初期設定 ---
load_dotenv('.env.development.local')
DATABASE_URL = os.environ.get('POSTGRES_URL_NON_POOLING')
app = Flask(__name__)

# --- データベース接続ヘルパー ---
def get_db_connection():
    if not DATABASE_URL:
        raise ValueError("データベースの接続URLが環境変数に設定されていません。")
    parsed_url = urlparse(DATABASE_URL)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    db_port = parsed_url.port or 5432
    return pg8000.dbapi.connect(
        user=parsed_url.username, password=parsed_url.password,
        host=parsed_url.hostname, port=db_port,
        database=parsed_url.path[1:], ssl_context=ssl_context
    )

# --- 実行エンジン (executor.pyのロジックを内包) ---
ENTRYPOINT_BOILERPLATE = "def entrypoint(func): func._is_entrypoint = True; return func"
class DatabaseConcierge:
    def __init__(self, script_id):
        self.script_id = script_id
    def set(self, key, value):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO user_data (script_id, key, value) VALUES (%s, %s, %s) ON CONFLICT (script_id, key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()", (self.script_id, key, json.dumps(value)))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    def get(self, key):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM user_data WHERE script_id = %s AND key = %s", (self.script_id, key))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] if result else None

def execute_user_script(code_string, request_args, script_id):
    result = {"stdout": "", "stderr": "", "return_value": None, "error": None}
    stdout_capture, stderr_capture = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            full_code = f"{ENTRYPOINT_BOILERPLATE}\n{code_string}"
            scope = {}
            exec(full_code, scope)
            entry_func = next((obj for obj in scope.values() if callable(obj) and hasattr(obj, '_is_entrypoint')), None)
            if not entry_func: raise ValueError("No @entrypoint function found.")
            
            db_concierge = DatabaseConcierge(script_id)
            entry_func.__globals__["db_set"] = db_concierge.set
            entry_func.__globals__["db_get"] = db_concierge.get

            sig = inspect.signature(entry_func)
            kwargs_to_pass = {}

            # --- ★★★ ここからが、型を自動変換する魔法の部分です ★★★ ---
            for param in sig.parameters.values():
                param_name = param.name
                if param_name in request_args:
                    value = request_args[param_name]
                    # 型ヒントが存在すれば、それに基づいて型変換を試みる
                    if param.annotation is not inspect.Parameter.empty:
                        try:
                            # bool型のための特別な処理
                            if param.annotation is bool:
                                if isinstance(value, str) and value.lower() in ['true', '1', 'yes']:
                                    value = True
                                elif isinstance(value, str) and value.lower() in ['false', '0', 'no']:
                                    value = False
                                else:
                                    value = bool(value)
                            else:
                                # int, float, str など、他の型に変換
                                value = param.annotation(value)
                        except (ValueError, TypeError):
                            raise TypeError(f"Argument '{param_name}' could not be converted to the required type '{param.annotation.__name__}'. Received value: '{value}'")
                    kwargs_to_pass[param_name] = value
                elif param.default is inspect.Parameter.empty:
                    raise TypeError(f"Missing required argument: '{param_name}'")
            # --- ★★★ 魔法ここまで ★★★ ---
            
            result["return_value"] = entry_func(**kwargs_to_pass)

    except Exception as e:
        print(f"Execution Error: {e}", file=sys.stderr)
        result["error"] = str(e)
    finally:
        result["stdout"] = stdout_capture.getvalue()
        result["stderr"] = stderr_capture.getvalue()
    return result

# --- APIエンドポイント ---
@app.route('/api/upload', methods=['POST'])
def upload_code():
    if 'file' not in request.files: return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if not file.filename.endswith('.py'): return jsonify({'error': 'Invalid file type'}), 400
    code, script_id = file.read().decode('utf-8'), str(uuid.uuid4())
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO scripts (id, code) VALUES (%s, %s)", (script_id, code))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e: return jsonify({'error': f'Database error: {str(e)}'}), 500
    return jsonify({'message': 'Script uploaded!', 'script_id': script_id, 'execution_url': f"https://megarunner.vercel.app/api/run/{script_id}"}), 201

@app.route('/api/run/<string:script_id>', methods=['GET', 'POST'])
def run_code(script_id):
    code_to_run = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT code FROM scripts WHERE id = %s", (script_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result: code_to_run = result[0]
    except Exception as e: return jsonify({'error': f'Database error: {str(e)}'}), 500
    if not code_to_run: return jsonify({'error': 'Script not found'}), 404
    
    args = request.args.to_dict() if request.method == 'GET' else (request.get_json(silent=True) or {})
    
    final_result = execute_user_script(code_to_run, args, script_id)
    return jsonify(final_result)

if __name__ == "__main__":
    app.run(debug=True)
# ```

# ---

# ### 次のステップ：最後のテスト

# 1.  **新しいユーザーファイルを作成:**
#     `type_hinted_counter.py` という名前で、ユーザーが書くべき、型ヒント付きの新しいスクリプトを作成します。

#     ```python
#     @entrypoint
#     def counter(increment_by: int = 1):
#         current_visits = db_get("visits") or 0
#         # ★ ここで int() を書く必要は、もうありません！
#         new_visits = current_visits + increment_by
#         db_set("visits", new_visits)
#         return f"This function has been executed {new_visits} time(s)."
#     ```

# 2.  **ローカルサーバーを再起動:**
#     `.\venv\Scripts\python.exe app.py` で、更新した`app.py`を起動します。

# 3.  **アップロード:**
#     ```bash
#     python upload.py type_hinted_counter.py
#     ```

# 4.  **実行:** `upload.py`で返ってきたIDを使って、**正しい使い方**で`run.py`を実行します。
#     ```bash
#     python run.py YOUR_SCRIPT_ID increment_by=1000
#     ```

# **期待される結果:**
# 今度こそ、`run.py`は引数を正しくAPIに渡し、APIは`"1000"`という文字列を`1000`という**整数**に自動変換して実行するため、エラーは一切出ずに、完璧な結果が返ってきます！

# ```json
# {
#   "return_value": "This function has been executed 1001 time(s)."
# }

