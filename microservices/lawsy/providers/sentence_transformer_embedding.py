"""
Sentence Transformersを使用したローカルエンベディングプロバイダ実装
"""
from typing import List, Optional

from lawsy.interfaces.embedding import EmbeddingProvider


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    """Sentence Transformers を使用したエンベディングプロバイダ"""
    
    def __init__(
        self,
        model_name: str = "intfloat/multilingual-e5-large",
        dim: Optional[int] = None,
        device: str = "cpu"
    ):
        """
        初期化
        
        Args:
            model_name: Sentence Transformersのモデル名
            dim: エンベディングの次元数（Noneの場合はモデルのデフォルト値）
            device: 実行デバイス ('cpu' または 'cuda')
        """
        self.model_name = model_name
        self.device = device
        
        # モデルとその次元数は遅延して初期化（実際に使うときに初期化）
        self._model = None
        self._default_dim = None
        
        # 次元数の設定
        self.dim = dim  # ユーザーが指定した次元数

    def _get_model(self):
        """Sentence Transformersモデルを遅延初期化して返す"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name, device=self.device)
                self._default_dim = self._model.get_sentence_embedding_dimension()
            except ImportError:
                raise ImportError(
                    "sentence-transformers パッケージがインストールされていません。"
                    "pip install sentence-transformers でインストールしてください。"
                )
        return self._model

    def get_dimension(self) -> int:
        """次元数を返す"""
        # 必要に応じてモデルを初期化して次元数を取得
        if self._default_dim is None:
            self._get_model()
        
        # ユーザー指定の次元数またはデフォルト次元数を返す
        return self.dim or self._default_dim

    def get_embedding(self, texts: List[str]) -> List[List[float]]:
        """
        Sentence Transformersを使用してテキストのエンベディングを取得する
        
        Args:
            texts: エンベディングを取得するテキストのリスト
            
        Returns:
            テキストのエンベディング（リストのリスト）
        """
        # モデルを取得
        model = self._get_model()
        
        # エンベディングを計算
        embeddings = model.encode(texts)
        
        # 次元数を制限（指定されている場合）
        if self.dim is not None and self.dim < self._default_dim:
            embeddings = embeddings[:, :self.dim]
        
        # numpy配列をリストに変換して返す
        return embeddings.tolist()