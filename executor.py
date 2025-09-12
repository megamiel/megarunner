import sys
import json
import inspect
import io
import contextlib

# ユーザーが使うためのデコレータ。単なるマーカーとして機能します。
def entrypoint(func):
    func._is_entrypoint = True
    return func

def run_user_code(user_code_string, request_args_json):
    """
    ユーザーコードを動的にロードし、@entrypointが付いた関数を探して実行する。
    """
    # 実行結果を格納する辞書
    result = {
        "stdout": "",
        "stderr": "",
        "return_value": None,
        "error": None
    }
    
    # 標準出力とエラー出力をキャプチャする
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    try:
        with contextlib.redirect_stdout(stdout_capture):
            with contextlib.redirect_stderr(stderr_capture):
                
                # ユーザーコードを一時的なモジュールとして実行
                user_module_globals = {"entrypoint": entrypoint}
                exec(user_code_string, user_module_globals)

                # @entrypoint が付いた関数を探す
                entry_func = None
                for obj in user_module_globals.values():
                    if callable(obj) and hasattr(obj, '_is_entrypoint'):
                        entry_func = obj
                        break
                
                if not entry_func:
                    raise ValueError("No function decorated with @entrypoint found.")

                # 関数のシグネチャ（引数情報）を解析
                sig = inspect.signature(entry_func)
                func_params = sig.parameters

                # リクエスト引数を辞書に変換
                request_args = json.loads(request_args_json)

                # 関数に渡すための引数（kwargs）を組み立てる
                kwargs_to_pass = {}
                for param_name, param in func_params.items():
                    if param_name in request_args:
                        kwargs_to_pass[param_name] = request_args[param_name]
                    elif param.default is inspect.Parameter.empty:
                        # デフォルト値がなく、リクエストにも引数がない場合はエラー
                        raise TypeError(f"Missing required argument: '{param_name}'")
                
                # 関数を実行し、戻り値を取得
                return_value = entry_func(**kwargs_to_pass)
                result["return_value"] = return_value

    except Exception as e:
        # 実行時エラーをキャプチャ
        print(str(e), file=sys.stderr)
        result["error"] = str(e)
    
    finally:
        # キャプチャした出力を結果に格納
        result["stdout"] = stdout_capture.getvalue()
        result["stderr"] = stderr_capture.getvalue()

    return result

if __name__ == "__main__":
    # このスクリプトが直接実行された場合（subprocessから呼ばれる）
    user_code = sys.stdin.readline()
    request_args = sys.stdin.readline()
    
    execution_result = run_user_code(user_code, request_args)
    
    # 最終的な結果をJSONとして標準出力に出力
    print(json.dumps(execution_result))
