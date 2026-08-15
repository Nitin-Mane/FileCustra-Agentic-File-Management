#!/usr/bin/env python3
"""
Test suite for FileCustra EmbeddingGemma Vector Search Subsystem.
"""

import tempfile
import unittest
from pathlib import Path

import numpy as np

from vector_search import (
    EmbeddingGemmaSearch,
    EmbeddingGemmaModel,
    EmbeddingCache,
    VectorStore,
    VectorEntry,
    SearchResult,
    DuplicateCluster,
    SemanticCluster,
    create_vector_search,
)


class TestVectorEntry(unittest.TestCase):
    """Test VectorEntry dataclass."""
    
    def test_to_dict(self):
        entry = VectorEntry(
            id="test-id",
            file_path="/test/file.txt",
            text="Test text content",
            embedding=np.random.randn(300).astype(np.float32),
            metadata={"type": "test"},
        )
        
        d = entry.to_dict()
        
        self.assertEqual(d["id"], "test-id")
        self.assertEqual(d["file_path"], "/test/file.txt")
        self.assertEqual(d["metadata"]["type"], "test")


class TestSearchResult(unittest.TestCase):
    """Test SearchResult dataclass."""
    
    def test_to_dict(self):
        entry = VectorEntry(
            id="test-id",
            file_path="/test/file.txt",
            text="Test text",
            embedding=np.random.randn(300).astype(np.float32),
        )
        result = SearchResult(entry=entry, score=0.95, distance=0.05)
        
        d = result.to_dict()
        
        self.assertEqual(d["score"], 0.95)
        self.assertEqual(d["distance"], 0.05)


class TestDuplicateCluster(unittest.TestCase):
    """Test DuplicateCluster dataclass."""
    
    def test_to_dict(self):
        cluster = DuplicateCluster(
            cluster_id="abc123",
            files=["file1.txt", "file2.txt"],
            similarity_score=0.98,
            representative_text="Representative text content",
        )
        
        d = cluster.to_dict()
        
        self.assertEqual(d["cluster_id"], "abc123")
        self.assertEqual(len(d["files"]), 2)
        self.assertEqual(d["similarity_score"], 0.98)


class TestEmbeddingCache(unittest.TestCase):
    """Test embedding cache."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cache_operations(self):
        cache = EmbeddingCache()
        
        embedding = np.random.randn(300).astype(np.float32)
        cache.set("key1", embedding)
        
        self.assertTrue(cache.has("key1"))
        self.assertEqual(cache.size(), 1)
        
        retrieved = cache.get("key1")
        np.testing.assert_array_equal(retrieved, embedding)
        
        self.assertIsNone(cache.get("nonexistent"))
        
        cache.clear()
        self.assertEqual(cache.size(), 0)
    
    def test_cache_persistence(self):
        cache_path = str(Path(self.temp_dir) / "cache.bin")
        cache = EmbeddingCache(cache_path)
        
        embedding = np.random.randn(300).astype(np.float32)
        cache.set("key1", embedding)
        cache._save_cache()
        
        new_cache = EmbeddingCache(cache_path)
        retrieved = new_cache.get("key1")
        np.testing.assert_array_equal(retrieved, embedding)


class TestVectorStore(unittest.TestCase):
    """Test vector store."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add_and_get_entry(self):
        store = VectorStore(dimension=300)
        
        entry = VectorEntry(
            id="test-id",
            file_path="/test/file.txt",
            text="Test text",
            embedding=np.random.randn(300).astype(np.float32),
        )
        
        store.add_entry(entry)
        self.assertEqual(store.size(), 1)
        
        retrieved = store.get_entry("test-id")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.file_path, "/test/file.txt")
    
    def test_search(self):
        store = VectorStore(dimension=300)
        
        for i in range(5):
            entry = VectorEntry(
                id=f"entry-{i}",
                file_path=f"/test/file{i}.txt",
                text=f"Document {i}",
                embedding=np.random.randn(300).astype(np.float32),
            )
            store.add_entry(entry)
        
        query = np.random.randn(300).astype(np.float32)
        results = store.search(query, top_k=3, threshold=-1.0)
        
        self.assertEqual(len(results), 3)
        self.assertTrue(all(isinstance(r, SearchResult) for r in results))
    
    def test_find_duplicates(self):
        store = VectorStore(dimension=300)
        
        embedding1 = np.random.randn(300).astype(np.float32)
        embedding2 = embedding1 + np.random.randn(300).astype(np.float32) * 0.01
        embedding3 = np.random.randn(300).astype(np.float32)
        
        store.add_entry(VectorEntry(
            id="file1",
            file_path="/test/file1.txt",
            text="Document 1",
            embedding=embedding1,
        ))
        store.add_entry(VectorEntry(
            id="file2",
            file_path="/test/file2.txt",
            text="Document 2",
            embedding=embedding2,
        ))
        store.add_entry(VectorEntry(
            id="file3",
            file_path="/test/file3.txt",
            text="Document 3",
            embedding=embedding3,
        ))
        
        duplicates = store.find_duplicates(threshold=0.99)
        self.assertEqual(len(duplicates), 1)
        self.assertEqual(len(duplicates[0].files), 2)


