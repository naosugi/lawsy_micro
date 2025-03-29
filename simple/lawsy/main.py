"""
Cloud Function用のメインエントリーポイント
入力を受け取り、検索からレポート作成までの一連の処理を実行する
"""
import json
import asyncio
from typing import Dict, Any, List, Optional

from lawsy.config import Config
from lawsy.interfaces import SearchResult, DocumentSearchProvider


# ファクトリー関数
def create_search_provider(provider_type: Optional[str] = None):
    """検索プロバイダを作成する"""
    provider_type = provider_type or Config.get("SEARCH_PROVIDER")
    
    if provider_type == "google":
        from lawsy.providers import GoogleSearchProvider
        return GoogleSearchProvider()
    else:
        raise ValueError(f"サポートされていない検索プロバイダです: {provider_type}")


def create_embedding_provider(provider_type: Optional[str] = None):
    """エンベディングプロバイダを作成する"""
    provider_type = provider_type or Config.get("EMBEDDING_PROVIDER")
    
    if provider_type == "openai":
        from lawsy.providers import OpenAIEmbeddingProvider
        return OpenAIEmbeddingProvider()
    else:
        raise ValueError(f"サポートされていないエンベディングプロバイダです: {provider_type}")


def create_llm_provider(provider_type: Optional[str] = None):
    """LLMプロバイダを作成する"""
    provider_type = provider_type or Config.get("LLM_PROVIDER")
    
    if provider_type == "openai":
        from lawsy.providers import OpenAILLMProvider
        return OpenAILLMProvider()
    else:
        raise ValueError(f"サポートされていないLLMプロバイダです: {provider_type}")


def create_document_search_provider(config: Dict[str, Any]) -> DocumentSearchProvider:
    """
    ドキュメント検索プロバイダを作成する
    
    Args:
        config: プロバイダ設定
        
    Returns:
        ドキュメント検索プロバイダ
    """
    provider_type = config.get("document_search_provider", Config.get("DOCUMENT_SEARCH_PROVIDER", "faiss"))
    
    if provider_type == "faiss":
        from lawsy.services import VectorSearchService
        return VectorSearchService(embedding_provider=create_embedding_provider())
        
    elif provider_type == "opensearch":
        from lawsy.providers import OpenSearchProvider
        opensearch_config = config.get("opensearch", {})
        return OpenSearchProvider(
            endpoint=opensearch_config.get("endpoint"),
            index=opensearch_config.get("index"),
            username=opensearch_config.get("username"),
            password=opensearch_config.get("password"),
            auth_type=opensearch_config.get("auth_type", "basic"),
            embedding_provider=create_embedding_provider() if opensearch_config.get("use_vector_search", True) else None
        )
        
    elif provider_type == "vertex_ai_search":
        from lawsy.providers import VertexAISearchProvider
        vertex_config = config.get("vertex_ai_search", {})
        return VertexAISearchProvider(
            project_id=vertex_config.get("project_id"),
            location=vertex_config.get("location"),
            data_store_id=vertex_config.get("data_store_id")
        )
        
    else:
        raise ValueError(f"サポートされていないドキュメント検索プロバイダです: {provider_type}")


def create_report_service():
    """レポート生成サービスを作成する"""
    llm_provider = create_llm_provider()
    from lawsy.services import ReportService
    return ReportService(llm_provider=llm_provider)


# メインのCloud Function
async def process_request(request):
    """
    リクエストを処理するメイン関数
    検索からレポート作成までの一連の処理を実行する
    
    Args:
        request: リクエスト
        
    Returns:
        処理結果のJSON
    """
    # リクエスト解析
    try:
        request_json = request.get_json()
        
        # 操作タイプの取得
        operation = request_json.get("operation")
        if not operation:
            return json.dumps({"error": "操作タイプが指定されていません"}), 400
            
        # クエリの取得
        query = request_json.get("query")
        if not query:
            return json.dumps({"error": "検索クエリが指定されていません"}), 400
            
        # 設定の取得
        config = request_json.get("config", {})
        
    except Exception as e:
        return json.dumps({"error": f"リクエストの解析に失敗しました: {str(e)}"}), 400
    
    try:
        # 操作タイプに応じた処理
        if operation == "web_search":
            # Web検索を実行
            return await web_search(query, config)
            
        elif operation == "document_search":
            # ドキュメント検索を実行
            return await document_search(query, config)
            
        elif operation == "generate_report":
            # レポート生成を実行
            return await generate_report(query, config)
            
        elif operation == "deep_research":
            # DeepResearch（検索からレポート生成までの一連の処理）を実行
            return await deep_research(query, config)
            
        else:
            return json.dumps({"error": f"サポートされていない操作タイプです: {operation}"}), 400
            
    except Exception as e:
        return json.dumps({"error": f"処理に失敗しました: {str(e)}"}), 500


