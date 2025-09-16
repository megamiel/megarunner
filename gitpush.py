import subprocess
import random
import string
import sys

def generate_random_string(length=8):
    """指定された長さのランダムな英数字の文字列を生成する"""
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(length))

def run_command(command):
    """シェルコマンドを実行し、その出力を表示する"""
    print(f"\n> 実行中: {' '.join(command)}")
    try:
        # コマンドを実行し、エラーがあれば例外を発生させる (check=True)
        result = subprocess.run(
            command, 
            check=True, 
            capture_output=True, 
            text=True, 
            encoding='utf-8',
            errors='replace' # 文字コードエラーを無視
        )
        print("--- 成功 ---")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return True
    except FileNotFoundError:
        print(f"エラー: コマンドが見つかりません: '{command[0]}'")
        print("Gitがインストールされ、PATHが通っているか確認してください。")
        return False
    except subprocess.CalledProcessError as e:
        print("--- エラー ---")
        # 何もコミットするものがない場合のエラーは、無視して成功とみなす
        if "nothing to commit, working tree clean" in e.stdout:
            print("コミットする新しい変更はありませんでした。")
            return True # 次のステップに進むためにTrueを返す
        
        print(f"コマンド '{' '.join(command)}' の実行に失敗しました。")
        print(f"リターンコード: {e.returncode}")
        if e.stdout:
            print(f"Stdout:\n{e.stdout}")
        if e.stderr:
            print(f"Stderr:\n{e.stderr}")
        return False

def git_deploy():
    """git add, commit, pushのプロセスを自動化する"""
    
    # 1. git add .
    if not run_command(["git", "add", "."]):
        return

    # 2. git commit -m "{ランダム生成}"
    commit_message = f"Auto-commit: {generate_random_string()}"
    if not run_command(["git", "commit", "-m", commit_message]):
        # 'nothing to commit' の場合はrun_commandがTrueを返すので、
        # ここで処理が止まるのは、それ以外のコミットエラーの場合
        print("\nコミットに失敗したため、プッシュを中止しました。")
        return
        
    # 3. git push origin master
    if not run_command(["git", "push", "origin", "master"]):
        return
        
    print("\n✅ デプロイプロセスが正常に完了しました！")
    print("Vercelのダッシュボードでデプロイの進捗を確認してください。")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "master":
        print("Gitデプロイプロセスを開始します...")
        git_deploy()
    else:
        print("使い方: python deploy.py master")
        print("警告: このコマンドは 'master' ブランチに直接プッシュします。")
