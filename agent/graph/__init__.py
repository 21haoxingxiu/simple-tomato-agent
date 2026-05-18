"""GraphRAG (Neo4j) 可选适配。通过 ENABLE_GRAPHRAG=true 启用。"""
from graph.graphrag import get_graph_store

__all__ = ["get_graph_store"]
