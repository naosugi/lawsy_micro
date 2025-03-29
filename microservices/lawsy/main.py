"""
Lawsyマイクロサービスのメインエントリーポイント
Cloud Function用のエンドポイントを提供
"""
import os
import json
from typing import Dict, Any, List, Optional

# 環境変数のデフォルト値を設定
DEFAULT_SEARCH_PROVIDER = "google"
DEFAULT_EMBEDDING_PROVIDER = "openai"
DEFAULT_DOCUMENT_SEARCH_PROVIDER = "faiss"
DEFAULT_LLM_PROVIDER = "openai"


def get_search_provider(provider_name: str = None):
    """
    指定された名前の検索プロバイダを取得する
    
    Args:
        provider_name: プロバイダ名（デフォルト: 環境変数またはgoogle）
        
    Returns:
        検索プロバイダのインスタンス
    """
    provider_name = provider_name or os.getenv("SEARCH_PROVIDER", DEFAULT_SEARCH_PROVIDER)
    
    if provider_name == "google":
        from lawsy.providers.google_search import GoogleSearchProvider
        return GoogleSearchProvider()
    elif provider_name == "tavily":
        from lawsy.providers.tavily_search import TavilySearchProvider
        return TavilySearchProvider()
    else:
        raise ValueError(f"サポートされていない検索プロバイダです: {provider_name}")


def get_embedding_provider(provider_name: str = None, model_name: str = None):
    """
    指定された名前のエンベディングプロバイダを取得する
    
    Args:
        provider_name: プロバイダ名（デフォルト: 環境変数またはopenai）
        model_name: モデル名（デフォルト: プロバイダのデフォルト値）
        
    Returns:
        エンベディングプロバイダのインスタンス
    """
    provider_name = provider_name or os.getenv("EMBEDDING_PROVIDER", DEFAULT_EMBEDDING_PROVIDER)
    
    if provider_name == "openai":
        from lawsy.providers.openai_embedding import OpenAIEmbeddingProvider
        model_name = model_name or os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        return OpenAIEmbeddingProvider(model_name=model_name)
    elif provider_name == "sentence_transformer":
        from lawsy.providers.sentence_transformer_embedding import SentenceTransformerEmbeddingProvider
        model_name = model_name or os.getenv("SENTENCE_TRANSFORMER_MODEL", "intfloat/multilingual-e5-large")
        return SentenceTransformerEmbeddingProvider(model_name=model_name)
    else:
        raise ValueError(f"サポートされていない埋め込みプロバイダです: {provider_name}")


def get_document_search_provider(provider_name: str = None):
    """
    指定された名前のドキュメント検索プロバイダを取得する
    
    Args:
        provider_name: プロバイダ名（デフォルト: 環境変数またはfaiss）
        
    Returns:
        ドキュメント検索プロバイダのインスタンス
    """
    provider_name = provider_name or os.getenv("DOCUMENT_SEARCH_PROVIDER", DEFAULT_DOCUMENT_SEARCH_PROVIDER)
    
    # エンベディングプロバイダを取得
    embedding_provider = get_embedding_provider()
    
    if provider_name == "faiss":
        from lawsy.services.document_search_service import FaissDocumentSearchService
        index_path = os.getenv("FAISS_INDEX_PATH")
        docs_path = os.getenv("FAISS_DOCUMENTS_PATH")
        
        if index_path and docs_path:
            return FaissDocumentSearchService(
                embedding_provider=embedding_provider,
                index_path=index_path,
                documents_path=docs_path
            )
        else:
            return FaissDocumentSearchService(embedding_provider=embedding_provider)
    elif provider_name == "elasticsearch":
        from lawsy.services.elasticsearch_search_service import ElasticsearchDocumentSearchService
        return ElasticsearchDocumentSearchService(embedding_provider=embedding_provider)
    else:
        raise ValueError(f"サポートされていないドキュメント検索プロバイダです: {provider_name}")


def get_llm_provider(provider_name: str = None, model_name: str = None):
    """
    指定された名前のLLMプロバイダを取得する
    
    Args:
        provider_name: プロバイダ名（デフォルト: 環境変数またはopenai）
        model_name: モデル名（デフォルト: プロバイダのデフォルト値）
        
    Returns:
        LLMプロバイダのインスタンス
    """
    provider_name = provider_name or os.getenv("LLM_PROVIDER", DEFAULT_LLM_PROVIDER)
    
    if provider_name == "openai":
        from lawsy.providers.openai_llm import OpenAIProvider
        model_name = model_name or os.getenv("OPENAI_LLM_MODEL", "gpt-4o")
        return OpenAIProvider(model_name=model_name)
    elif provider_name == "claude":
        from lawsy.providers.claude_llm import ClaudeProvider
        model_name = model_name or os.getenv("CLAUDE_MODEL", "claude-3-opus-20240229")
        return ClaudeProvider(model_name=model_name)
    else:
        raise ValueError(f"サポートされていないLLMプロバイダです: {provider_name}")


