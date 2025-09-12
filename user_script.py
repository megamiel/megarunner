import sys
import json

print("--- User Script Start ---")

# スクリプトに渡された引数（JSON文字列）があるかチェック
if len(sys.argv) > 1:
    try:
        # 最初の引数（JSON文字列）をPythonの辞書に変換します
        request_data = json.loads(sys.argv[1])
        
        print("Received data:")
        
        # 辞書から'name'と'age'を安全に取り出します
        # .get()を使うと、キーが存在しなくてもエラーにならず、デフォルト値を返せます
        name = request_data.get('name', 'Anonymous')
        age = request_data.get('age', 'N/A')
        
        print(f"  Name: {name}")
        print(f"  Age: {age}")
        
        # ループを使って、渡された全てのキーと値を出力します
        print("\nAll received key-value pairs:")
        for key, value in request_data.items():
            print(f"  - {key}: {value}")

    except json.JSONDecodeError:
        print("Error: The provided argument is not a valid JSON string.")
    except Exception as e:
        print(f"An error occurred: {e}")
else:
    print("No data received.")

print("--- User Script End ---")