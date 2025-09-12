import sys

print("--- Script Start ---")
# sys.argv[0] はスクリプト名(-c)なので、[1:]で引数だけを取得
arguments = sys.argv[1:]
print(f"Received {len(arguments)} argument(s).")

for i, arg in enumerate(arguments):
    print(f"Argument {i+1}: {arg}")

print("--- Script End ---")