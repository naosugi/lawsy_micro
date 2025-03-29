"""
OpenAI APIを使用したLLMプロバイダーの実装
"""
import os
import json
from typing import List, Dict, Any, Optional, AsyncGenerator

from lawsy.interfaces.llm import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI APIを使用したLLMプロバイダー"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        organization: Optional[str] = None
    ):
        """
        初期化
        
        Args:
            api_key: OpenAI APIキー
            model: 使用するモデル名
            organization: 組織ID（オプション）
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI APIキーが指定されていません")
            
        self.model = model
        self.organization = organization
        
        # クライアントは遅延して初期化
        self._client = None
        
    def _get_client(self):
        """OpenAIクライアントを遅延初期化して返す"""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                
                args = {
                    "api_key": self.api_key
                }
                
                if self.organization:
                    args["organization"] = self.organization
                    
                self._client = AsyncOpenAI(**args)
            except ImportError:
                raise ImportError("openai パッケージがインストールされていません")
        return self._client
        
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
        client = self._get_client()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        args = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            args["max_tokens"] = max_tokens
            
        if json_mode:
            args["response_format"] = {"type": "json_object"}
        
        response = await client.chat.completions.create(**args)
        return response.choices[0].message.content
    
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
        client = self._get_client()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        args = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        
        if max_tokens:
            args["max_tokens"] = max_tokens
        
        response = await client.chat.completions.create(**args)
        
        async for chunk in response:
            if chunk.choices and hasattr(chunk.choices[0], 'delta') and hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
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
        text_result = await self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            json_mode=True
        )
        
        try:
            return json.loads(text_result)
        except json.JSONDecodeError:
            # JSONのパースに失敗した場合、テキストからJSONを抽出する
            import re
            json_match = re.search(r'```json\n([\s\S]*?)\n```', text_result)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
                    
            # それでも失敗した場合は空の辞書を返す
            return {}