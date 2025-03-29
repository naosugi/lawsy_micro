"""
Elasticsearchを使用した法文書検索サービス
Elasticsearchのベクトル検索機能を利用
"""
import os
from typing import List, Dict, Any, Optional

from lawsy.interfaces.document_search import DocumentSearchProvider, DocumentSearchResult
from lawsy.interfaces.embedding import EmbeddingProvider


class ElasticsearchDocumentSearchService(DocumentSearchProvider):
    """
    Elasticsearchを使用した検索サービス
    Elasticsearchのベクトル検索機能を利用
    """
    
    def __init__(
        self, 
        embedding_provider: EmbeddingProvider,
        index_name: str = "law_documents",
        hosts: Optional[List[str]] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        cloud_id: Optional[str] = None
    ):
        """
        初期化
        
        Args:
            embedding_provider: エンベディングプロバイダ（クエリをベクトル化するために使用）
            index_name: Elasticsearchのインデックス名
            hosts: Elasticsearchのホスト
            username: Elasticsearchのユーザー名
            password: Elasticsearchのパスワード
            cloud_id: Elastic CloudのクラウドID
        """
        self.embedding_provider = embedding_provider
        self.index_name = index_name
        
        # Elasticsearch設定
        self.hosts = hosts or os.getenv("ELASTICSEARCH_HOSTS", "http://localhost:9200").split(",")
        self.username = username or os.getenv("ELASTICSEARCH_USERNAME")
        self.password = password or os.getenv("ELASTICSEARCH_PASSWORD")
        self.cloud_id = cloud_id or os.getenv("ELASTICSEARCH_CLOUD_ID")
        
        # Elasticsearchクライアントは遅延して初期化
        self._client = None
    
    def _get_client(self):
        """Elasticsearchクライアントを遅延初期化して返す"""
        if self._client is None:
            try:
                from elasticsearch import Elasticsearch
                
                # 認証情報の設定
                es_config = {}
                
                if self.cloud_id:
                    es_config["cloud_id"] = self.cloud_id
                else:
                    es_config["hosts"] = self.hosts
                    
                if self.username and self.password:
                    es_config["basic_auth"] = (self.username, self.password)
                
                # クライアント初期化
                self._client = Elasticsearch(**es_config)
                
            except ImportError:
                raise ImportError(
                    "elasticsearch パッケージがインストールされていません。"
                    "pip install elasticsearch でインストールしてください。"
                )
        return self._client
    
    def search(
        self,
        query: str,
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[DocumentSearchResult]:
        """
        クエリに一致するドキュメントを検索する
        
        Args:
            query: 検索クエリ
            k: 返す結果の最大数
            filters: メタデータによるフィルター条件
            
        Returns:
            検索結果のリスト
        """
        client = self._get_client()
        
        # クエリをベクトル化
        query_vector = self.embedding_provider.get_embedding([query])[0]
        
        # 検索クエリを構築
        search_query = {
            "size": k,
            "query": {
                "bool": {
                    "must": [
                        # ベクトル検索
                        {
                            "script_score": {
                                "query": {"match_all": {}},
                                "script": {
                                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                                    "params": {"query_vector": query_vector}
                                }
                            }
                        }
                    ]
                }
            }
        }
        
        # フィルターを追加（指定されている場合）
        if filters:
            filter_clauses = []
            for key, value in filters.items():
                filter_clauses.append({"term": {key: value}})
                
            if filter_clauses:
                search_query["query"]["bool"]["filter"] = filter_clauses
        
        # 検索を実行
        response = client.search(
            index=self.index_name,
            body=search_query
        )
        
        # 結果をフォーマット
        results = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            results.append(DocumentSearchResult(
                title=source.get("title", ""),
                content=source.get("content", ""),
                score=hit["_score"],
                metadata=source
            ))
        
        return results
        
    def create_index(self, settings: Optional[Dict[str, Any]] = None, mappings: Optional[Dict[str, Any]] = None):
        """
        Elasticsearchにインデックスを作成する
        
        Args:
            settings: インデックス設定
            mappings: フィールドマッピング
        """
        client = self._get_client()
        
        # デフォルトの設定とマッピング
        default_settings = {
            "analysis": {
                "analyzer": {
                    "kuromoji_analyzer": {
                        "type": "custom",
                        "tokenizer": "kuromoji_tokenizer",
                        "filter": ["kuromoji_baseform", "ja_stop", "kuromoji_number", "lowercase"]
                    }
                }
            }
        }
        
        default_mappings = {
            "properties": {
                "title": {
                    "type": "text",
                    "analyzer": "kuromoji_analyzer"
                },
                "content": {
                    "type": "text",
                    "analyzer": "kuromoji_analyzer"
                },
                "embedding": {
                    "type": "dense_vector",
                    "dims": self.embedding_provider.get_dimension(),
                    "index": True,
                    "similarity": "cosine"
                }
            }
        }
        
        # 設定とマッピングをマージ
        settings = settings or default_settings
        mappings = mappings or default_mappings
        
        # インデックスを作成
        client.indices.create(
            index=self.index_name,
            body={
                "settings": settings,
                "mappings": mappings
            },
            ignore=400  # インデックスが既に存在する場合はエラーを無視
        )
        
    def add_documents(self, documents: List[Dict[str, Any]], generate_embeddings: bool = True):
        """
        ドキュメントをElasticsearchに追加する
        
        Args:
            documents: 追加するドキュメントのリスト
            generate_embeddings: ドキュメントのエンベディングを生成するかどうか
        """
        client = self._get_client()
        
        # バルクリクエスト用のデータを準備
        bulk_data = []
        
        for doc in documents:
            # ドキュメントIDを取得または生成
            doc_id = doc.pop("id", None)
            
            # エンベディングを計算（指定されている場合）
            if generate_embeddings and "embedding" not in doc and "content" in doc:
                doc["embedding"] = self.embedding_provider.get_embedding([doc["content"]])[0]
            
            # インデックス操作を追加
            index_action = {
                "_index": self.index_name,
            }
            
            if doc_id:
                index_action["_id"] = doc_id
                
            bulk_data.append({"index": index_action})
            bulk_data.append(doc)
        
        # バルク操作を実行
        if bulk_data:
            client.bulk(body=bulk_data, refresh=True)