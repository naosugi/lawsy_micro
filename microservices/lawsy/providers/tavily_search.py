"""
Tavily検索プロバイダ
"""
import os
import asyncio
from typing import List, Optional, Dict, Any

from lawsy.interfaces.search import SearchProvider, WebSearchResult


class TavilySearchProvider(SearchProvider):
    """Tavily APIを使用した検索プロバイダ"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初期化
        
        Args:
            api_key: Tavily API キー
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Tavily APIキーが必要です。"
                "環境変数TAVILY_API_KEYを設定するか、初期化時に指定してください。"
            )
        
        # クライアントは遅延して初期化
        self._client = None

    def _get_client(self):
        """Tavily APIクライアントを遅延初期化して返す"""
        if self._client is None:
            try:
                from tavily import TavilyClient
                self._client = TavilyClient(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "tavily パッケージがインストールされていません。"
                    "pip install tavily でインストールしてください。"
                )
        return self._client

    async def _fix_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tavilyのレスポンスの文字エンコーディングを修正する
        
        Args:
            response: Tavilyのレスポンス
            
        Returns:
            修正されたレスポンス
        """
        # 必要なパッケージを遅延インポート
        try:
            import fast_langdetect as langdetect
            import httpx
        except ImportError:
            raise ImportError(
                "fast-langdetect と httpx パッケージがインストールされていません。"
                "pip install fast-langdetect httpx でインストールしてください。"
            )

        async def fix_result(result: Dict[str, Any]) -> Dict[str, Any]:
            """個々の検索結果を修正する"""
            result = result.copy()
            
            # 言語検出（複数行のテキストには対応していないので、スペースに置き換え）
            try:
                content = result.get("content", "").replace("\n", " ")
                
                if content:
                    det = langdetect.detect(content)
                    
                    # 日本語でない場合はエンコーディングを修正
                    if det["lang"] != "ja":
                        r = httpx.head(result["url"], timeout=1.0)
                        
                        if r.encoding:
                            # 文字エンコーディングを修正
                            for key in ("content", "raw_content"):
                                if key in result and isinstance(result[key], str):
                                    result[key] = result[key].encode("latin-1").decode(r.encoding)
            except Exception:
                # エラーが発生した場合は無視
                pass
                
            return result

        # レスポンスを修正
        fixed_response = response.copy()
        
        # 各検索結果を並行して修正
        if "results" in response:
            tasks = [fix_result(result) for result in response["results"]]
            results = await asyncio.gather(*tasks)
            fixed_response["results"] = results
            
        return fixed_response

    def search(
        self, 
        query: str, 
        k: int = 30, 
        language: str = "ja", 
        domains: Optional[List[str]] = None
    ) -> List[WebSearchResult]:
        """
        Tavily検索を実行する
        
        Args:
            query: 検索クエリ
            k: 返す結果の最大数
            language: 検索結果の言語（Tavilyでは使用しないが、インターフェースのため保持）
            domains: 検索対象のドメイン（指定されている場合）
            
        Returns:
            検索結果のリスト
        """
        client = self._get_client()
        
        # ドメインはTavilyのinclude_domainsとして使用
        include_domains = domains or []
        
        # API呼び出し
        response = client.search(
            query=query,
            include_images=False,
            include_raw_content=False,
            max_results=k,
            include_domains=include_domains
        )
        
        # レスポンスのエンコーディングを修正
        fixed_response = asyncio.run(self._fix_response(response))
        
        # 結果を処理
        results = []
        
        if "results" in fixed_response:
            for result in fixed_response["results"]:
                results.append(
                    WebSearchResult(
                        title=result.get("title", ""),
                        snippet=result.get("content", ""),
                        url=result.get("url", ""),
                        meta=result
                    )
                )
        
        return results