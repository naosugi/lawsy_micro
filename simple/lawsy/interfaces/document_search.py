"""
ドキュメント検索インターフェース
様々な検索バックエンドへの抽象化レイヤー
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from lawsy.interfaces.search import SearchResult


class DocumentSearchProvider(ABC):
    """ドキュメント検索プロバイダーのインターフェース"""
    
    @abstractmethod
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
        pass