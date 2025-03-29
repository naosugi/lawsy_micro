"""
Google検索プロバイダ
"""
import os
from typing import List, Optional, Dict, Any

from lawsy.interfaces.search import SearchProvider, WebSearchResult


class GoogleSearchProvider(SearchProvider):
    """Google Custom Search APIを使用した検索プロバイダ"""
    
    def __init__(
        self,
        cse_key: Optional[str] = None,
        cse_id: Optional[str] = None
    ):
        """
        初期化
        
        Args:
            cse_key: Google Custom Search Engine API キー
            cse_id: Google Custom Search Engine ID
        """
        self.cse_key = cse_key or os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ACCESS_KEY")
        self.cse_id = cse_id or os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")
        
        if not self.cse_key or not self.cse_id:
            raise ValueError(
                "Google Custom Search EngineのAPIキーとIDが必要です。"
                "環境変数GOOGLE_CUSTOM_SEARCH_ENGINE_ACCESS_KEYとGOOGLE_CUSTOM_SEARCH_ENGINE_IDを設定するか、"
                "初期化時に指定してください。"
            )
        
        # クライアントは遅延して初期化
        self._service = None

    def _get_service(self):
        """Google Custom Search APIクライアントを遅延初期化して返す"""
        if self._service is None:
            try:
                from googleapiclient.discovery import build
                self._service = build("customsearch", "v1", developerKey=self.cse_key)
            except ImportError:
                raise ImportError(
                    "google-api-python-client パッケージがインストールされていません。"
                    "pip install google-api-python-client でインストールしてください。"
                )
        return self._service

    def search(
        self, 
        query: str, 
        k: int = 30, 
        language: str = "ja", 
        domains: Optional[List[str]] = None
    ) -> List[WebSearchResult]:
        """
        Google検索を実行する
        
        Args:
            query: 検索クエリ
            k: 返す結果の最大数
            language: 検索結果の言語
            domains: 検索対象のドメイン（指定されている場合）
            
        Returns:
            検索結果のリスト
        """
        # 前処理
        if domains:
            site_query = " OR ".join([f"site:{domain}" for domain in domains])
            query = f"{query} {site_query}"
        
        # 言語パラメータを設定
        lr = f"lang_{language}" if language else None
        
        # 検索実行
        service = self._get_service()
        results = []
        start = 1
        
        # 指定された数の結果を取得するまで繰り返す
        while len(results) < k:
            # API呼び出し
            request = service.cse().list(
                q=query,
                cx=self.cse_id,
                lr=lr,
                num=min(10, k - len(results)),  # 一度に取得する結果数（最大10）
                start=start
            )
            response = request.execute()
            
            # 検索結果がない場合は終了
            if "items" not in response:
                break
            
            # 結果を処理
            for item in response["items"]:
                results.append(
                    WebSearchResult(
                        title=item.get("title", ""),
                        snippet=item.get("snippet", ""),
                        url=item.get("link", ""),
                        meta=item
                    )
                )
            
            # 次のページがなければ終了
            if "nextPage" not in response.get("queries", {}):
                break
            
            # 次のページの開始インデックスを設定
            start = response["queries"]["nextPage"][0]["startIndex"]
        
        return results[:k]