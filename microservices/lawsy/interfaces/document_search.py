"""
法文書検索インターフェース
検索エンジンへのアクセスを抽象化
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class DocumentSearchResult:
    """法文書検索結果を表すデータクラス"""
    
    def __init__(
        self,
        title: str,
        content: str,
        score: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.title = title
        self.content = content
        self.score = score
        self.metadata = metadata or {}

class DocumentSearchProvider(ABC):
    """法文書検索プロバイダのインターフェース"""
    
    @abstractmethod
    def search(
        self,
        query: str,
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[DocumentSearchResult]:
        """
        与えられたクエリで法文書を検索する
        
        Args:
            query: 検索クエリ
            k: 返す結果の最大数
            filters: 検索フィルター（任意）
            
        Returns:
            法文書検索結果のリスト
        """
        pass