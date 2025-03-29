"""
レポート生成サービス
"""
import json
from typing import List, Dict, Any, Optional, AsyncGenerator

from lawsy.interfaces.llm import LLMProvider
from lawsy.interfaces.search import SearchResult


class ReportService:
    """レポート生成サービス"""
    
    def __init__(self, llm_provider: LLMProvider):
        """
        初期化
        
        Args:
            llm_provider: LLMプロバイダ
        """
        self.llm_provider = llm_provider
    
    async def expand_query(self, query: str) -> List[str]:
        """
        クエリを拡張する
        
        Args:
            query: 元のクエリ
            
        Returns:
            拡張クエリのリスト
        """
        system_prompt = "あなたは日本の法律や法令に関する専門的知識を持つアシスタントです。"
        
        prompt = f"""
次のクエリを分析し、より詳細な調査のために5つの具体的で関連性の高いサブクエリに展開してください。
元のクエリをカバーしつつも、異なる側面や観点から調査を深めるものにしてください。

クエリ: {query}

JSON形式のみで回答してください:
```json
{{
  "sub_queries": [
    "サブクエリ1",
    "サブクエリ2",
    "サブクエリ3",
    "サブクエリ4",
    "サブクエリ5"
  ]
}}
```
"""
        
        result = await self.llm_provider.generate_json(
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        return result.get("sub_queries", [])
    
    async def create_outline(
        self, 
        query: str, 
        search_results: List[SearchResult]
    ) -> Dict[str, Any]:
        """
        レポートのアウトラインを作成する
        
        Args:
            query: クエリ
            search_results: 検索結果
            
        Returns:
            アウトライン
        """
        system_prompt = "あなたは日本の法律や法令に関する専門的知識を持つアシスタントです。"
        
        # 検索結果からコンテキストを構築
        references = "\n\n".join([
            f"[{i+1}] タイトル: {result.title}\n"
            f"内容: {result.content}\n"
            f"URL: {result.url or 'N/A'}"
            for i, result in enumerate(search_results[:20])
        ])
        
        prompt = f"""
次のクエリと検索結果を分析し、専門的で体系的なレポートのアウトラインを作成してください。

クエリ: {query}

以下の情報源を参考にしてください:

{references}

アウトラインは以下の形式で作成してください:
```json
{{
  "title": "レポートタイトル",
  "sections": [
    {{
      "heading": "1. セクション見出し",
      "subsections": [
        {{
          "heading": "1.1 サブセクション見出し",
          "reference_ids": [1, 5, 8]
        }},
        {{
          "heading": "1.2 サブセクション見出し",
          "reference_ids": [2, 7, 10]
        }}
      ]
    }}
  ]
}}
```

アウトラインは4〜6のメインセクションで構成し、各セクションには2〜4のサブセクションを含めてください。
reference_idsは情報源の番号を参照してください。
"""
        
        outline = await self.llm_provider.generate_json(
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # 参照情報を追加
        outline["references"] = [
            {
                "id": i+1,
                "title": result.title,
                "content": result.content,
                "url": result.url
            }
            for i, result in enumerate(search_results[:20])
        ]
        
        return outline
    
    async def write_section(
        self, 
        query: str, 
        references: str, 
        section_outline: str
    ) -> AsyncGenerator[str, None]:
        """
        レポートのセクションを記述する
        
        Args:
            query: クエリ
            references: 参照情報
            section_outline: セクションのアウトライン
            
        Returns:
            生成されたテキスト
        """
        system_prompt = "あなたは日本の法令に精通し、適切な法令解釈を行い、分かりやすい解説を書くことに定評のあるライターです。"
        
        prompt = f"""
下記のクエリに関する調査をしており、アウトラインを作成しました。
アウトラインの中にある引用番号は漏れることなく参照し、情報源の内容を適切に解釈しながら各セクションを記載してください。
各サブセクションごとに400字以上記載し、法令に詳しくない人向けにわかりやすく説明してください。

クエリ: {query}

収集された情報源と引用番号:
{references}

セクションのアウトライン:
{section_outline}

注意事項:
1. アウトラインのタイトルは変更しないでください。
2. 必ず情報源に基づき記載し、ハルシネーションに気をつけてください。
3. 引用は "...です[4][1][27]。" のように明示してください。
4. 日本語のです・ます調で解説を書いてください。
"""
        
        async for chunk in self.llm_provider.generate_stream(
            prompt=prompt,
            system_prompt=system_prompt
        ):
            yield chunk