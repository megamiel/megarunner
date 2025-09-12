import sys

# 引数が渡されたかチェック
if len(sys.argv) > 1:
    # 渡された引数を名前にして挨拶
    name = sys.argv[1]
    print(f"Hello, {name}! Welcome to your custom API.")
else:
    # 引数がなければ、デフォルトのメッセージ
    print("Hello! Please provide a name as an argument.")

print(f"(This script was executed on the cloud via your Vercel API!)")