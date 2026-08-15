#!/usr/bin/env python3
"""
Test suite for FileCustra Magika File Type Router.
"""

import tempfile
import unittest
from pathlib import Path

from magika_router import (
    MagikaFileRouter,
    FileCategory,
    FileTypeResult,
    create_file_router,
    EXTENSION_TO_CATEGORY,
)


class TestFileCategory(unittest.TestCase):
    """Test file category enum."""
    
    def test_categories_exist(self):
        self.assertEqual(FileCategory.DOCUMENT.value, "document")
        self.assertEqual(FileCategory.CODE.value, "code")
        self.assertEqual(FileCategory.ARCHIVE.value, "archive")
        self.assertEqual(FileCategory.EXECUTABLE.value, "executable")
        self.assertEqual(FileCategory.MEDIA.value, "media")
        self.assertEqual(FileCategory.SYSTEM.value, "system")
        self.assertEqual(FileCategory.DATA.value, "data")
        self.assertEqual(FileCategory.UNKNOWN.value, "unknown")


class TestExtensionMapping(unittest.TestCase):
    """Test extension to category mapping."""
    
    def test_document_extensions(self):
        self.assertEqual(EXTENSION_TO_CATEGORY["pdf"], FileCategory.DOCUMENT)
        self.assertEqual(EXTENSION_TO_CATEGORY["docx"], FileCategory.DOCUMENT)
        self.assertEqual(EXTENSION_TO_CATEGORY["txt"], FileCategory.DOCUMENT)
    
    def test_code_extensions(self):
        self.assertEqual(EXTENSION_TO_CATEGORY["py"], FileCategory.CODE)
        self.assertEqual(EXTENSION_TO_CATEGORY["js"], FileCategory.CODE)
        self.assertEqual(EXTENSION_TO_CATEGORY["rs"], FileCategory.CODE)
    
    def test_archive_extensions(self):
        self.assertEqual(EXTENSION_TO_CATEGORY["zip"], FileCategory.ARCHIVE)
        self.assertEqual(EXTENSION_TO_CATEGORY["rar"], FileCategory.ARCHIVE)
        self.assertEqual(EXTENSION_TO_CATEGORY["7z"], FileCategory.ARCHIVE)
    
    def test_executable_extensions(self):
        self.assertEqual(EXTENSION_TO_CATEGORY["exe"], FileCategory.EXECUTABLE)
        self.assertEqual(EXTENSION_TO_CATEGORY["msi"], FileCategory.EXECUTABLE)
    
    def test_media_extensions(self):
        self.assertEqual(EXTENSION_TO_CATEGORY["png"], FileCategory.MEDIA)
        self.assertEqual(EXTENSION_TO_CATEGORY["mp3"], FileCategory.MEDIA)
        self.assertEqual(EXTENSION_TO_CATEGORY["mp4"], FileCategory.MEDIA)


