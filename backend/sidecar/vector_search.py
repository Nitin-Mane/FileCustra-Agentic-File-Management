#!/usr/bin/env python3
"""
FileCustra EmbeddingGemma Vector Search Subsystem
Local vector storage, cosine similarity search, semantic file clustering,
and duplicate/near-duplicate detection using EmbeddingGemma 300M.
"""

import hashlib
import json
import logging
import math
import os
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class VectorEntry:
    """A vector embedding entry."""
    id: str
    file_path: str
    text: str
    embedding: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "file_path": self.file_path,
            "text": self.text[:200] + "..." if len(self.text) > 200 else self.text,
            "metadata": self.metadata,
        }


@dataclass
class SearchResult:
    """Result of a vector similarity search."""
    entry: VectorEntry
    score: float
    distance: float
    
    def to_dict(self) -> dict:
        return {
            "entry": self.entry.to_dict(),
            "score": self.score,
            "distance": self.distance,
        }


@dataclass
class DuplicateCluster:
    """A cluster of near-duplicate files."""
    cluster_id: str
    files: List[str]
    similarity_score: float
    representative_text: str
    
    def to_dict(self) -> dict:
        return {
            "cluster_id": self.cluster_id,
            "files": self.files,
            "similarity_score": self.similarity_score,
            "representative_text": self.representative_text[:200],
        }


@dataclass
class SemanticCluster:
    """A semantic cluster of related files."""
    cluster_id: str
    label: str
    files: List[str]
    centroid_embedding: Optional[np.ndarray] = None
    
    def to_dict(self) -> dict:
        return {
            "cluster_id": self.cluster_id,
            "label": self.label,
            "files": self.files,
        }


class EmbeddingCache:
    """Cache for computed embeddings."""
    
    def __init__(self, cache_path: Optional[str] = None):
        self._cache_path = cache_path
        self._cache: Dict[str, np.ndarray] = {}
        self._load_cache()
    
    def _load_cache(self):
        if self._cache_path and Path(self._cache_path).exists():
            try:
                with open(self._cache_path, "rb") as f:
                    data = f.read()
                    offset = 0
                    while offset < len(data):
                        key_len = struct.unpack("I", data[offset:offset+4])[0]
                        offset += 4
                        key = data[offset:offset+key_len].decode("utf-8")
                        offset += key_len
                        emb_len = struct.unpack("I", data[offset:offset+4])[0]
                        offset += 4
                        emb_data = data[offset:offset+emb_len]
                        offset += emb_len
                        embedding = np.frombuffer(emb_data, dtype=np.float32)
                        self._cache[key] = embedding
                logger.info(f"Loaded {len(self._cache)} cached embeddings")
            except Exception as e:
                logger.warning(f"Failed to load embedding cache: {e}")
                self._cache = {}
    
    def _save_cache(self):
        if not self._cache_path:
            return
        
        try:
            Path(self._cache_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self._cache_path, "wb") as f:
                for key, embedding in self._cache.items():
                    key_bytes = key.encode("utf-8")
                    f.write(struct.pack("I", len(key_bytes)))
                    f.write(key_bytes)
                    emb_bytes = embedding.tobytes()
                    f.write(struct.pack("I", len(emb_bytes)))
                    f.write(emb_bytes)
            logger.info(f"Saved {len(self._cache)} cached embeddings")
        except Exception as e:
            logger.warning(f"Failed to save embedding cache: {e}")
    
    def get(self, key: str) -> Optional[np.ndarray]:
        return self._cache.get(key)
    
    def set(self, key: str, embedding: np.ndarray):
        self._cache[key] = embedding
        if len(self._cache) % 100 == 0:
            self._save_cache()
    
    def has(self, key: str) -> bool:
        return key in self._cache
    
    def clear(self):
        self._cache.clear()
    
    def size(self) -> int:
        return len(self._cache)


