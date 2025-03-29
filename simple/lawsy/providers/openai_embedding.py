"""
OpenAI APIを使用したエンベディングプロバイダ
"""
from typing import List, Optional

from lawsy.interfaces.embedding import EmbeddingProvider
from lawsy.config import Config


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI APIを使用したエンベディングプロバイダ"""
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        dimension: Optional[int] = None
    ):
        """
        初期化
        
        Args:
            model_name: モデル名
            api_key: OpenAI APIキー
            dimension: エンベディング次元数
        """
        self.model_name = model_name or Config.get("OPENAI_EMBEDDING_MODEL")
        self.api_key = api_key or Config.get_required("OPENAI_API_KEY")
        
        # 次元数の設定
        if dimension is not None:
            self.dimension = dimension
        elif self.model_name == "text-embedding-3-large":
            self.dimension = 3072
        elif self.model_name == "text-embedding-3-small":
            self.dimension = 1536
        else:
            self.dimension = 1536
        
        # OpenAI APIクライアント
        self._client = None
    
    def get_dimension(self) -> int:
        """エンベディングの次元数を取得"""
        return self.dimension
    
    def _get_client(self):
        """OpenAIクライアントを遅延初期化"""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        テキストのエンベディングを取得
        
        Args:
            texts: エンベディングを取得するテキストのリスト
            
        Returns:
            テキストのエンベディング
        """
        # テキスト前処理
        processed_texts = [text.replace("\n", " ")[:8191] for text in texts]
        
        # OpenAI APIでエンベディングを取得
        client = self._get_client()
        response = client.embeddings.create(
            input=processed_texts,
            model=self.model_name
        )
        
        # 結果を処理して返す（次元数で切り取り）
        embeddings = [d.embedding[:self.dimension] for d in response.data]
        return embeddings