class TestMagikaFileRouter(unittest.TestCase):
    """Test Magika file router."""
    
    def setUp(self):
        self.router = create_file_router()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_router(self):
        router = create_file_router()
        self.assertIsInstance(router, MagikaFileRouter)
    
    def test_classify_pdf(self):
        pdf_path = Path(self.temp_dir) / "document.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")
        
        result = self.router.classify_file(str(pdf_path))
        
        self.assertIsInstance(result, FileTypeResult)
        self.assertEqual(result.file_name, "document.pdf")
        self.assertEqual(result.extension, "pdf")
        self.assertEqual(result.category, FileCategory.DOCUMENT)
        self.assertEqual(result.risk_level, "safe")
    
    def test_classify_python(self):
        py_path = Path(self.temp_dir) / "script.py"
        py_path.write_text("#!/usr/bin/env python3\nprint('hello')")
        
        result = self.router.classify_file(str(py_path))
        
        self.assertEqual(result.file_name, "script.py")
        self.assertEqual(result.extension, "py")
        self.assertEqual(result.category, FileCategory.CODE)
        self.assertEqual(result.risk_level, "safe")
    
    def test_classify_executable(self):
        exe_path = Path(self.temp_dir) / "malware.exe"
        exe_path.write_bytes(b"MZ\x90\x00" + b"\x00" * 100)
        
        result = self.router.classify_file(str(exe_path))
        
        self.assertEqual(result.file_name, "malware.exe")
        self.assertEqual(result.extension, "exe")
        self.assertEqual(result.risk_level, "high")
    
    def test_classify_archive(self):
        zip_path = Path(self.temp_dir) / "archive.zip"
        zip_path.write_bytes(b"PK\x03\x04" + b"\x00" * 100)
        
        result = self.router.classify_file(str(zip_path))
        
        self.assertEqual(result.file_name, "archive.zip")
        self.assertEqual(result.extension, "zip")
        self.assertEqual(result.category, FileCategory.ARCHIVE)
        self.assertEqual(result.risk_level, "low")
    
    def test_classify_unknown_extension(self):
        unknown_path = Path(self.temp_dir) / "file.xyz"
        unknown_path.write_text("some content")
        
        result = self.router.classify_file(str(unknown_path))
        
        self.assertEqual(result.file_name, "file.xyz")
        self.assertEqual(result.extension, "xyz")
        self.assertIn(result.category, [FileCategory.UNKNOWN, FileCategory.DOCUMENT])
    
    def test_classify_batch(self):
        files = []
        for name in ["doc.pdf", "code.py", "image.png"]:
            path = Path(self.temp_dir) / name
            path.write_bytes(b"test content")
            files.append(str(path))
        
        results = self.router.classify_batch(files)
        
        self.assertEqual(len(results), 3)
        self.assertIsInstance(results[0], FileTypeResult)
    
    def test_get_supported_extensions(self):
        extensions = self.router.get_supported_extensions()
        self.assertIsInstance(extensions, list)
        self.assertIn("pdf", extensions)
        self.assertIn("py", extensions)
        self.assertIn("zip", extensions)
    
    def test_get_extension_mapping(self):
        mapping = self.router.get_extension_mapping()
        self.assertIsInstance(mapping, dict)
        self.assertEqual(mapping["pdf"], "document")
        self.assertEqual(mapping["py"], "code")
    
    def test_risk_levels(self):
        test_cases = [
            ("exe", "high"),
            ("bat", "high"),
            ("dll", "medium"),
            ("zip", "low"),
            ("pdf", "safe"),
            ("py", "safe"),
            ("txt", "safe"),
        ]
        
        for ext, expected_risk in test_cases:
            test_path = Path(self.temp_dir) / f"test.{ext}"
            test_path.write_bytes(b"test content")
            result = self.router.classify_file(str(test_path))
            self.assertEqual(
                result.risk_level, expected_risk,
                f"Expected {expected_risk} risk for .{ext}, got {result.risk_level}"
            )


class TestFileTypeResult(unittest.TestCase):
    """Test FileTypeResult serialization."""
    
    def test_to_dict(self):
        result = FileTypeResult(
            path="/test/file.pdf",
            file_name="file.pdf",
            extension="pdf",
            magika_label="pdf",
            magika_mime="application/pdf",
            magika_confidence=0.99,
            extension_mime="application/pdf",
            category=FileCategory.DOCUMENT,
            risk_level="safe",
        )
        
        d = result.to_dict()
        
        self.assertEqual(d["path"], "/test/file.pdf")
        self.assertEqual(d["file_name"], "file.pdf")
        self.assertEqual(d["extension"], "pdf")
        self.assertEqual(d["category"], "document")
        self.assertEqual(d["risk_level"], "safe")
        self.assertIsNone(d["mismatch_warning"])
    
    def test_to_dict_with_mismatch(self):
        result = FileTypeResult(
            path="/test/fake.txt",
            file_name="fake.txt",
            extension="txt",
            magika_label="pdf",
            magika_mime="application/pdf",
            magika_confidence=0.95,
            extension_mime="text/plain",
            category=FileCategory.DOCUMENT,
            risk_level="safe",
            mismatch_warning="Extension mismatch detected",
        )
        
        d = result.to_dict()
        self.assertEqual(d["mismatch_warning"], "Extension mismatch detected")


if __name__ == "__main__":
    unittest.main()
