"""
エンベディングインターフェース
異なるエンベディングプロバイダに対する抽象化レイヤー
"""
from abc import ABC, abstractmethod
from typing import List, Any

class EmbeddingProvider(ABC):
    """エンベディングプロバイダのインターフェース"""
    
    @abstractmethod
    def get_dimension(self) -> int:
        """エンベディングの次元数を返す"""
        pass
    
    @abstractmethod
    def get_embedding(self, texts: List[str]) -> List[List[float]]:
        """
        テキストのエンベディングを取得する
        
        Args:
            texts: エンベディングを取得するテキストのリスト
            
        Returns:
            テキストのエンベディング（リストのリスト）
        """
        pass