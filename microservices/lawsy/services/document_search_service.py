"""
法文書検索サービス
エンベディングを使用して法文書を検索する機能を提供
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import faiss

from lawsy.interfaces.document_search import DocumentSearchProvider, DocumentSearchResult
from lawsy.interfaces.embedding import EmbeddingProvider


class FaissDocumentSearchService(DocumentSearchProvider):
    """
    FAISSを使用したローカルベクトル検索サービス
    エンベディングプロバイダを使用して検索を行う
    """
    
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
            index_path: FAISSインデックスファイルパス
            documents_path: 文書メタデータJSONファイルパス
        """
        self.embedding_provider = embedding_provider
        self.dim = embedding_provider.get_dimension()
        
        # インデックスとドキュメントを読み込む
        if index_path and documents_path:
            self.load(index_path, documents_path)
        else:
            # 新しいインデックスを作成
            self.index = faiss.IndexFlatIP(self.dim)  # 内積（コサイン類似度）
            self.documents = []
    
    def load(self, index_path: str, documents_path: str):
        """
        保存されたインデックスとドキュメントを読み込む
        
        Args:
            index_path: FAISSインデックスファイルパス
            documents_path: 文書メタデータJSONファイルパス
        """
        # FAISSインデックスを読み込む
        self.index = faiss.read_index(index_path)
        
        # ドキュメントメタデータを読み込む
        with open(documents_path, 'r', encoding='utf-8') as f:
            self.documents = json.load(f)
    
    def save(self, index_path: str, documents_path: str):
        """
        インデックスとドキュメントを保存する
        
        Args:
            index_path: FAISSインデックスファイルパス
            documents_path: 文書メタデータJSONファイルパス
        """
        # ディレクトリを作成
        Path(index_path).parent.mkdir(parents=True, exist_ok=True)
        Path(documents_path).parent.mkdir(parents=True, exist_ok=True)
        
        # FAISSインデックスを保存
        faiss.write_index(self.index, index_path)
        
        # ドキュメントメタデータを保存
        with open(documents_path, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        ドキュメントをインデックスに追加する
        
        Args:
            documents: 追加するドキュメントのリスト
                各ドキュメントは {'title': str, 'content': str, ...} 形式の辞書
        """
        # ドキュメントのテキストを抽出
        texts = [doc['content'] for doc in documents]
        
        # エンベディングを計算
        embeddings = self.embedding_provider.get_embedding(texts)
        
        # FAISSインデックスに追加
        embeddings_array = np.array(embeddings).astype(np.float32)
        self.index.add(embeddings_array)
        
        # ドキュメントメタデータを保存
        self.documents.extend(documents)
    
    def search(
        self,
        query: str,
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[DocumentSearchResult]:
        """
        クエリに一致するドキュメントを検索する
        
        Args:
            query: 検索クエリ
            k: 返す結果の最大数
            filters: メタデータによるフィルター条件
            
        Returns:
            検索結果のリスト
        """
        # クエリをエンベディングに変換
        query_embedding = self.embedding_provider.get_embedding([query])[0]
        query_embedding_array = np.array([query_embedding]).astype(np.float32)
        
        # FAISSで検索
        scores, indices = self.index.search(query_embedding_array, k=k)
        
        # 結果をフォーマット
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(self.documents):
                continue  # 無効なインデックス
                
            doc = self.documents[idx]
            
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
            results.append(DocumentSearchResult(
                title=doc['title'],
                content=doc['content'],
                score=float(scores[0][i]),
                metadata=doc
            ))
        
        return results