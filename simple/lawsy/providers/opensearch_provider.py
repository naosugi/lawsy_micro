"""
OpenSearchを使用したドキュメント検索プロバイダ
"""
from typing import List, Dict, Any, Optional

from lawsy.interfaces.document_search import DocumentSearchProvider
from lawsy.interfaces.search import SearchResult
from lawsy.interfaces.embedding import EmbeddingProvider
from lawsy.config import Config


class OpenSearchProvider(DocumentSearchProvider):
    """OpenSearchを使用したドキュメント検索プロバイダ"""
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        index: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        auth_type: str = "basic",
        embedding_provider: Optional[EmbeddingProvider] = None
    ):
        """
        初期化
        
        Args:
            endpoint: OpenSearchエンドポイント
            index: インデックス名
            username: ユーザー名 (Basic認証の場合)
            password: パスワード (Basic認証の場合)
            auth_type: 認証タイプ ("basic", "iam", "none")
            embedding_provider: クエリをベクトル化するためのエンベディングプロバイダ
        """
        self.endpoint = endpoint or Config.get_required("OPENSEARCH_ENDPOINT")
        self.index = index or Config.get("OPENSEARCH_INDEX", "law_documents")
        self.auth_type = auth_type or Config.get("OPENSEARCH_AUTH_TYPE", "basic")
        
        if self.auth_type == "basic":
            self.username = username or Config.get_required("OPENSEARCH_USERNAME")
            self.password = password or Config.get_required("OPENSEARCH_PASSWORD")
        
        self.embedding_provider = embedding_provider
        
        # OpenSearchクライアント
        self._client = None
    
    def _get_client(self):
        """OpenSearchクライアントを遅延初期化"""
        if self._client is None:
            try:
                from opensearchpy import OpenSearch, RequestsHttpConnection
                
                # 認証設定
                auth = None
                connection_class = RequestsHttpConnection
                
                if self.auth_type == "basic":
                    auth = (self.username, self.password)
                elif self.auth_type == "iam":
                    try:
                        from opensearchpy.helpers.aws import AWS4Auth
                        import boto3
                        
                        # AWSのリージョンを抽出
                        region = self.endpoint.split(".")[1]
                        
                        # IAM認証を設定
                        service = "es"
                        credentials = boto3.Session().get_credentials()
                        auth = AWS4Auth(
                            credentials.access_key,
                            credentials.secret_key,
                            region,
                            service,
                            session_token=credentials.token
                        )
                    except ImportError:
                        raise ImportError("AWS IAM認証を使用するには boto3 がインストールされている必要があります")
                
                # OpenSearchクライアントを初期化
                self._client = OpenSearch(
                    hosts=[self.endpoint],
                    http_auth=auth,
                    connection_class=connection_class,
                    use_ssl=True,
                    verify_certs=True
                )
            except ImportError:
                raise ImportError("opensearch-py がインストールされていません")
        
        return self._client
    
    def search(
        self, 
        query: str, 
        limit: int = 10, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        ドキュメント検索を実行する
        
        Args:
            query: 検索クエリ
            limit: 返す結果の最大数
            filters: 検索フィルター
            
        Returns:
            検索結果のリスト
        """
        client = self._get_client()
        
        # 検索クエリを構築
        search_query = {
            "size": limit,
            "query": {
                "bool": {
                    "must": []
                }
            }
        }
        
        # テキスト検索クエリを追加
        search_query["query"]["bool"]["must"].append({
            "multi_match": {
                "query": query,
                "fields": ["title^2", "content"]
            }
        })
        
        # エンベディングを使用したベクトル検索（エンベディングプロバイダが設定されている場合）
        if self.embedding_provider:
            embedding = self.embedding_provider.get_embeddings([query])[0]
            
            # kNN検索を追加
            search_query["query"]["bool"]["must"].append({
                "knn": {
                    "embedding": {
                        "vector": embedding,
                        "k": limit
                    }
                }
            })
        
        # フィルターを追加
        if filters:
            filter_clauses = []
            for key, value in filters.items():
                if isinstance(value, list):
                    filter_clauses.append({"terms": {key: value}})
                else:
                    filter_clauses.append({"term": {key: value}})
            
            if filter_clauses:
                search_query["query"]["bool"]["filter"] = filter_clauses
        
        # 検索実行
        response = client.search(
            body=search_query,
            index=self.index
        )
        
        # 結果を処理
        results = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            results.append(SearchResult(
                title=source.get("title", ""),
                content=source.get("content", ""),
                url=source.get("url", ""),
                score=hit["_score"],
                metadata=source
            ))
        
        return results