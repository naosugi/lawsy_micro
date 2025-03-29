"""
OpenAIのエンベディングプロバイダ実装
"""
import os
from typing import List, Optional

from lawsy.interfaces.embedding import EmbeddingProvider


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAIのエンベディングプロバイダ"""
    
    def __init__(
        self,
        model_name: str = "text-embedding-3-small",
        dim: Optional[int] = None,
        api_key: Optional[str] = None
    ):
        """
        初期化
        
        Args:
            model_name: OpenAIのエンベディングモデル名
            dim: エンベディングの次元数（Noneの場合はモデルのデフォルト値）
            api_key: OpenAI API キー（Noneの場合は環境変数から取得）
        """
        # モデル名の検証
        valid_models = ["text-embedding-3-small", "text-embedding-3-large"]
        if model_name not in valid_models:
            raise ValueError(f"モデル名は {', '.join(valid_models)} のいずれかである必要があります")
        
        self.model_name = model_name
        
        # 次元数の設定
        if dim is None:
            if model_name == "text-embedding-3-large":
                self.dim = 3072
            elif model_name == "text-embedding-3-small":
                self.dim = 1536
        else:
            # 次元数の検証
            max_dim = 3072 if model_name == "text-embedding-3-large" else 1536
            if dim <= 0 or dim > max_dim:
                raise ValueError(f"{model_name} の有効な次元数は 1～{max_dim} です")
            self.dim = dim
        
        # OpenAI クライアントの設定
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI APIキーが指定されていません")
        
        # クライアント初期化は遅延して行う（実際に使うときに初期化）
        self._client = None
    
    def _get_client(self):
        """OpenAIクライアントを遅延初期化して返す"""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def get_dimension(self) -> int:
        """次元数を返す"""
        return self.dim

    def get_embedding(self, texts: List[str]) -> List[List[float]]:
        """
        OpenAIを使用してテキストのエンベディングを取得する
        
        Args:
            texts: エンベディングを取得するテキストのリスト
            
        Returns:
            テキストのエンベディング（リストのリスト）
        """
        # 前処理
        processed_texts = [text.replace("\n", " ")[:6000] for text in texts]
        
        # OpenAI APIでエンベディングを取得
        client = self._get_client()
        response = client.embeddings.create(
            input=processed_texts,
            model=self.model_name
        )
        
        # 結果を処理して返す
        embeddings = [d.embedding[:self.dim] for d in response.data]
        return embeddings