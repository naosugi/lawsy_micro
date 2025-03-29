"""
レポート生成インターフェース
さまざまな生成AIモデルに対する抽象化レイヤー
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator


class ReportGenerationProvider(ABC):
    """レポート生成プロバイダーのインターフェース"""
    
    @abstractmethod
    async def expand_query(self, query: str) -> List[str]:
        """
        クエリーを拡張する
        
        Args:
            query: 元のクエリー
            
        Returns:
            拡張されたクエリーのリスト
        """
        pass
    
    @abstractmethod
    async def refine_query(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """
        検索結果を基にクエリーを精緻化する
        
        Args:
            query: 元のクエリー
            search_results: 検索結果
            
        Returns:
            精緻化されたクエリー
        """
        pass
    
    @abstractmethod
    async def create_outline(
        self, 
        query: str, 
        search_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        検索結果からレポートのアウトラインを作成する
        
        Args:
            query: クエリー
            search_results: 検索結果
            
        Returns:
            アウトライン情報
        """
        pass
    
    @abstractmethod
    async def create_mindmap(
        self, 
        query: str, 
        outline: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        アウトラインからマインドマップを作成する
        
        Args:
            query: クエリー
            outline: アウトラインデータ
            
        Returns:
            マインドマップデータ
        """
        pass
    
    @abstractmethod
    async def write_report_section(
        self, 
        query: str, 
        references: str, 
        section_outline: str
    ) -> AsyncGenerator[str, None]:
        """
        レポートのセクションを記述する
        
        Args:
            query: クエリー
            references: 参照情報
            section_outline: セクションのアウトライン
            
        Returns:
            生成されたテキストのストリーム
        """
        pass
    
    @abstractmethod
    async def write_report_lead(
        self, 
        query: str,
        title: str, 
        draft: str
    ) -> AsyncGenerator[str, None]:
        """
        レポートの導入部を記述する
        
        Args:
            query: クエリー
            title: レポートのタイトル
            draft: レポート全体のドラフト
            
        Returns:
            生成されたテキストのストリーム
        """
        pass
    
    @abstractmethod
    async def write_report_conclusion(
        self, 
        query: str, 
        report_draft: str
    ) -> AsyncGenerator[str, None]:
        """
        レポートの結論部を記述する
        
        Args:
            query: クエリー
            report_draft: レポート全体のドラフト
            
        Returns:
            生成されたテキストのストリーム
        """
        pass