async def web_search(query: str, config: Dict[str, Any]):
    """
    Web検索を実行する
    
    Args:
        query: 検索クエリ
        config: 設定
        
    Returns:
        検索結果のJSON
    """
    provider_type = config.get("search_provider")
    limit = config.get("limit", 10)
    domains = config.get("domains", [])
    language = config.get("language", "ja")
    
    # 検索プロバイダを作成
    search_provider = create_search_provider(provider_type)
    
    # 検索を実行
    results = search_provider.search(
        query=query,
        limit=limit,
        filters={
            "domains": domains,
            "language": language
        }
    )
    
    # 結果を整形
    response = {
        "query": query,
        "results": [result.to_dict() for result in results]
    }
    
    return json.dumps(response, ensure_ascii=False), 200


async def document_search(query: str, config: Dict[str, Any]):
    """
    ドキュメント検索を実行する
    
    Args:
        query: 検索クエリ
        config: 設定
        
    Returns:
        検索結果のJSON
    """
    limit = config.get("limit", 10)
    filters = config.get("filters")
    
    # ドキュメント検索プロバイダを作成
    document_search_provider = create_document_search_provider(config)
    
    # 検索を実行
    results = document_search_provider.search(
        query=query,
        limit=limit,
        filters=filters
    )
    
    # 結果を整形
    response = {
        "query": query,
        "results": [result.to_dict() for result in results]
    }
    
    return json.dumps(response, ensure_ascii=False), 200


async def generate_report(query: str, config: Dict[str, Any]):
    """
    レポート生成を実行する
    
    Args:
        query: 検索クエリ
        config: 設定
        
    Returns:
        レポートのJSON
    """
    search_results_data = config.get("search_results", [])
    
    # 検索結果をオブジェクトに変換
    search_results = [
        SearchResult(
            title=result.get("title", ""),
            content=result.get("content", ""),
            url=result.get("url", ""),
            score=result.get("score", 0.0),
            metadata=result.get("metadata", {})
        )
        for result in search_results_data
    ]
    
    # レポート生成サービスを作成
    report_service = create_report_service()
    
    # アウトラインを作成
    outline = await report_service.create_outline(query, search_results)
    
    # レポートセクションを生成（アウトラインの中身だけ返す場合）
    # 実際のレポート生成はストリーミングで行うため、ここではアウトラインのみ返す
    response = {
        "query": query,
        "outline": outline
    }
    
    return json.dumps(response, ensure_ascii=False), 200


async def deep_research(query: str, config: Dict[str, Any]):
    """
    DeepResearch（検索からレポート生成までの一連の処理）を実行する
    
    Args:
        query: 検索クエリ
        config: 設定
        
    Returns:
        処理結果のJSON
    """
    # 設定を取得
    search_provider_type = config.get("search_provider")
    limit = config.get("limit", 20)
    domains = config.get("domains", [])
    language = config.get("language", "ja")
    
    # レポート生成サービスを作成
    report_service = create_report_service()
    
    # 1. クエリ拡張を実行
    sub_queries = await report_service.expand_query(query)
    
    # 全ての検索結果を格納するリスト
    all_results = []
    
    # 2. 元のクエリでWeb検索を実行
    search_provider = create_search_provider(search_provider_type)
    original_web_results = search_provider.search(
        query=query,
        limit=limit,
        filters={
            "domains": domains,
            "language": language
        }
    )
    all_results.extend(original_web_results)
    
    # 3. 拡張クエリでWeb検索を実行（オプション）
    expanded_web_results = []
    if config.get("use_expanded_queries", True):
        for sub_query in sub_queries[:2]:  # 最初の2つだけ使用して効率化
            sub_results = search_provider.search(
                query=sub_query,
                limit=limit // 2,  # 各サブクエリの結果数を制限
                filters={
                    "domains": domains,
                    "language": language
                }
            )
            expanded_web_results.extend(sub_results)
        all_results.extend(expanded_web_results)
    
    # 4. ドキュメント検索を実行（設定されている場合）
    document_results = []
    if config.get("use_document_search", False):
        document_search_provider = create_document_search_provider(config)
        
        # 元のクエリでドキュメント検索
        document_results = document_search_provider.search(
            query=query,
            limit=limit,
            filters=config.get("document_filters")
        )
        all_results.extend(document_results)
        
        # 拡張クエリでもドキュメント検索（オプション）
        if config.get("use_expanded_document_queries", False):
            for sub_query in sub_queries[:1]:  # 最初の1つだけ使用
                sub_document_results = document_search_provider.search(
                    query=sub_query,
                    limit=limit // 2,
                    filters=config.get("document_filters")
                )
                document_results.extend(sub_document_results)
                all_results.extend(sub_document_results)
    
    # 5. アウトラインを作成
    outline = await report_service.create_outline(query, all_results)
    
    # 6. 結果を整形
    response = {
        "query": query,
        "sub_queries": sub_queries,
        "web_results": {
            "original": [result.to_dict() for result in original_web_results],
            "expanded": [result.to_dict() for result in expanded_web_results]
        },
        "document_results": [result.to_dict() for result in document_results],
        "all_results": [result.to_dict() for result in all_results],
        "outline": outline
    }
    
    return json.dumps(response, ensure_ascii=False), 200