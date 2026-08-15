#!/usr/bin/env python3
"""
Test suite for FileCustra Tesseract OCR Subsystem.
"""

import tempfile
import unittest
from pathlib import Path

from ocr_subsystem import (
    TesseractOCR,
    OCRResult,
    ImagePreprocessor,
    create_ocr_engine,
)


class TestOCRResult(unittest.TestCase):
    """Test OCRResult dataclass."""
    
    def test_to_dict(self):
        result = OCRResult(
            file_path="/test/image.png",
            success=True,
            text="Hello world",
            language="eng",
            confidence=85.0,
            page_count=1,
            preprocessing_applied=["grayscale", "sharpening"],
        )
        
        d = result.to_dict()
        
        self.assertEqual(d["file_path"], "/test/image.png")
        self.assertTrue(d["success"])
        self.assertEqual(d["text"], "Hello world")
        self.assertEqual(d["language"], "eng")
        self.assertEqual(d["confidence"], 85.0)
        self.assertEqual(d["page_count"], 1)
        self.assertEqual(d["preprocessing_applied"], ["grayscale", "sharpening"])


class TestImagePreprocessor(unittest.TestCase):
    """Test image preprocessing."""
    
    def setUp(self):
        self.preprocessor = ImagePreprocessor()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_preprocess_image(self):
        try:
            from PIL import Image
            
            img_path = Path(self.temp_dir) / "test.png"
            img = Image.new("RGB", (100, 100), color="gray")
            img.save(str(img_path))
            
            output_path = str(Path(self.temp_dir) / "processed.png")
            result_path, applied = self.preprocessor.preprocess(
                str(img_path), output_path
            )
            
            self.assertTrue(Path(result_path).exists())
            self.assertIn("grayscale_conversion", applied)
            self.assertIn("sharpening", applied)
        except ImportError:
            self.skipTest("Pillow not installed")


class TestTesseractOCR(unittest.TestCase):
    """Test Tesseract OCR engine."""
    
    def setUp(self):
        self.engine = create_ocr_engine()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_engine(self):
        engine = create_ocr_engine()
        self.assertIsInstance(engine, TesseractOCR)
    
    def test_availability(self):
        availability = self.engine.is_available()
        self.assertIsInstance(availability, bool)
    
    def test_version(self):
        version = self.engine.get_version()
        if self.engine.is_available():
            self.assertIsNotNone(version)
        else:
            self.assertIsNone(version)
    
    def test_languages(self):
        languages = self.engine.get_available_languages()
        self.assertIsInstance(languages, list)
        if self.engine.is_available():
            self.assertIn("eng", languages)
    
    def test_extract_text_nonexistent_file(self):
        result = self.engine.extract_text_from_image("/nonexistent/image.png")
        self.assertFalse(result.success)
        if self.engine.is_available():
            self.assertIn("not found", result.error_message.lower())
        else:
            self.assertIn("not available", result.error_message.lower())
    
    def test_extract_text_from_image(self):
        if not self.engine.is_available():
            self.skipTest("Tesseract not available")
        
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            img_path = Path(self.temp_dir) / "test_ocr.png"
            img = Image.new("RGB", (400, 100), color="white")
            draw = ImageDraw.Draw(img)
            draw.text((10, 30), "Hello World", fill="black")
            img.save(str(img_path))
            
            result = self.engine.extract_text_from_image(str(img_path))
            
            self.assertTrue(result.success)
            self.assertEqual(result.language, "eng")
            self.assertEqual(result.page_count, 1)
        except ImportError:
            self.skipTest("Pillow not installed")
    
    def test_extract_text_with_preprocessing(self):
        if not self.engine.is_available():
            self.skipTest("Tesseract not available")
        
        try:
            from PIL import Image, ImageDraw
            
            img_path = Path(self.temp_dir) / "test_preprocess.png"
            img = Image.new("RGB", (400, 100), color="white")
            draw = ImageDraw.Draw(img)
            draw.text((10, 30), "Test Text", fill="black")
            img.save(str(img_path))
            
            result = self.engine.extract_text_from_image(
                str(img_path), preprocess=True
            )
            
            self.assertTrue(result.success)
        except ImportError:
            self.skipTest("Pillow not installed")


class TestOCREngineIntegration(unittest.TestCase):
    """Integration tests for OCR engine."""
    
    def setUp(self):
        self.engine = create_ocr_engine()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_batch_ocr(self):
        if not self.engine.is_available():
            self.skipTest("Tesseract not available")
        
        try:
            from PIL import Image, ImageDraw
            
            files = []
            for i in range(3):
                img_path = Path(self.temp_dir) / f"test_{i}.png"
                img = Image.new("RGB", (400, 100), color="white")
                draw = ImageDraw.Draw(img)
                draw.text((10, 30), f"Document {i}", fill="black")
                img.save(str(img_path))
                files.append(str(img_path))
            
            results = self.engine.batch_ocr(files)
            
            self.assertEqual(len(results), 3)
            self.assertTrue(all(isinstance(r, OCRResult) for r in results))
        except ImportError:
            self.skipTest("Pillow not installed")


if __name__ == "__main__":
    unittest.main()