def get_report_generation_service(llm_provider_name: str = None):
    """
    レポート生成サービスを取得する
    
    Args:
        llm_provider_name: LLMプロバイダ名
        
    Returns:
        レポート生成サービスのインスタンス
    """
    from lawsy.services.report_generation_service import ReportGenerationService
    llm_provider = get_llm_provider(provider_name=llm_provider_name)
    return ReportGenerationService(llm_provider=llm_provider)


# Cloud Function向けのエンドポイント関数
async def web_search(request):
    """
    Web検索を実行するCloud Function
    
    Args:
        request: Cloud Functionのリクエスト
        
    Returns:
        検索結果のJSON
    """
    # リクエストからパラメータを取得
    try:
        request_json = request.get_json()
        
        query = request_json.get("query")
        provider = request_json.get("provider")
        k = request_json.get("k", 30)
        language = request_json.get("language", "ja")
        domains = request_json.get("domains")
        
        if not query:
            return json.dumps({"error": "検索クエリが指定されていません"}), 400
            
    except Exception as e:
        return json.dumps({"error": f"リクエストの解析に失敗しました: {str(e)}"}), 400
    
    try:
        # 検索プロバイダを取得
        search_provider = get_search_provider(provider)
        
        # 検索を実行
        results = search_provider.search(
            query=query,
            k=k,
            language=language,
            domains=domains
        )
        
        # 結果を整形
        response = {
            "query": query,
            "provider": provider or DEFAULT_SEARCH_PROVIDER,
            "results": [
                {
                    "title": result.title,
                    "snippet": result.snippet,
                    "url": result.url
                }
                for result in results
            ]
        }
        
        return json.dumps(response, ensure_ascii=False), 200
        
    except Exception as e:
        return json.dumps({"error": f"検索に失敗しました: {str(e)}"}), 500


async def document_search(request):
    """
    法文書検索を実行するCloud Function
    
    Args:
        request: Cloud Functionのリクエスト
        
    Returns:
        検索結果のJSON
    """
    # リクエストからパラメータを取得
    try:
        request_json = request.get_json()
        
        query = request_json.get("query")
        provider = request_json.get("provider")
        k = request_json.get("k", 10)
        filters = request_json.get("filters")
        
        if not query:
            return json.dumps({"error": "検索クエリが指定されていません"}), 400
            
    except Exception as e:
        return json.dumps({"error": f"リクエストの解析に失敗しました: {str(e)}"}), 400
    
    try:
        # ドキュメント検索プロバイダを取得
        document_search_provider = get_document_search_provider(provider)
        
        # 検索を実行
        results = document_search_provider.search(
            query=query,
            k=k,
            filters=filters
        )
        
        # 結果を整形
        response = {
            "query": query,
            "provider": provider or DEFAULT_DOCUMENT_SEARCH_PROVIDER,
            "results": [
                {
                    "title": result.title,
                    "content": result.content,
                    "score": result.score,
                    "metadata": result.metadata
                }
                for result in results
            ]
        }
        
        return json.dumps(response, ensure_ascii=False), 200
        
    except Exception as e:
        return json.dumps({"error": f"ドキュメント検索に失敗しました: {str(e)}"}), 500


async def get_embedding(request):
    """
    テキストのエンベディングを取得するCloud Function
    
    Args:
        request: Cloud Functionのリクエスト
        
    Returns:
        エンベディング結果のJSON
    """
    # リクエストからパラメータを取得
    try:
        request_json = request.get_json()
        
        texts = request_json.get("texts")
        provider = request_json.get("provider")
        model = request_json.get("model")
        
        if not texts:
            return json.dumps({"error": "テキストが指定されていません"}), 400
            
        if not isinstance(texts, list):
            texts = [texts]
            
    except Exception as e:
        return json.dumps({"error": f"リクエストの解析に失敗しました: {str(e)}"}), 400
    
    try:
        # エンベディングプロバイダを取得
        embedding_provider = get_embedding_provider(provider, model)
        
        # エンベディングを計算
        embeddings = embedding_provider.get_embedding(texts)
        
        # 結果を整形
        response = {
            "provider": provider or DEFAULT_EMBEDDING_PROVIDER,
            "model": embedding_provider.model_name,
            "dimension": embedding_provider.get_dimension(),
            "embeddings": embeddings
        }
        
        return json.dumps(response), 200
        
    except Exception as e:
        return json.dumps({"error": f"エンベディングの計算に失敗しました: {str(e)}"}), 500


