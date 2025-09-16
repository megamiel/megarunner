# ユーザーは、APIが魔法のように用意してくれる
# db_get と db_set を使って、自分のスクリプト専用のDBを操作できます。

@entrypoint
def counter(increment_by = 1):
    # 'visits'というキーで、訪問回数を取得。データがなければ0から始める
    current_visits = db_get("visits") or 0
    
    # 引数で受け取った分だけ、訪問回数を増やす
    new_visits = current_visits + increment_by
    
    # 新しい訪問回数をDBに保存
    db_set("visits", new_visits)
    
    # 関数の戻り値として、現在の訪問回数を返す
    return f"This function has been executed {new_visits} time(s)."
# ```

# #### テスト手順

# 1.  **デプロイ:** 更新した`app.py`と`executor.py`を`git push`して、Vercelにデプロイします。
# 2.  **アップロード:**
#     ```bash
#     curl -X POST -F "file=@stateful_counter.py" https://megarunner.vercel.app/api/upload
#     ```
# 3.  **実行 (1回目):** 返ってきた実行URLにアクセスします。
#     ```bash
#     curl "https://megarunner.vercel.app/api/run/YOUR_SCRIPT_ID"
#     ```
#     **結果:** `{"return_value": "This function has been executed 1 time(s)."}`

# 4.  **実行 (2回目、引数付き):** もう一度、今度は引数を付けてアクセスします。
#     ```bash
#     curl "https://megarunner.vercel.app/api/run/YOUR_SCRIPT_ID?increment_by=10"
    
