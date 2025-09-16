import sys
import requests
import json

# APIのベースURL
BASE_URL = "http://127.0.0.1:5000/api/run/"

def run_script(script_id, args):
    """指定されたscript_idのスクリプトを、名前付き引数を渡して実行する"""
    
    # 実行用のURLを作成
    run_url = BASE_URL + script_id
    
    # コマンドライン引数を辞書に変換
    params = {}
    for arg in args:
        if '=' not in arg:
            print(f"エラー: 引数の形式が正しくありません: '{arg}'。'key=value'形式で指定してください。")
            return
        key, value = arg.split('=', 1)
        params[key] = value

    print(f"ID '{script_id}' を実行中...")
    print(f"引数: {params}")

    try:
        # GETリクエストでクエリパラメータとして引数を渡す
        response = requests.get(run_url, params=params)
        # 2xx以外のステータスコードで例外を発生させる
        response.raise_for_status() 

        print("\n--- 実行成功！ ---")
        # 結果をきれいに表示
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))

    except requests.exceptions.RequestException as e:
        print(f"\n--- エラー ---")
        # サーバーからのエラーレスポンスがあれば、それも表示する
        if e.response:
            print(f"ステータスコード: {e.response.status_code}")
            try:
                print("エラー内容:")
                print(json.dumps(e.response.json(), indent=2, ensure_ascii=False))
            except json.JSONDecodeError:
                print(f"レスポンス内容:\n{e.response.text}")
        else:
            print(f"APIへの接続に失敗しました: {e}")

    except json.JSONDecodeError:
        print("\n--- エラー ---")
        print("APIからのレスポンスがJSON形式ではありませんでした。")
        print("サーバーのログを確認してください。")
        print(f"レスポンス内容:\n{response.text}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python run.py <script_id> [key1=value1] [key2=value2] ...")
        sys.exit(1)
        
    target_script_id = sys.argv[1]
    script_args = sys.argv[2:] # 2番目以降の引数を取得
    
    run_script(target_script_id, script_args)
# ```

# ### 新しい`run.py`の使い方

# 1.  **サーバーを起動する:**
#     まず、`.\venv\Scripts\python.exe app.py`コマンドで、あなたのローカルサーバーが起動していることを確認してください。

# 2.  **スクリプトをアップロードする:**
#     `upload.py`を使って、テストしたいスクリプト（例: `my_simple_function.py`）をアップロードし、`script_id`を取得します。
#     ```bash
#     python upload.py my_simple_function.py
#     ```

# 3.  **`run.py`で実行する:**
#     取得した`script_id`と、**`キー=値`**の形式で好きな引数を渡して、スクリプトを実行します。
#     ```bash
#     python run.py YOUR_SCRIPT_ID name=megamiel age=25 city=Kyoto
    

