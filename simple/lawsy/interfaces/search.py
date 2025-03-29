"""
検索インターフェース
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class SearchResult:
    """検索結果を表すデータクラス"""
    
    def __init__(
        self, 
        title: str, 
        content: str, 
        url: Optional[str] = None,
        score: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.title = title
        self.content = content
        self.url = url
        self.score = score
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "title": self.title,
            "content": self.content,
            "url": self.url,
            "score": self.score,
            "metadata": self.metadata
        }


class SearchProvider(ABC):
    """検索プロバイダーのインターフェース"""
    
    @abstractmethod
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
            
        Returns:
            検索結果のリスト
        """
        pass