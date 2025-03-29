"""
Anthropic Claude APIを使用したLLMプロバイダーの実装
"""
import os
import json
import re
from typing import List, Dict, Any, Optional, AsyncGenerator

from lawsy.interfaces.llm import LLMProvider


class ClaudeProvider(LLMProvider):
    """Anthropic Claude APIを使用したLLMプロバイダー"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-opus-20240229"
    ):
        """
        初期化
        
        Args:
            api_key: Anthropic APIキー
            model: 使用するモデル名
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic APIキーが指定されていません")
            
        self.model = model
        
        # クライアントは遅延して初期化
        self._client = None
        
    def _get_client(self):
        """Anthropicクライアントを遅延初期化して返す"""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("anthropic パッケージがインストールされていません")
        return self._client
    
    def _format_json_prompt(self, prompt: str) -> str:
        """JSON出力のプロンプトを整形する"""
        return f"{prompt}\n\nPlease provide your response in JSON format only."
        
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
        
        # JSON出力モードが有効な場合、プロンプトを調整
        if json_mode:
            prompt = self._format_json_prompt(prompt)
        
        args = {
            "model": self.model,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        
        if system_prompt:
            args["system"] = system_prompt
            
        if max_tokens:
            args["max_tokens"] = max_tokens
        
        response = await client.messages.create(**args)
        return response.content[0].text
    
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
        
        args = {
            "model": self.model,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True
        }
        
        if system_prompt:
            args["system"] = system_prompt
            
        if max_tokens:
            args["max_tokens"] = max_tokens
        
        stream = await client.messages.create(**args)
        
        async for chunk in stream:
            if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text') and chunk.delta.text:
                yield chunk.delta.text
    
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
        prompt_with_json = self._format_json_prompt(prompt)
        
        text_result = await self.generate_text(
            prompt=prompt_with_json,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        try:
            return json.loads(text_result)
        except json.JSONDecodeError:
            # JSONのパースに失敗した場合、テキストからJSONを抽出する
            json_match = re.search(r'```json\n([\s\S]*?)\n```', text_result)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
                    
            # コードブロックなしでもう一度試す
            json_match = re.search(r'{[\s\S]*}', text_result)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
                    
            # それでも失敗した場合は空の辞書を返す
            return {}