async def expand_query(request):
    """
    クエリー拡張を実行するCloud Function
    
    Args:
        request: Cloud Functionのリクエスト
        
    Returns:
        拡張クエリーのJSON
    """
    # リクエストからパラメータを取得
    try:
        request_json = request.get_json()
        
        query = request_json.get("query")
        llm_provider = request_json.get("llm_provider")
        
        if not query:
            return json.dumps({"error": "クエリーが指定されていません"}), 400
            
    except Exception as e:
        return json.dumps({"error": f"リクエストの解析に失敗しました: {str(e)}"}), 400
    
    try:
        # レポート生成サービスを取得
        report_service = get_report_generation_service(llm_provider_name=llm_provider)
        
        # クエリー拡張を実行
        sub_queries = await report_service.expand_query(query)
        
        # 結果を整形
        response = {
            "query": query,
            "sub_queries": sub_queries
        }
        
        return json.dumps(response, ensure_ascii=False), 200
        
    except Exception as e:
        return json.dumps({"error": f"クエリー拡張に失敗しました: {str(e)}"}), 500


async def refine_query(request):
    """
    クエリー精緻化を実行するCloud Function
    
    Args:
        request: Cloud Functionのリクエスト
        
    Returns:
        精緻化されたクエリーのJSON
    """
    # リクエストからパラメータを取得
    try:
        request_json = request.get_json()
        
        query = request_json.get("query")
        search_results = request_json.get("search_results", [])
        llm_provider = request_json.get("llm_provider")
        
        if not query:
            return json.dumps({"error": "クエリーが指定されていません"}), 400
            
    except Exception as e:
        return json.dumps({"error": f"リクエストの解析に失敗しました: {str(e)}"}), 400
    
    try:
        # レポート生成サービスを取得
        report_service = get_report_generation_service(llm_provider_name=llm_provider)
        
        # クエリー精緻化を実行
        refined_query = await report_service.refine_query(query, search_results)
        
        # 結果を整形
        response = {
            "original_query": query,
            "refined_query": refined_query
        }
        
        return json.dumps(response, ensure_ascii=False), 200
        
    except Exception as e:
        return json.dumps({"error": f"クエリー精緻化に失敗しました: {str(e)}"}), 500


async def create_outline(request):
    """
    レポートアウトライン作成を実行するCloud Function
    
    Args:
        request: Cloud Functionのリクエスト
        
    Returns:
        アウトラインのJSON
    """
    # リクエストからパラメータを取得
    try:
        request_json = request.get_json()
        
        query = request_json.get("query")
        search_results = request_json.get("search_results", [])
        llm_provider = request_json.get("llm_provider")
        
        if not query:
            return json.dumps({"error": "クエリーが指定されていません"}), 400
            
    except Exception as e:
        return json.dumps({"error": f"リクエストの解析に失敗しました: {str(e)}"}), 400
    
    try:
        # レポート生成サービスを取得
        report_service = get_report_generation_service(llm_provider_name=llm_provider)
        
        # アウトライン作成を実行
        outline = await report_service.create_outline(query, search_results)
        
        # 結果を整形
        response = {
            "query": query,
            "outline": outline
        }
        
        return json.dumps(response, ensure_ascii=False), 200
        
    except Exception as e:
        return json.dumps({"error": f"アウトライン作成に失敗しました: {str(e)}"}), 500


async def create_mindmap(request):
    """
    マインドマップ作成を実行するCloud Function
    
    Args:
        request: Cloud Functionのリクエスト
        
    Returns:
        マインドマップのJSON
    """
    # リクエストからパラメータを取得
    try:
        request_json = request.get_json()
        
        query = request_json.get("query")
        outline = request_json.get("outline", {})
        llm_provider = request_json.get("llm_provider")
        
        if not query or not outline:
            return json.dumps({"error": "クエリーまたはアウトラインが指定されていません"}), 400
            
    except Exception as e:
        return json.dumps({"error": f"リクエストの解析に失敗しました: {str(e)}"}), 400
    
    try:
        # レポート生成サービスを取得
        report_service = get_report_generation_service(llm_provider_name=llm_provider)
        
        # マインドマップ作成を実行
        mindmap = await report_service.create_mindmap(query, outline)
        
        # 結果を整形
        response = {
            "query": query,
            "mindmap": mindmap
        }
        
        return json.dumps(response, ensure_ascii=False), 200
        
    except Exception as e:
        return json.dumps({"error": f"マインドマップ作成に失敗しました: {str(e)}"}), 500


