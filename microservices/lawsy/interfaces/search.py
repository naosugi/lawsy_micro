"""
検索インターフェース
異なる検索プロバイダに対する抽象化レイヤー
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class WebSearchResult:
    """検索結果を表すデータクラス"""
    
    def __init__(
        self, 
        title: str, 
        snippet: str, 
        url: str, 
        meta: Optional[Dict[str, Any]] = None
    ):
        self.title = title
        self.snippet = snippet
        self.url = url
        self.meta = meta or {}

class SearchProvider(ABC):
    """検索プロバイダのインターフェース"""
    
    @abstractmethod
    def search(
        self, 
        query: str, 
        k: int = 30, 
        language: str = "ja", 
        domains: Optional[List[str]] = None
    ) -> List[WebSearchResult]:
        """
        与えられたクエリで検索を実行する
        
        Args:
            query: 検索クエリ
            k: 返す結果の最大数
            language: 検索結果の言語
            domains: 検索対象のドメイン（指定されている場合）
            
        Returns:
            検索結果のリスト
        """
        pass