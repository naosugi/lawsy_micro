"""
OpenAI APIを使用したLLMプロバイダ
"""
import json
from typing import Dict, Any, Optional, AsyncGenerator

from lawsy.interfaces.llm import LLMProvider
from lawsy.config import Config


class OpenAILLMProvider(LLMProvider):
    """OpenAI APIを使用したLLMプロバイダ"""
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        初期化
        
        Args:
            model_name: モデル名
            api_key: OpenAI APIキー
        """
        self.model_name = model_name or Config.get("OPENAI_LLM_MODEL")
        self.api_key = api_key or Config.get_required("OPENAI_API_KEY")
        
        # OpenAI APIクライアント
        self._client = None
    
    def _get_client(self):
        """OpenAIクライアントを遅延初期化"""
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client
    
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
        client = self._get_client()
        
        # メッセージを構築
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # APIリクエストを実行
        response = await client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            stream=False  # streamパラメータは無視（別メソッドで対応）
        )
        
        return response.choices[0].message.content
    
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
        client = self._get_client()
        
        # メッセージを構築
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # APIリクエストを実行
        stream = await client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
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
        client = self._get_client()
        
        # メッセージを構築
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # APIリクエストを実行
        response = await client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"}
        )
        
        # JSONとしてパース
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {}