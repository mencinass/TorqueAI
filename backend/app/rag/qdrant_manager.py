"""Qdrant vector database manager for the automotive RAG pipeline.

Handles collection lifecycle and batch upsert of :class:`DocumentChunk`
embeddings.  All Qdrant operations use the official ``qdrant-client``
Python SDK (pure Python transport).

Usage::

    manager = QdrantManager()
    await manager.ensure_collection()
    await manager.batch_upsert_chunks(chunks, embeddings)
"""

from __future__ import annotations

import uuid
from typing import Any, List, Optional

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdrant_models

from app.core.config import settings
from app.core.logging import get_logger
from app.rag.chunker import DocumentChunk

logger = get_logger(__name__)

# Payload fields that need keyword / integer indexes for filtered search
_KEYWORD_INDEXES = [
    "generation_code",
    "system",
    "document_type",
    "document_id",
]
_INTEGER_INDEXES = [
    "page_number",
]


class QdrantManager:
    """Manages the ``automotive_manuals`` Qdrant collection.

    Creates and validates the collection and its payload indexes on startup,
    then exposes a single :meth:`batch_upsert_chunks` method used by the
    ingestion pipeline.
    """

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        api_key: str | None = None,
        collection: str | None = None,
        dim: int | None = None,
    ) -> None:
        self._host = host or settings.QDRANT_HOST
        self._port = port or settings.QDRANT_PORT
        self._api_key = api_key or settings.QDRANT_API_KEY
        self._collection = collection or settings.QDRANT_COLLECTION
        self._dim = dim or settings.EMBEDDING_DIM

    def _client(self) -> AsyncQdrantClient:
        """Create a fresh async Qdrant client."""
        return AsyncQdrantClient(
            host=self._host,
            port=self._port,
            api_key=self._api_key,
            prefer_grpc=False,
        )

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    async def ensure_collection(self) -> None:
        """Create the collection and payload indexes if they don't exist.

        Idempotent: safe to call on every startup.
        """
        client = self._client()
        try:
            collections = await client.get_collections()
            existing = {c.name for c in collections.collections}
            if self._collection not in existing:
                await client.create_collection(
                    collection_name=self._collection,
                    vectors_config=qdrant_models.VectorParams(
                        size=self._dim,
                        distance=qdrant_models.Distance.COSINE,
                    ),
                )
                logger.info(
                    "qdrant_collection_created",
                    extra={"collection": self._collection, "dim": self._dim},
                )
            else:
                logger.debug(
                    "qdrant_collection_exists",
                    extra={"collection": self._collection},
                )

            # Ensure payload indexes (idempotent — Qdrant silently skips duplicates)
            for field in _KEYWORD_INDEXES:
                await client.create_payload_index(
                    collection_name=self._collection,
                    field_name=field,
                    field_schema=qdrant_models.PayloadSchemaType.KEYWORD,
                )
            for field in _INTEGER_INDEXES:
                await client.create_payload_index(
                    collection_name=self._collection,
                    field_name=field,
                    field_schema=qdrant_models.PayloadSchemaType.INTEGER,
                )
            logger.info(
                "qdrant_indexes_ensured",
                extra={
                    "collection": self._collection,
                    "keyword": _KEYWORD_INDEXES,
                    "integer": _INTEGER_INDEXES,
                },
            )
        finally:
            await client.close()

    # ------------------------------------------------------------------
    # Upsert
    # ------------------------------------------------------------------

    async def batch_upsert_chunks(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]],
        batch_size: int = 64,
    ) -> int:
        """Upsert a list of chunks with their corresponding embedding vectors.

        Args:
            chunks: Document chunks produced by :class:`AutomotiveChunker`.
            embeddings: Embedding vectors — must have the same length as *chunks*.
            batch_size: How many points to send per Qdrant request.

        Returns:
            Total number of points upserted.

        Raises:
            ValueError: If *chunks* and *embeddings* have different lengths.
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"chunks/embeddings length mismatch: {len(chunks)} vs {len(embeddings)}"
            )
        if not chunks:
            return 0

        total = 0
        client = self._client()
        try:
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i : i + batch_size]
                batch_vecs = embeddings[i : i + batch_size]

                points = [
                    qdrant_models.PointStruct(
                        id=str(uuid.UUID(chunk.chunk_id)),
                        vector=vec,
                        payload=chunk.to_payload(),
                    )
                    for chunk, vec in zip(batch_chunks, batch_vecs)
                ]
                await client.upsert(
                    collection_name=self._collection,
                    points=points,
                    wait=True,
                )
                total += len(points)
                logger.debug(
                    "qdrant_batch_upserted",
                    extra={
                        "collection": self._collection,
                        "batch": i // batch_size + 1,
                        "points": len(points),
                        "total_so_far": total,
                    },
                )

            logger.info(
                "qdrant_upsert_complete",
                extra={"collection": self._collection, "total_points": total},
            )
        finally:
            await client.close()
        return total

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def collection_info(self) -> dict:
        """Return basic info about the collection (points count, status)."""
        client = self._client()
        try:
            info = await client.get_collection(self._collection)
            return {
                "name": self._collection,
                "status": info.status.value if info.status else "unknown",
                "points_count": info.points_count or 0,
                "vectors_count": getattr(info, "vectors_count", 0) or 0,
                "dim": self._dim,
            }
        finally:
            await client.close()

    async def search_chunks(
        self,
        vector: List[float],
        generation_code: Optional[str] = None,
        system: Optional[str] = None,
        limit: int = 5,
    ) -> List[Any]:
        """Search indexed manual chunks with optional automotive filters."""
        conditions = []
        if generation_code:
            conditions.append(
                qdrant_models.FieldCondition(
                    key="generation_code",
                    match=qdrant_models.MatchValue(value=generation_code),
                )
            )
        if system:
            conditions.append(
                qdrant_models.FieldCondition(
                    key="system",
                    match=qdrant_models.MatchValue(value=system.lower()),
                )
            )

        query_filter = qdrant_models.Filter(must=conditions) if conditions else None
        client = self._client()
        try:
            collections = await client.get_collections()
            if self._collection not in {item.name for item in collections.collections}:
                logger.info(
                    "qdrant_collection_not_ready",
                    extra={"collection": self._collection},
                )
                return []
            response = await client.query_points(
                collection_name=self._collection,
                query=vector,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
            )
            return response.points
        finally:
            await client.close()

    async def delete_by_document(self, document_id: int) -> int:
        """Delete all points belonging to *document_id*.

        Useful for re-ingestion without duplicates.

        Returns:
            Number of points deleted (estimated from Qdrant operation result).
        """
        client = self._client()
        try:
            result = await client.delete(
                collection_name=self._collection,
                points_selector=qdrant_models.FilterSelector(
                    filter=qdrant_models.Filter(
                        must=[
                            qdrant_models.FieldCondition(
                                key="document_id",
                                match=qdrant_models.MatchValue(value=document_id),
                            )
                        ]
                    )
                ),
                wait=True,
            )
            deleted = getattr(result, "deleted", 0) or 0
            logger.info(
                "qdrant_document_deleted",
                extra={"document_id": document_id, "deleted": deleted},
            )
            return deleted
        finally:
            await client.close()
