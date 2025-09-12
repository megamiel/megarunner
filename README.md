# Python APIセットアップガイド (Vercel Postgres版)

このAPIは、アップロードされたPythonコードをVercel Postgresに保存し、ユニークな実行URLを生成します。

## 1. Vercel Postgresのセットアップ

1.  **Vercelダッシュボードにアクセス:** あなたのVercelプロジェクト (`megarunner`) のダッシュボードを開きます。
2.  **ストレージタブに移動:** 上部にある「Storage」タブをクリックします。
3.  **Postgresデータベースの作成:**
    * 「Create New」ドロップダウンから「Postgres」を選択します。
    * データベース名（例: `megarunner-db`）とリージョン（例: `Japan (Tokyo)`）を選択し、「Create」をクリックします。
4.  **接続:**
    * 作成が完了すると、接続画面が表示されます。「Accept and Connect」をクリックします。
    * **重要:** Vercelは、接続に必要なすべての環境変数 (`POSTGRES_URL`など) を、あなたのVercelプロジェクトに**自動的に設定してくれます**。手動でキーをコピー＆ペーストする必要は一切ありません。

## 2. データベーステーブルの作成

データベースは作成されましたが、まだ空の状態です。コードを保存するためのテーブルを作成する必要があります。

1.  **Vercelのクエリエディタを開く:**
    * データベースの管理画面で、「Query」タブをクリックします。
2.  **SQLコマンドを実行:**
    * 表示されたテキストエリアに、以下のSQLコマンドをコピー＆ペーストします。
    ```sql
    CREATE TABLE scripts (
        id UUID PRIMARY KEY,
        code TEXT NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    ```
    * 「Run」ボタンを押して、テーブルを作成します。

## 3. デプロイ

1.  ローカルの`app.py`と`requirements.txt`ファイルを、このガイドに記載されている新しい内容で更新します。
2.  変更をGitHubにプッシュします。
3.  Vercelは変更を検知し、自動的に再デプロイを開始します。Vercelが環境変数を自動設定してくれているため、デプロイは成功するはずです。

## 4. APIのテスト方法

デプロイが完了したら、以前と同じ`curl`コマンドでテストできます。

* **アップロード:**
    ```bash
    curl -X POST -F "file=@/path/to/your/test.py" [https://megarunner.vercel.app/api/upload](https://megarunner.vercel.app/api/upload)
    ```

* **実行:**
    アップロード後に返ってきた`execution_url`にアクセスします。
    ```bash
    curl [https://megarunner.vercel.app/api/run/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx](https://megarunner.vercel.app/api/run/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
    ```