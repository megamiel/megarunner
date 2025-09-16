import sys
import requests
import json
import os

# APIのエンドポイント
UPLOAD_URL = "http://127.0.0.1:5000/api/upload"

def upload_script(file_path):
    """指定されたPythonスクリプトをAPIにアップロードする"""
    if not os.path.exists(file_path):
        print(f"エラー: ファイルが見つかりません: {file_path}")
        return

    # 'rb'モード（バイナリ読み込み）でファイルを開く
    with open(file_path, 'rb') as f:
        # multipart/form-data形式で送信するためのデータを作成
        files = {'file': (os.path.basename(file_path), f, 'text/x-python')}
        
        print(f"'{file_path}' をアップロード中...")
        try:
            response = requests.post(UPLOAD_URL, files=files)
            # 2xx以外のステータスコードで例外を発生させる
            response.raise_for_status() 
            
            # 結果をきれいに表示
            print("\n--- アップロード成功！ ---")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))

        except requests.exceptions.RequestException as e:
            print(f"\n--- エラー ---")
            print(f"APIへの接続に失敗しました: {e}")
        except json.JSONDecodeError:
            print("\n--- エラー ---")
            print("APIからのレスポンスがJSON形式ではありませんでした。")
            print("サーバーのログを確認してください。")
            print(f"レスポンス内容:\n{response.text}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python upload.py <ファイルパス>")
        sys.exit(1)
    
    script_path = sys.argv[1]
    upload_script(script_path)
