import sys
import json
import inspect
import io
import contextlib

# ★ 変更点 ★
# executor.py のみが entrypoint の定義を知っていれば良くなった
ENTRYPOINT_BOILERPLATE = """
def entrypoint(func):
    func._is_entrypoint = True
    return func
"""

def run_user_code(user_code_string, request_args_json):
    result = {
        "stdout": "",
        "stderr": "",
        "return_value": None,
        "error": None
    }
    
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    try:
        with contextlib.redirect_stdout(stdout_capture):
            with contextlib.redirect_stderr(stderr_capture):
                
                # ★ 変更点 ★
                # ユーザーコードの先頭に、entrypointの定義を自動的に追加する
                full_code_to_exec = ENTRYPOINT_BOILERPLATE + "\n" + user_code_string
                
                # グローバルスコープを空にして、ユーザーコードを実行
                user_module_globals = {}
                exec(full_code_to_exec, user_module_globals)

                # @entrypoint が付いた関数を探す (ここは以前と同じ)
                entry_func = None
                for obj in user_module_globals.values():
                    if callable(obj) and hasattr(obj, '_is_entrypoint'):
                        entry_func = obj
                        break
                
                if not entry_func:
                    raise ValueError("No function decorated with @entrypoint found.")

                sig = inspect.signature(entry_func)
                func_params = sig.parameters
                request_args = json.loads(request_args_json)
                kwargs_to_pass = {}

                for param_name, param in func_params.items():
                    if param_name in request_args:
                        kwargs_to_pass[param_name] = request_args[param_name]
                    elif param.default is inspect.Parameter.empty:
                        raise TypeError(f"Missing required argument: '{param_name}'")
                
                return_value = entry_func(**kwargs_to_pass)
                result["return_value"] = return_value

    except Exception as e:
        print(f"Execution Engine Error: {e}", file=sys.stderr)
        result["error"] = str(e)
    
    finally:
        result["stdout"] = stdout_capture.getvalue()
        result["stderr"] = stderr_capture.getvalue()

    return result

if __name__ == "__main__":
    # subprocessから標準入力経由でデータを受け取る
    # 1行目: ユーザーコード (Base64エンコード)
    # 2行目: 引数JSON
    user_code_b64 = sys.stdin.readline().strip()
    request_args_json = sys.stdin.readline().strip()
    
    import base64
    user_code = base64.b64decode(user_code_b64).decode('utf-8')
    
    execution_result = run_user_code(user_code, request_args_json)
    print(json.dumps(execution_result))