# 以下はストリーミングレスポンスを返す関数（Cloud Run等で利用することを想定）
async def write_report_section(request):
    """
    レポートセクション執筆を実行するCloud Function
    ストリーミングレスポンスを返す
    
    Args:
        request: Cloud Functionのリクエスト
        
    Returns:
        ストリーミングレスポンス
    """
    from flask import Response, stream_with_context
    
    # リクエストからパラメータを取得
    try:
        request_json = request.get_json()
        
        query = request_json.get("query")
        references = request_json.get("references")
        section_outline = request_json.get("section_outline")
        llm_provider = request_json.get("llm_provider")
        
        if not query or not references or not section_outline:
            return json.dumps({"error": "必要なパラメータが指定されていません"}), 400
            
    except Exception as e:
        return json.dumps({"error": f"リクエストの解析に失敗しました: {str(e)}"}), 400
    
    try:
        # レポート生成サービスを取得
        report_service = get_report_generation_service(llm_provider_name=llm_provider)
        
        # ストリーミングジェネレータ
        async def generate():
            async for chunk in report_service.write_report_section(query, references, section_outline):
                yield chunk
        
        # ストリーミングレスポンスを返す
        return Response(stream_with_context(generate()), mimetype='text/plain')
        
    except Exception as e:
        return json.dumps({"error": f"レポートセクション執筆に失敗しました: {str(e)}"}), 500


async def write_report_lead(request):
    """
    レポート導入部執筆を実行するCloud Function
    ストリーミングレスポンスを返す
    
    Args:
        request: Cloud Functionのリクエスト
        
    Returns:
        ストリーミングレスポンス
    """
    from flask import Response, stream_with_context
    
    # リクエストからパラメータを取得
    try:
        request_json = request.get_json()
        
        query = request_json.get("query")
        title = request_json.get("title")
        draft = request_json.get("draft")
        llm_provider = request_json.get("llm_provider")
        
        if not query or not title or not draft:
            return json.dumps({"error": "必要なパラメータが指定されていません"}), 400
            
    except Exception as e:
        return json.dumps({"error": f"リクエストの解析に失敗しました: {str(e)}"}), 400
    
    try:
        # レポート生成サービスを取得
        report_service = get_report_generation_service(llm_provider_name=llm_provider)
        
        # ストリーミングジェネレータ
        async def generate():
            async for chunk in report_service.write_report_lead(query, title, draft):
                yield chunk
        
        # ストリーミングレスポンスを返す
        return Response(stream_with_context(generate()), mimetype='text/plain')
        
    except Exception as e:
        return json.dumps({"error": f"レポート導入部執筆に失敗しました: {str(e)}"}), 500


async def write_report_conclusion(request):
    """
    レポート結論部執筆を実行するCloud Function
    ストリーミングレスポンスを返す
    
    Args:
        request: Cloud Functionのリクエスト
        
    Returns:
        ストリーミングレスポンス
    """
    from flask import Response, stream_with_context
    
    # リクエストからパラメータを取得
    try:
        request_json = request.get_json()
        
        query = request_json.get("query")
        report_draft = request_json.get("report_draft")
        llm_provider = request_json.get("llm_provider")
        
        if not query or not report_draft:
            return json.dumps({"error": "必要なパラメータが指定されていません"}), 400
            
    except Exception as e:
        return json.dumps({"error": f"リクエストの解析に失敗しました: {str(e)}"}), 400
    
    try:
        # レポート生成サービスを取得
        report_service = get_report_generation_service(llm_provider_name=llm_provider)
        
        # ストリーミングジェネレータ
        async def generate():
            async for chunk in report_service.write_report_conclusion(query, report_draft):
                yield chunk
        
        # ストリーミングレスポンスを返す
        return Response(stream_with_context(generate()), mimetype='text/plain')
        
    except Exception as e:
        return json.dumps({"error": f"レポート結論部執筆に失敗しました: {str(e)}"}), 500