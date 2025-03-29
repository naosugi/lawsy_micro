"""
設定管理モジュール
環境変数からの設定読み込みと、デフォルト値の提供
"""
import os
from typing import Dict, Any, Optional


class Config:
    """設定管理クラス"""
    
    # デフォルト設定
    _defaults = {
        # 検索設定
        "SEARCH_PROVIDER": "google",
        "GOOGLE_CUSTOM_SEARCH_ENGINE_ACCESS_KEY": None,
        "GOOGLE_CUSTOM_SEARCH_ENGINE_ID": None,
        "TAVILY_API_KEY": None,
        
        # エンベディング設定
        "EMBEDDING_PROVIDER": "openai",
        "OPENAI_API_KEY": None,
        "OPENAI_EMBEDDING_MODEL": "text-embedding-3-small",
        "SENTENCE_TRANSFORMER_MODEL": "intfloat/multilingual-e5-large",
        
        # LLM設定
        "LLM_PROVIDER": "openai",
        "OPENAI_LLM_MODEL": "gpt-4o",
        "ANTHROPIC_API_KEY": None,
        "CLAUDE_MODEL": "claude-3-opus-20240229",
        
        # ドキュメント検索設定
        "DOCUMENT_SEARCH_PROVIDER": "faiss",
        "FAISS_INDEX_PATH": None,
        "FAISS_DOCUMENTS_PATH": None,
        
        # OpenSearch設定
        "OPENSEARCH_ENDPOINT": None,
        "OPENSEARCH_INDEX": "law_documents",
        "OPENSEARCH_USERNAME": None,
        "OPENSEARCH_PASSWORD": None,
        "OPENSEARCH_AUTH_TYPE": "basic",
        
        # Vertex AI Search設定
        "VERTEX_PROJECT_ID": None,
        "VERTEX_LOCATION": "us-central1",
        "VERTEX_DATA_STORE_ID": None,
    }
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        設定値を取得する
        
        Args:
            key: 設定キー
            default: キーが存在しない場合のデフォルト値
            
        Returns:
            設定値
        """
        # 環境変数から取得を試みる
        value = os.getenv(key)
        
        # 環境変数になければデフォルト値を返す
        if value is None:
            return cls._defaults.get(key, default)
            
        return value
    
    @classmethod
    def get_required(cls, key: str) -> Any:
        """
        必須設定値を取得する（存在しない場合は例外を発生）
        
        Args:
            key: 設定キー
            
        Returns:
            設定値
            
        Raises:
            ValueError: 設定値が存在しない場合
        """
        value = cls.get(key)
        if value is None:
            raise ValueError(f"必須設定 '{key}' が指定されていません")
        return value