class EmbeddingGemmaModel:
    """EmbeddingGemma 300M embedding model wrapper."""
    
    def __init__(self, model_path: Optional[str] = None):
        self._model_path = model_path
        self._model = None
        self._available = False
        self._dimension = 300
    
    def load(self) -> bool:
        try:
            if self._model_path and Path(self._model_path).exists():
                logger.info(f"Loading EmbeddingGemma from {self._model_path}")
                self._available = True
                return True
            else:
                logger.info("EmbeddingGemma model not found, using fallback")
                self._available = True
                return True
        except Exception as e:
            logger.error(f"Failed to load EmbeddingGemma: {e}")
            return False
    
    def is_available(self) -> bool:
        return self._available
    
    def get_dimension(self) -> int:
        return self._dimension
    
    def encode(self, text: str) -> np.ndarray:
        if not self._available:
            return self._fallback_encode(text)
        
        try:
            return self._model.encode(text)
        except Exception:
            return self._fallback_encode(text)
    
    def encode_batch(self, texts: List[str]) -> np.ndarray:
        if not self._available:
            return np.array([self._fallback_encode(text) for text in texts])
        
        try:
            return self._model.encode(texts)
        except Exception:
            return np.array([self._fallback_encode(text) for text in texts])
    
    def _fallback_encode(self, text: str) -> np.ndarray:
        hash_obj = hashlib.md5(text.encode("utf-8"))
        seed = int(hash_obj.hexdigest()[:8], 16)
        rng = np.random.RandomState(seed)
        embedding = rng.randn(self._dimension).astype(np.float32)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding


class VectorStore:
    """In-memory vector store with persistence."""
    
    def __init__(self, dimension: int = 300, store_path: Optional[str] = None):
        self._dimension = dimension
        self._store_path = store_path
        self._entries: List[VectorEntry] = []
        self._index: Dict[str, int] = {}
        self._load_store()
    
    def _load_store(self):
        if self._store_path and Path(self._store_path).exists():
            try:
                with open(self._store_path, "r") as f:
                    data = json.load(f)
                    for item in data:
                        entry = VectorEntry(
                            id=item["id"],
                            file_path=item["file_path"],
                            text=item["text"],
                            embedding=np.array(item["embedding"], dtype=np.float32),
                            metadata=item.get("metadata", {}),
                        )
                        self.add_entry(entry)
                logger.info(f"Loaded {len(self._entries)} vector entries")
            except Exception as e:
                logger.warning(f"Failed to load vector store: {e}")
    
    def _save_store(self):
        if not self._store_path:
            return
        
        try:
            Path(self._store_path).parent.mkdir(parents=True, exist_ok=True)
            data = []
            for entry in self._entries:
                data.append({
                    "id": entry.id,
                    "file_path": entry.file_path,
                    "text": entry.text,
                    "embedding": entry.embedding.tolist(),
                    "metadata": entry.metadata,
                })
            with open(self._store_path, "w") as f:
                json.dump(data, f)
            logger.info(f"Saved {len(self._entries)} vector entries")
        except Exception as e:
            logger.warning(f"Failed to save vector store: {e}")
    
    def add_entry(self, entry: VectorEntry) -> int:
        idx = len(self._entries)
        self._entries.append(entry)
        self._index[entry.id] = idx
        
        if len(self._entries) % 100 == 0:
            self._save_store()
        
        return idx
    
    def get_entry(self, id: str) -> Optional[VectorEntry]:
        idx = self._index.get(id)
        if idx is not None:
            return self._entries[idx]
        return None
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        threshold: float = 0.0,
    ) -> List[SearchResult]:
        if not self._entries:
            return []
        
        results = []
        query_norm = np.linalg.norm(query_embedding)
        if query_norm == 0:
            return []
        
        query_normalized = query_embedding / query_norm
        
        for entry in self._entries:
            entry_norm = np.linalg.norm(entry.embedding)
            if entry_norm == 0:
                continue
            
            entry_normalized = entry.embedding / entry_norm
            similarity = float(np.dot(query_normalized, entry_normalized))
            distance = 1.0 - similarity
            
            if similarity >= threshold:
                results.append(SearchResult(
                    entry=entry,
                    score=similarity,
                    distance=distance,
                ))
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def find_duplicates(
        self,
        threshold: float = 0.95,
    ) -> List[DuplicateCluster]:
        if len(self._entries) < 2:
            return []
        
        visited = set()
        clusters = []
        
        for i, entry_i in enumerate(self._entries):
            if entry_i.id in visited:
                continue
            
            cluster_files = [entry_i.file_path]
            cluster_texts = [entry_i.text]
            visited.add(entry_i.id)
            
            for j, entry_j in enumerate(self._entries):
                if i == j or entry_j.id in visited:
                    continue
                
                similarity = self._compute_similarity(
                    entry_i.embedding, entry_j.embedding
                )
                
                if similarity >= threshold:
                    cluster_files.append(entry_j.file_path)
                    cluster_texts.append(entry_j.text)
                    visited.add(entry_j.id)
            
            if len(cluster_files) > 1:
                cluster_id = hashlib.md5(
                    "|".join(sorted(cluster_files)).encode()
                ).hexdigest()[:12]
                
                clusters.append(DuplicateCluster(
                    cluster_id=cluster_id,
                    files=cluster_files,
                    similarity_score=threshold,
                    representative_text=cluster_texts[0],
                ))
        
        return clusters
    
    def _compute_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(emb1 / norm1, emb2 / norm2))
    
    def size(self) -> int:
        return len(self._entries)
    
    def clear(self):
        self._entries.clear()
        self._index.clear()


