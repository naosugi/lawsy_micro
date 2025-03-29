"""
ベクトル検索サービス
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np

from lawsy.interfaces.search import SearchProvider, SearchResult
from lawsy.interfaces.embedding import EmbeddingProvider
from lawsy.config import Config


class VectorSearchService(SearchProvider):
    """ベクトル検索サービス"""
    
    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        index_path: Optional[str] = None,
        documents_path: Optional[str] = None
    ):
        """
        初期化
        
        Args:
            embedding_provider: エンベディングプロバイダ
            index_path: インデックスファイルパス
            documents_path: ドキュメントファイルパス
        """
        self.embedding_provider = embedding_provider
        self.index_path = index_path or Config.get("FAISS_INDEX_PATH")
        self.documents_path = documents_path or Config.get("FAISS_DOCUMENTS_PATH")
        
        # FAISSインデックスは遅延して初期化
        self._index = None
        self._documents = []
        
        # 初期化時に読み込み
        if self.index_path and self.documents_path:
            self.load()
    
    def load(self):
        """インデックスとドキュメントを読み込む"""
        try:
            import faiss
            
            # インデックスを読み込む
            if Path(self.index_path).exists():
                self._index = faiss.read_index(self.index_path)
            
            # ドキュメントを読み込む
            if Path(self.documents_path).exists():
                with open(self.documents_path, 'r', encoding='utf-8') as f:
                    self._documents = json.load(f)
        except ImportError:
            raise ImportError("FAISSがインストールされていません。pip install faiss-cpu または faiss-gpu でインストールしてください。")
        except Exception as e:
            raise RuntimeError(f"インデックスまたはドキュメントの読み込みに失敗しました: {str(e)}")
    
    def _get_index(self):
        """FAISSインデックスを遅延初期化して返す"""
        if self._index is None:
            import faiss
            dim = self.embedding_provider.get_dimension()
            self._index = faiss.IndexFlatIP(dim)  # 内積（コサイン類似度）用のインデックス
        return self._index
    
    def search(
        self, 
        query: str, 
        limit: int = 10, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        ベクトル検索を実行する
        
        Args:
            query: 検索クエリ
            limit: 返す結果の最大数
            filters: 検索フィルター
            
        Returns:
            検索結果のリスト
        """
        # インデックスを取得
        index = self._get_index()
        
        # クエリをベクトル化
        query_embedding = self.embedding_provider.get_embeddings([query])[0]
        query_embedding_array = np.array([query_embedding]).astype(np.float32)
        
        # 検索を実行
        k = min(limit, len(self._documents)) if self._documents else limit
        if k == 0:
            return []
            
        scores, indices = index.search(query_embedding_array, k=k)
        
        # 結果を構築
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(self._documents):
                continue  # 無効なインデックス
            
            doc = self._documents[idx]
            
            # フィルター適用
            if filters:
                skip = False
                for key, value in filters.items():
                    if key in doc and doc[key] != value:
                        skip = True
                        break
                if skip:
                    continue
            
            # 結果を追加
            results.append(SearchResult(
                title=doc.get("title", ""),
                content=doc.get("content", ""),
                url=doc.get("url", ""),
                score=float(scores[0][i]),
                metadata=doc
            ))
        
        return results