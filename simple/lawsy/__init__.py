"""
Lawsyマイクロサービスパッケージ
法律関連のテキスト検索と分析のためのマイクロサービス
"""

__version__ = "0.1.0"

# 主要なインターフェースとプロバイダーをインポート
from lawsy.interfaces import SearchResult, SearchProvider, EmbeddingProvider, LLMProvider
from lawsy.config import Config