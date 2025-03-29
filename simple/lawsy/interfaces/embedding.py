"""
エンベディングインターフェース
"""
from abc import ABC, abstractmethod
from typing import List


class EmbeddingProvider(ABC):
    """エンベディングプロバイダーのインターフェース"""
    
    @abstractmethod
    def get_dimension(self) -> int:
        """エンベディングの次元数を取得"""
        pass
    
    @abstractmethod
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        テキストのエンベディングを取得
        
        Args:
            texts: エンベディングを取得するテキストのリスト
            
        Returns:
            テキストのエンベディング（リストのリスト）
        """
        pass