# Lawsyマイクロサービス

法律テキスト検索・分析のためのマイクロサービス。Cloud Functionsでの実行を想定したシンプルな構成です。

## 特徴

- ビジネスロジックのみに特化したPythonマイクロサービス
- 外部API依存を抽象化し、様々なプロバイダへの切り替えが容易
- 単一のCloud Function関数で検索からレポート生成までの一連の処理を実行

## 処理の流れ

### DeepResearch処理フロー

1. **クエリ拡張**
   - 元のクエリから関連サブクエリを生成（例：「労働基準法第19条の解雇予告制度について」）
   - LLMを使用して専門的な関連クエリを複数生成

2. **検索実行**
   - 元のクエリでWeb検索実行（Google検索など）
   - 拡張クエリでWeb検索実行
   - ドキュメント検索実行（OpenSearch/Vertex AI Search/FAISSなど）

3. **検索結果統合**
   - すべての検索結果を結合
   - 重複排除（オプション）

4. **レポート構造化**
   - アウトラインの作成（レポートの章立て）
   - 参照情報の整理

5. **レポート出力**
   - 検索結果とレポートアウトラインをJSON形式で返却

## 外部で必要な処理

Cloud Function内部では処理できない、事前準備や後処理などの外部処理：

### 事前準備

1. **ドキュメントのインデックス作成**
   - 法律文書をチャンク分割
   - エンベディング計算（OpenAI APIなど）
   - インデックス構築（FAISS/OpenSearch/Vertex AI Search）

   ```bash
   # 例：法律文書からFAISSインデックスを作成
   python scripts/create_faiss_index.py --input_dir data/laws --output_dir indices
   ```

2. **外部サービスの設定**
   - OpenSearch: クラスター作成、インデックスマッピング設定
   - Vertex AI Search: データストア作成、スキーマ設定
   - Google Search: Custom Search Engine設定

### 後処理

1. **レポート生成**
   - アウトラインからレポートセクション生成（ストリーミング処理）
   - 完成レポートの保存

2. **表示・共有**
   - レポートの表示フォーマット処理
   - PDF生成、共有リンク作成など

## インターフェース仕様

### リクエスト形式

```json
{
  "operation": "deep_research",
  "query": "労働基準法における解雇規制",
  "config": {
    "search_provider": "google",
    "document_search_provider": "opensearch",
    "opensearch": {
      "endpoint": "https://your-opensearch-endpoint.com",
      "index": "law_documents"
    },
    "limit": 20,
    "domains": ["courts.go.jp", "cao.go.jp"],
    "language": "ja",
    "use_expanded_queries": true,
    "use_document_search": true
  }
}
```

### レスポンス形式 (deep_research)

```json
{
  "query": "労働基準法における解雇規制",
  "sub_queries": ["労働基準法第19条の解雇予告制度について", "..."],
  "web_results": {
    "original": [{"title": "...", "content": "...", "url": "..."}],
    "expanded": [{"title": "...", "content": "...", "url": "..."}]
  },
  "document_results": [{"title": "...", "content": "...", "score": 0.95}],
  "all_results": [...],
  "outline": {
    "title": "労働基準法における解雇規制",
    "sections": [...],
    "references": [...]
  }
}
```

## 外部検索サービス要件

### OpenSearch

OpenSearchはElasticsearch互換のベクトル検索サービスです。

#### 要件

1. **インデックス設定**:
   - ベクトルフィールド（`embedding`）の定義：1536次元（OpenAI）
   - 日本語解析用のkuromoji設定

2. **ドキュメント形式**:
   ```json
   {
     "title": "労働基準法 第20条",
     "content": "使用者は、労働者を解雇しようとする場合...",
     "url": "https://elaws.e-gov.go.jp/...",
     "embedding": [0.123, 0.456, ...],
     "category": "労働法",
     "law_id": "S22HO049"
   }
   ```

### Vertex AI Search

Vertex AI SearchはGoogleの検索サービスです。

#### 要件

1. **データストア設定**:
   - Enterprise版データストア
   - ベクトル検索有効化

2. **ドキュメントスキーマ**:
   ```json
   {
     "id": "labor_standards_act_article_20",
     "title": "労働基準法 第20条",
     "content": "使用者は、労働者を解雇しようとする場合...",
     "url": "https://elaws.e-gov.go.jp/...",
     "category": "労働法",
     "law_id": "S22HO049"
   }
   ```

## 環境変数設定

```bash
# 共通設定
export SEARCH_PROVIDER=google
export GOOGLE_CUSTOM_SEARCH_ENGINE_ACCESS_KEY=your_key
export GOOGLE_CUSTOM_SEARCH_ENGINE_ID=your_id
export OPENAI_API_KEY=your_key

# OpenSearch設定例
export DOCUMENT_SEARCH_PROVIDER=opensearch
export OPENSEARCH_ENDPOINT=https://your-opensearch.com
export OPENSEARCH_USERNAME=admin
export OPENSEARCH_PASSWORD=password
export OPENSEARCH_INDEX=law_documents

# Vertex AI Search設定例
export DOCUMENT_SEARCH_PROVIDER=vertex_ai_search
export VERTEX_PROJECT_ID=your-gcp-project
export VERTEX_DATA_STORE_ID=your-data-store-id
```