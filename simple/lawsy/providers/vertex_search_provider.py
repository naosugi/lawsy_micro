"""
Vertex AI Searchを使用したドキュメント検索プロバイダ
"""
from typing import List, Dict, Any, Optional

from lawsy.interfaces.document_search import DocumentSearchProvider
from lawsy.interfaces.search import SearchResult
from lawsy.config import Config


class VertexAISearchProvider(DocumentSearchProvider):
    """Vertex AI Searchを使用したドキュメント検索プロバイダ"""
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        data_store_id: Optional[str] = None
    ):
        """
        初期化
        
        Args:
            project_id: GCPプロジェクトID
            location: Vertex AI Searchのロケーション (例: us-central1)
            data_store_id: データストアID
        """
        self.project_id = project_id or Config.get_required("VERTEX_PROJECT_ID")
        self.location = location or Config.get("VERTEX_LOCATION", "us-central1")
        self.data_store_id = data_store_id or Config.get_required("VERTEX_DATA_STORE_ID")
        
        # 検索クライアント
        self._client = None
    
    def _get_client(self):
        """Vertex AI Searchクライアントを遅延初期化"""
        if self._client is None:
            try:
                from google.cloud import discoveryengine_v1 as discoveryengine
                
                # クライアント初期化
                self._client = discoveryengine.SearchServiceClient()
                
                # 検索のためのリソース名を構築
                self._serving_config = self._client.serving_config_path(
                    project=self.project_id,
                    location=self.location,
                    data_store=self.data_store_id,
                    serving_config="default_config"
                )
            except ImportError:
                raise ImportError("google-cloud-discoveryengine がインストールされていません")
        
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
        
        try:
            from google.cloud import discoveryengine_v1 as discoveryengine
            
            # フィルター文字列を構築
            filter_str = ""
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, list):
                        or_conditions = [f"{key}=\"{v}\"" for v in value]
                        conditions.append(f"({' OR '.join(or_conditions)})")
                    else:
                        conditions.append(f"{key}=\"{value}\"")
                
                if conditions:
                    filter_str = " AND ".join(conditions)
            
            # 検索リクエスト構築
            request = discoveryengine.SearchRequest(
                serving_config=self._serving_config,
                query=query,
                page_size=limit,
                content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                    # ハイブリッド検索（テキスト + ベクトル）
                    search_type=discoveryengine.SearchRequest.ContentSearchSpec.SearchType.HYBRID,
                    # スニペット生成
                    snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                        return_snippet=True
                    )
                )
            )
            
            # フィルターを追加
            if filter_str:
                request.filter = filter_str
            
            # 検索実行
            response = client.search(request)
            
            # 結果を処理
            results = []
            for result in response.results:
                # ドキュメントのメタデータを取得
                document = result.document
                
                # コンテンツを取得（スニペットまたは原文）
                content = ""
                if hasattr(result, "snippet") and result.snippet and result.snippet.content:
                    content = result.snippet.content
                elif hasattr(document, "derived_struct_data"):
                    content = document.derived_struct_data.get("content", "")
                
                # タイトルを取得
                title = ""
                if hasattr(document, "derived_struct_data"):
                    title = document.derived_struct_data.get("title", "")
                
                # URLを取得
                url = ""
                if hasattr(document, "derived_struct_data"):
                    url = document.derived_struct_data.get("url", "")
                
                # メタデータを構築
                metadata = {}
                if hasattr(document, "derived_struct_data"):
                    metadata = dict(document.derived_struct_data)
                
                # 結果を追加
                results.append(SearchResult(
                    title=title,
                    content=content,
                    url=url,
                    score=result.relevant_score if hasattr(result, "relevant_score") else 0.0,
                    metadata=metadata
                ))
            
            return results
            
        except Exception as e:
            # エラーログ
            print(f"Vertex AI Search Error: {str(e)}")
            return []