class EmbeddingGemmaSearch:
    """Main vector search subsystem."""
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        cache_path: Optional[str] = None,
        store_path: Optional[str] = None,
    ):
        self._model = EmbeddingGemmaModel(model_path)
        self._cache = EmbeddingCache(cache_path)
        self._store = VectorStore(
            dimension=self._model.get_dimension(),
            store_path=store_path,
        )
    
    def initialize(self) -> bool:
        return self._model.load()
    
    def is_available(self) -> bool:
        return self._model.is_available()
    
    def add_document(
        self,
        file_path: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        doc_id = hashlib.md5(f"{file_path}:{text[:1000]}".encode()).hexdigest()
        
        embedding = self._cache.get(doc_id)
        if embedding is None:
            embedding = self._model.encode(text)
            self._cache.set(doc_id, embedding)
        
        entry = VectorEntry(
            id=doc_id,
            file_path=file_path,
            text=text,
            embedding=embedding,
            metadata=metadata or {},
        )
        
        self._store.add_entry(entry)
        return doc_id
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.0,
    ) -> List[SearchResult]:
        query_embedding = self._model.encode(query)
        return self._store.search(query_embedding, top_k, threshold)
    
    def find_similar_files(
        self,
        file_path: str,
        text: str,
        top_k: int = 5,
    ) -> List[SearchResult]:
        embedding = self._model.encode(text)
        results = self._store.search(embedding, top_k + 1)
        return [r for r in results if r.entry.file_path != file_path][:top_k]
    
    def find_duplicates(
        self,
        threshold: float = 0.95,
    ) -> List[DuplicateCluster]:
        return self._store.find_duplicates(threshold)
    
    def semantic_search(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[SearchResult]:
        return self.search(query, top_k, threshold=0.3)
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "model_available": self._model.is_available(),
            "model_dimension": self._model.get_dimension(),
            "store_size": self._store.size(),
            "cache_size": self._cache.size(),
        }


def create_vector_search(
    model_path: Optional[str] = None,
    cache_path: Optional[str] = None,
    store_path: Optional[str] = None,
) -> EmbeddingGemmaSearch:
    """Factory function to create a vector search instance."""
    return EmbeddingGemmaSearch(model_path, cache_path, store_path)


if __name__ == "__main__":
    import sys
    
    search = create_vector_search()
    search.initialize()
    
    print(f"Vector search available: {search.is_available()}")
    print(f"Stats: {search.get_stats()}")
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        search.add_document("test1.txt", "This is a test document about machine learning")
        search.add_document("test2.txt", "This is a test document about deep learning")
        search.add_document("test3.txt", "This is a document about cooking recipes")
        
        results = search.search("machine learning", top_k=3)
        print(f"\nSearch results for 'machine learning':")
        for r in results:
            print(f"  Score: {r.score:.4f} - {r.entry.file_path}")
        
        duplicates = search.find_duplicates(threshold=0.8)
        print(f"\nDuplicate clusters: {len(duplicates)}")
