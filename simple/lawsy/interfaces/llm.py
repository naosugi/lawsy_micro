"""
LLMインターフェース
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator


class LLMProvider(ABC):
    """LLMプロバイダーのインターフェース"""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str:
        """
        テキストを生成する
        
        Args:
            prompt: プロンプト
            system_prompt: システムプロンプト
            temperature: 生成の温度
            stream: ストリーミングを有効にするかどうか
            
        Returns:
            生成されたテキスト
        """
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        テキストをストリーミングで生成する
        
        Args:
            prompt: プロンプト
            system_prompt: システムプロンプト
            temperature: 生成の温度
            
        Returns:
            生成されたテキストのストリーム
        """
        pass
    
    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        JSON形式のテキストを生成する
        
        Args:
            prompt: プロンプト
            system_prompt: システムプロンプト
            temperature: 生成の温度
            
        Returns:
            生成されたJSONデータ
        """
        pass