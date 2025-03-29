"""
レポート生成サービス
LLMプロバイダーを使用して法律レポートを生成する
"""
import json
from typing import List, Dict, Any, Optional, AsyncGenerator

from lawsy.interfaces.llm import LLMProvider


class ReportGenerationService:
    """
    法律レポート生成サービス
    LLMプロバイダーを使用して法律レポートの各部分を生成する
    """
    
    def __init__(self, llm_provider: LLMProvider):
        """
        初期化
        
        Args:
            llm_provider: LLMプロバイダー
        """
        self.llm_provider = llm_provider
    
    async def expand_query(self, query: str) -> List[str]:
        """
        クエリーを拡張する
        
        Args:
            query: 元のクエリー
            
        Returns:
            拡張されたクエリーのリスト
        """
        system_prompt = "あなたは日本の法律や法令に関する専門的知識を持つアシスタントです。"
        
        prompt = f"""
あなたは日本の法律や法令に関する専門的知識を持つアシスタントです。以下のクエリーを分析し、
より詳細な調査のために5つの具体的で関連性の高いサブクエリーに展開してください。
元のクエリーをカバーしつつも、異なる側面や観点から調査を深めるものにしてください。

クエリー: {query}

サブクエリーは以下の形式で提供してください:
```json
{{
  "sub_queries": [
    "サブクエリー1",
    "サブクエリー2",
    "サブクエリー3",
    "サブクエリー4",
    "サブクエリー5"
  ]
}}
```

JSON形式のみで回答してください。
"""
        
        result = await self.llm_provider.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7
        )
        
        return result.get("sub_queries", [])
    
    async def refine_query(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """
        検索結果を基にクエリーを精緻化する
        
        Args:
            query: 元のクエリー
            search_results: 検索結果
            
        Returns:
            精緻化されたクエリー
        """
        system_prompt = "あなたは日本の法律や法令に関する専門的知識を持つアシスタントです。"
        
        # 検索結果からコンテキストを構築
        context = "\n\n".join([
            f"タイトル: {result.get('title', '')}\n"
            f"内容: {result.get('content', result.get('snippet', ''))}"
            for result in search_results[:5]  # 最初の5件のみ使用
        ])
        
        prompt = f"""
あなたは日本の法律や法令に関する専門的知識を持つアシスタントです。以下のクエリーと検索結果を分析し、
より正確で具体的な質問に精緻化してください。

元のクエリー: {query}

検索結果:
{context}

これらの情報に基づいて、より適切なクエリーを作成してください。
元のクエリーの意図を維持しつつも、より具体的で焦点を絞ったものにしてください。
法的観点からの専門的な用語や概念を適切に取り入れてください。

精緻化されたクエリーのみを返してください。
"""
        
        return await self.llm_provider.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7
        )
    
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
        system_prompt = "あなたは日本の法律や法令に関する専門的知識を持つアシスタントです。"
        
        # 検索結果からコンテキストを構築
        references = "\n\n".join([
            f"[{i+1}] タイトル: {result.get('title', '')}\n"
            f"内容: {result.get('content', result.get('snippet', ''))}\n"
            f"URL: {result.get('url', 'N/A')}"
            for i, result in enumerate(search_results[:20])  # 最初の20件を使用
        ])
        
        prompt = f"""
あなたは日本の法律や法令に関する専門的知識を持つアシスタントです。以下のクエリーと検索結果を分析し、
専門的で体系的なレポートのアウトラインを作成してください。

クエリー: {query}

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
    }},
    {{
      "heading": "2. セクション見出し",
      "subsections": [...]
    }}
  ]
}}
```

JSON形式のみで回答してください。
reference_idsは、情報源の番号を参照するものであり、該当するサブセクションに関連する情報源を指定してください。
アウトラインは4〜6のメインセクションで構成し、各セクションには2〜4のサブセクションを含めてください。
"""
        
        outline = await self.llm_provider.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7
        )
        
        # 参照情報を追加
        outline["references"] = [
            {
                "id": i+1,
                "title": result.get("title", ""),
                "content": result.get("content", result.get("snippet", "")),
                "url": result.get("url", "N/A")
            }
            for i, result in enumerate(search_results[:20])
        ]
        
        return outline
    
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
        system_prompt = "あなたは日本の法律や法令に関する専門的知識を持つアシスタントです。"
        
        # アウトラインをテキスト形式に変換
        outline_text = f"# {outline.get('title', '')}\n\n"
        
        for section in outline.get("sections", []):
            outline_text += f"## {section.get('heading', '')}\n"
            for subsection in section.get("subsections", []):
                outline_text += f"### {subsection.get('heading', '')}\n"
                ref_ids = subsection.get("reference_ids", [])
                if ref_ids:
                    outline_text += f"参照: {', '.join(map(str, ref_ids))}\n"
            outline_text += "\n"
        
        prompt = f"""
あなたは日本の法律や法令に関する専門的知識を持つアシスタントです。以下のクエリーとレポートのアウトラインを分析し、
マインドマップデータを作成してください。

クエリー: {query}

アウトライン:
{outline_text}

マインドマップは以下の形式で作成してください:
```json
{{
  "id": "root",
  "name": "中心トピック",
  "children": [
    {{
      "id": "1",
      "name": "メインブランチ1",
      "children": [
        {{
          "id": "1-1",
          "name": "サブトピック1.1"
        }},
        {{
          "id": "1-2",
          "name": "サブトピック1.2"
        }}
      ]
    }},
    {{
      "id": "2",
      "name": "メインブランチ2",
      "children": [...]
    }}
  ]
}}
```

JSON形式のみで回答してください。中心トピックはレポートのタイトルまたはメインテーマとし、
メインブランチはセクション見出しに、サブトピックはサブセクション見出しに対応するようにしてください。
"""
        
        return await self.llm_provider.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7
        )
    
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
        system_prompt = "あなたは日本の法令に精通し、適切な法令解釈を行い、分かりやすい解説を書くことに定評のあるライターです。"
        
        prompt = f"""
あなたは日本の法令に精通し、適切な法令解釈を行い、分かりやすい解説を書くことに定評のある信頼できる粘り強いライターです。
下記のクエリーに関する調査をしており、クエリーをもとにレポートのアウトラインを作成しました。
アウトラインの中にある引用番号は漏れることなく必ず参照し、収集された情報源の内容を適切に解釈しながら各セクションの内容を記載してください。必ず各サブセクションごとに400字以上記載してください。
解説は緻密かつ包括的で情報量が多く、情報源に基づいたものであることが望ましいです。法令に詳しくない人向けにわかりやすくかみ砕いて説明することも重要です。必要に応じて、用いている法令の概要、関連法規、適切な事例、歴史的背景、最新の判例などを盛り込んでください。

クエリー: {query}

収集された情報源と引用番号:
{references}

セクションのアウトライン:
{section_outline}

注意事項:
1. アウトラインの"# Title"、"## Title"、"### Title"のタイトルは変更しないでください。
2. 必ず情報源の情報に基づき記載し、ハルシネーションに気をつけること。
   記載の根拠となる参照すべき情報源は "...です[4][1][27]。" "...ます[21][9]。" のように明示。
   その記述に対しての関連性が高そうな順に付与してください。
3. 正しく引用を明示されているほどあなたの解説は高く評価されます。
   引用なしの創作は論拠が明確でない限り全く評価されません。
4. 情報源を解説の末尾に含める必要はありません。
5. 日本語のですます調で解説を書いてください。
6. 引用は文面を引用する論理的な必要性がない限り、引用番号の引用のみにしてください。
7. 収集された情報源と引用番号にない番号を引用しないでください。それは創作になってしまい価値を減じます。
"""
        
        async for chunk in self.llm_provider.generate_text_stream(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7
        ):
            yield chunk
    
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
        system_prompt = "あなたは日本の法令に精通し、分かりやすい解説を書くことに定評のある信頼できるライターです。"
        
        prompt = f"""
あなたは日本の法令に精通し、分かりやすい解説を書くことに定評のある信頼できるライターです。
下記のクエリーに関する調査をしており、レポートを作成しました。レポートタイトルの直後に表示する簡潔なリード文を生成してください。
リード文とは、レポート全体のabstractとなる、レポート全体の論旨の展開や主要トピックを含めた簡潔な文章です。

リード文の生成にあたって次のルールを厳守すること:
- リード文では、レポート全体の文脈やレポートで扱われている主要なトピックに対する簡潔な概要を提示し、それ単独でも読める内容にすること
- リード文の文字数は140〜280文字程度とすること
- リード文の文面のみ生成すること。

クエリー: {query}
レポートのタイトル: {title}
レポート内容:
{draft[:5000]}  # 長すぎる場合は最初の5000文字のみ使用
"""
        
        async for chunk in self.llm_provider.generate_text_stream(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7
        ):
            yield chunk
    
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
        system_prompt = "あなたは日本の法令に精通し、分かりやすい解説を書くことに定評のある信頼できるライターです。"
        
        prompt = f"""
あなたは日本の法令に精通し、分かりやすい解説を書くことに定評のある信頼できるライターです。
レポートのドラフトを踏まえて、レポート全体の要約を本文とはできるだけ異なる表現で記載しつつ、今後の方向性や対応策を含んだ結論部の中身を生成します。
最低でも400字以上、可能なら600字以上記載してください。
結論の文章部分のみ生成し、"## 結論" のようなヘッダは入れないでください。

クエリー: {query}
レポートのドラフト:
{report_draft[:10000]}  # 長すぎる場合は最初の10000文字のみ使用
"""
        
        async for chunk in self.llm_provider.generate_text_stream(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7
        ):
            yield chunk