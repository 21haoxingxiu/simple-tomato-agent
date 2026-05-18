"""GraphRAG:
- 以 Neo4j 为存储,使用 LLM 抽取 (实体, 关系, 实体) 三元组
- ingest:为每个 chunk 抽取实体并落图;chunk 与实体之间建立 MENTIONS 关系
- search:对 query 抽取实体后,从图中扩展邻居,反查相关 chunk_id

未启用 Neo4j 时所有方法静默返回。
"""
from __future__ import annotations

import os
import json
import logging
import re
from functools import lru_cache
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _enabled() -> bool:
    return os.getenv("ENABLE_GRAPHRAG", "false").lower() == "true" and bool(
        os.getenv("NEO4J_URI")
    )


_ENTITY_EXTRACT_PROMPT = """你是一个信息抽取助手。请从下面的文本中抽取关键实体与关系,以 JSON 返回。
- 实体类型示例:人物/组织/产品/概念/技术/事件
- 输出严格 JSON,字段为 entities(数组,每项 {name,type}) 与 relations(数组,每项 {source,relation,target})
- 仅返回 JSON,不要解释

文本:
\"\"\"{text}\"\"\"
"""


@lru_cache(maxsize=1)
def _llm():
    from llm import get_chat_model

    return get_chat_model(temperature=0.0)


async def _extract_entities(text: str) -> dict[str, Any]:
    text = text.strip()[:1500]
    if not text:
        return {"entities": [], "relations": []}
    try:
        llm = _llm()
        resp = await llm.ainvoke(_ENTITY_EXTRACT_PROMPT.format(text=text))
        raw = resp.content if hasattr(resp, "content") else str(resp)
        match = re.search(r"\{.*\}", raw, re.S)
        if not match:
            return {"entities": [], "relations": []}
        data = json.loads(match.group(0))
        return {
            "entities": data.get("entities", []) or [],
            "relations": data.get("relations", []) or [],
        }
    except Exception as exc:
        logger.warning("entity extract failed: %s", exc)
        return {"entities": [], "relations": []}


class Neo4jGraphStore:
    def __init__(self) -> None:
        from neo4j import AsyncGraphDatabase  # type: ignore

        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "neo4j_pass")
        self.driver = AsyncGraphDatabase.driver(self.uri, auth=(self.user, self.password))

    async def close(self) -> None:
        await self.driver.close()

    async def ingest_chunks(self, workspace_id: str, kb_id: str, chunks: list[dict]) -> int:
        cnt = 0
        async with self.driver.session() as session:
            for c in chunks:
                extracted = await _extract_entities(c["content"])
                entities = extracted["entities"]
                relations = extracted["relations"]
                cid = c["id"]
                # Chunk 节点
                await session.run(
                    "MERGE (c:Chunk {id: $cid}) "
                    "SET c.workspace_id=$ws, c.kb_id=$kb, c.document_id=$did, c.filename=$fn",
                    cid=cid,
                    ws=workspace_id,
                    kb=kb_id,
                    did=c.get("metadata", {}).get("document_id", ""),
                    fn=c.get("metadata", {}).get("filename", ""),
                )
                # 实体 + MENTIONS
                for ent in entities:
                    name = (ent.get("name") or "").strip()
                    if not name:
                        continue
                    ent_type = (ent.get("type") or "Entity").strip()
                    await session.run(
                        "MERGE (e:Entity {name: $name, workspace_id: $ws, kb_id: $kb}) "
                        "SET e.type=$type "
                        "WITH e MATCH (c:Chunk {id: $cid}) MERGE (c)-[:MENTIONS]->(e)",
                        name=name,
                        type=ent_type,
                        ws=workspace_id,
                        kb=kb_id,
                        cid=cid,
                    )
                # 关系
                for rel in relations:
                    s = (rel.get("source") or "").strip()
                    t = (rel.get("target") or "").strip()
                    r = (rel.get("relation") or "RELATED").strip().upper()
                    r = re.sub(r"[^A-Z0-9_]", "_", r) or "RELATED"
                    if not s or not t:
                        continue
                    await session.run(
                        f"MERGE (a:Entity {{name:$s, workspace_id:$ws, kb_id:$kb}}) "
                        f"MERGE (b:Entity {{name:$t, workspace_id:$ws, kb_id:$kb}}) "
                        f"MERGE (a)-[:{r}]->(b)",
                        s=s,
                        t=t,
                        ws=workspace_id,
                        kb=kb_id,
                    )
                cnt += 1
        return cnt

    async def search(
        self, workspace_id: str, kb_id: str, query: str, k: int = 8
    ) -> list[tuple[str, float, dict]]:
        extracted = await _extract_entities(query)
        names = list({(e.get("name") or "").strip() for e in extracted["entities"] if e.get("name")})
        if not names:
            return []
        async with self.driver.session() as session:
            res = await session.run(
                """
                UNWIND $names AS n
                MATCH (e:Entity {workspace_id:$ws, kb_id:$kb})
                WHERE toLower(e.name) CONTAINS toLower(n)
                MATCH (c:Chunk)-[:MENTIONS]->(e)
                WITH c, count(DISTINCT e) AS hits
                ORDER BY hits DESC
                LIMIT $k
                RETURN c.id AS chunk_id, c.filename AS filename, hits
                """,
                names=names,
                ws=workspace_id,
                kb=kb_id,
                k=k,
            )
            rows = await res.data()
        if not rows:
            return []
        max_hits = max(r["hits"] for r in rows) or 1
        return [
            (
                r["chunk_id"],
                float(r["hits"]) / max_hits,
                {"filename": r["filename"], "via": "graph"},
            )
            for r in rows
        ]


_singleton: Optional[Neo4jGraphStore] = None
_init_failed = False


def get_graph_store() -> Optional[Neo4jGraphStore]:
    global _singleton, _init_failed
    if _init_failed:
        return None
    if not _enabled():
        return None
    if _singleton is not None:
        return _singleton
    try:
        _singleton = Neo4jGraphStore()
        logger.info("GraphRAG enabled — Neo4j connected")
        return _singleton
    except Exception as exc:
        _init_failed = True
        logger.warning("Neo4j init failed (%s) — GraphRAG disabled this session", exc)
        return None
