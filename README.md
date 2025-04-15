# OCR Document Management System (OCRDB)

OCRDBは、写真やスキャンしたデータ、PDF、スクリーンショットなど様々なデータを管理するサーバーです。OCR処理を行い、検索可能なテキストとして保存します。

## 機能

- 画像のアップロードとOCR処理
- OCR結果の検索（API/Webブラウザ）
- 複数のOCRエンジン対応（Tesseract、EasyOCR、PaddleOCR）
- 画像データ以外にZIP形式のアップロード対応
- 検索結果からテキスト、縮小版画像、オリジナル画像の取得
- アップロード時のタグ付け
- フォルダ構造によるデータ整理
- S3（minio）と内部ストレージの両方に対応

## Docker環境での実行方法

### 前提条件

- Docker
- Docker Compose

### インストールと実行

1. リポジトリをクローン

```bash
git clone https://github.com/cer12u/ocrdb.git
cd ocrdb
```

2. Docker Composeでビルドと実行

```bash
docker-compose up -d
```

3. ブラウザでアクセス

```
http://localhost
```

### 環境変数の設定

`docker-compose.yml`ファイルで以下の環境変数を設定できます：

#### バックエンド

- `STORAGE_TYPE`: ストレージタイプ（`local`または`s3`）
- `STORAGE_PATH`: ローカルストレージのパス
- `DEFAULT_OCR_ENGINE`: デフォルトのOCRエンジン
- `MAX_FILE_SIZE`: 最大ファイルサイズ（バイト）
- `MAX_ZIP_SIZE`: 最大ZIPファイルサイズ（バイト）

S3ストレージを使用する場合は、以下も設定してください：

- `S3_ENDPOINT`: S3エンドポイントURL
- `S3_BUCKET`: S3バケット名
- `S3_ACCESS_KEY`: S3アクセスキー
- `S3_SECRET_KEY`: S3シークレットキー

#### フロントエンド

- `VITE_API_URL`: バックエンドAPIのURL

### ボリューム

- `backend_storage`: ドキュメントとサムネイルを保存するためのボリューム

## 開発環境での実行方法

### バックエンド

```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload
```

### フロントエンド

```bash
cd frontend
npm install
npm run dev
```

## APIエンドポイント

- `GET /api/documents`: ドキュメント一覧の取得
- `POST /api/documents`: ドキュメントのアップロード
- `GET /api/documents/{id}`: 特定のドキュメント情報の取得
- `DELETE /api/documents/{id}`: ドキュメントの削除
- `POST /api/documents/{id}/reprocess`: ドキュメントのOCR再処理
- `GET /api/documents/{id}/original`: オリジナルファイルの取得
- `GET /api/documents/{id}/thumbnail`: サムネイルの取得
- `GET /api/search`: ドキュメントの検索
- `GET /api/system/storage`: ストレージ情報の取得
- `GET /api/system/ocr-engines`: 利用可能なOCRエンジンの取得

## 注意事項

- 現在の実装では、大きなファイルのアップロードは同期処理で行われます
- 検索はインデックス最適化されていますが、キャッシュは実装されていません
- OCR精度向上のためのフィルタは実装されていません
- 多言語対応は実装されていません
