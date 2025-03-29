"""
LLM (Large Language Model) プロバイダーインターフェース
さまざまな生成AIモデルに対する抽象化レイヤー
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator, Union


class LLMProvider(ABC):
    """LLMプロバイダーのインターフェース"""
    
    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        json_mode: bool = False
    ) -> str:
        """
        テキストを生成する
        
        Args:
            prompt: 入力プロンプト
            system_prompt: システムプロンプト
            max_tokens: 生成する最大トークン数
            temperature: 生成の温度
            json_mode: JSON出力モードを有効にするかどうか
            
        Returns:
            生成されたテキスト
        """
        pass
    
    @abstractmethod
    async def generate_text_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        ストリーミングモードでテキストを生成する
        
        Args:
            prompt: 入力プロンプト
            system_prompt: システムプロンプト
            max_tokens: 生成する最大トークン数
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
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        JSON形式のデータを生成する
        
        Args:
            prompt: 入力プロンプト
            system_prompt: システムプロンプト
            max_tokens: 生成する最大トークン数
            temperature: 生成の温度
            
        Returns:
            生成されたJSONデータ
        """
        pass