class TestEmbeddingGemmaModel(unittest.TestCase):
    """Test EmbeddingGemma model."""
    
    def test_model_creation(self):
        model = EmbeddingGemmaModel()
        self.assertIsNotNone(model)
    
    def test_model_load(self):
        model = EmbeddingGemmaModel()
        result = model.load()
        self.assertTrue(result)
    
    def test_encode(self):
        model = EmbeddingGemmaModel()
        model.load()
        
        embedding = model.encode("Test text")
        
        self.assertEqual(embedding.shape, (300,))
        self.assertEqual(embedding.dtype, np.float32)
    
    def test_encode_batch(self):
        model = EmbeddingGemmaModel()
        model.load()
        
        embeddings = model.encode_batch(["Text 1", "Text 2", "Text 3"])
        
        self.assertEqual(embeddings.shape, (3, 300))


class TestEmbeddingGemmaSearch(unittest.TestCase):
    """Test EmbeddingGemma search subsystem."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_search(self):
        search = create_vector_search()
        self.assertIsInstance(search, EmbeddingGemmaSearch)
    
    def test_initialize(self):
        search = create_vector_search()
        result = search.initialize()
        self.assertTrue(result)
    
    def test_add_document(self):
        search = create_vector_search()
        search.initialize()
        
        doc_id = search.add_document(
            "test.txt",
            "This is a test document about machine learning",
        )
        
        self.assertIsNotNone(doc_id)
        self.assertEqual(search.get_stats()["store_size"], 1)
    
    def test_search(self):
        search = create_vector_search()
        search.initialize()
        
        search.add_document("doc1.txt", "Machine learning algorithms")
        search.add_document("doc2.txt", "Deep learning neural networks")
        search.add_document("doc3.txt", "Cooking recipes and food")
        
        results = search.search("machine learning", top_k=2)
        
        self.assertEqual(len(results), 2)
        self.assertTrue(all(isinstance(r, SearchResult) for r in results))
    
    def test_semantic_search(self):
        search = create_vector_search()
        search.initialize()
        
        search.add_document("doc1.txt", "Artificial intelligence and AI")
        search.add_document("doc2.txt", "Natural language processing")
        search.add_document("doc3.txt", "Weather forecasting")
        
        results = search.search("AI technology", top_k=2, threshold=-1.0)
        
        self.assertEqual(len(results), 2)
    
    def test_find_similar_files(self):
        search = create_vector_search()
        search.initialize()
        
        search.add_document("doc1.txt", "Machine learning fundamentals")
        search.add_document("doc2.txt", "Machine learning advanced topics")
        search.add_document("doc3.txt", "Cooking Italian food")
        
        results = search.find_similar_files(
            "doc1.txt",
            "Machine learning fundamentals",
            top_k=2,
        )
        
        self.assertEqual(len(results), 2)
        self.assertNotEqual(results[0].entry.file_path, "doc1.txt")
    
    def test_find_duplicates(self):
        search = create_vector_search()
        search.initialize()
        
        search.add_document("doc1.txt", "The quick brown fox jumps")
        search.add_document("doc2.txt", "The quick brown fox jumps over")
        search.add_document("doc3.txt", "Completely different content about space")
        
        duplicates = search.find_duplicates(threshold=0.9)
        
        self.assertIsInstance(duplicates, list)
    
    def test_get_stats(self):
        search = create_vector_search()
        search.initialize()
        
        stats = search.get_stats()
        
        self.assertIn("model_available", stats)
        self.assertIn("model_dimension", stats)
        self.assertIn("store_size", stats)
        self.assertIn("cache_size", stats)


if __name__ == "__main__":
    unittest.main()
