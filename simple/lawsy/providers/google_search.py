"""
Google検索プロバイダ
"""
from typing import List, Dict, Any, Optional

from lawsy.interfaces.search import SearchProvider, SearchResult
from lawsy.config import Config


class GoogleSearchProvider(SearchProvider):
    """Google Custom Search APIを使用した検索プロバイダ"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        cse_id: Optional[str] = None
    ):
        """
        初期化
        
        Args:
            api_key: Google Custom Search API Key
            cse_id: Google Custom Search Engine ID
        """
        self.api_key = api_key or Config.get_required("GOOGLE_CUSTOM_SEARCH_ENGINE_ACCESS_KEY")
        self.cse_id = cse_id or Config.get_required("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")
        
        # Google APIクライアント
        self._service = None
    
    def _get_service(self):
        """Google APIクライアントを遅延初期化"""
        if self._service is None:
            from googleapiclient.discovery import build
            self._service = build("customsearch", "v1", developerKey=self.api_key)
        return self._service
    
    def search(
        self, 
        query: str, 
        limit: int = 10, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        検索を実行する
        
        Args:
            query: 検索クエリ
            limit: 返す結果の最大数
            filters: 検索フィルター
                - domains: List[str] - 検索対象ドメイン
                - language: str - 検索言語
            
        Returns:
            検索結果のリスト
        """
        # フィルターからパラメータを抽出
        filters = filters or {}
        domains = filters.get("domains", [])
        language = filters.get("language", "ja")
        
        # ドメイン指定がある場合、クエリに追加
        if domains:
            domain_query = " OR ".join([f"site:{domain}" for domain in domains])
            query = f"{query} {domain_query}"
        
        # 言語設定
        lr = f"lang_{language}" if language else None
        
        # Google APIを使用して検索実行
        service = self._get_service()
        results = []
        start_index = 1
        
        # 指定された数の結果を取得するまで繰り返す
        while len(results) < limit:
            request = service.cse().list(
                q=query,
                cx=self.cse_id,
                lr=lr,
                num=min(10, limit - len(results)),
                start=start_index
            )
            response = request.execute()
            
            # 検索結果がない場合は終了
            if "items" not in response:
                break
            
            # 結果を処理
            for item in response["items"]:
                results.append(SearchResult(
                    title=item.get("title", ""),
                    content=item.get("snippet", ""),
                    url=item.get("link", ""),
                    metadata=item
                ))
            
            # 次のページがなければ終了
            if "queries" not in response or "nextPage" not in response["queries"]:
                break
            
            # 次のページのインデックスを取得
            start_index = response["queries"]["nextPage"][0]["startIndex"]
            
            # 十分な結果を得た場合は終了
            if len(results) >= limit:
                break
        
        return results[:limit]