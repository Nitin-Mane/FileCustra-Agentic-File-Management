#!/usr/bin/env python3
"""
FileCustra Tesseract OCR Subsystem
Selective OCR with Tesseract, multi-language support, and image preprocessing.
Invoked only for scanned PDFs and image files without text layers.
"""

import os
import logging
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Result of OCR extraction."""
    file_path: str
    success: bool
    text: str
    language: str
    confidence: float
    page_count: int
    preprocessing_applied: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "success": self.success,
            "text": self.text,
            "language": self.language,
            "confidence": self.confidence,
            "page_count": self.page_count,
            "preprocessing_applied": self.preprocessing_applied,
            "error_message": self.error_message,
        }


class ImagePreprocessor:
    """Image preprocessing for improved OCR accuracy."""
    
    def __init__(self):
        self._available = self._check_availability()
    
    def _check_availability(self) -> bool:
        try:
            from PIL import Image, ImageFilter, ImageEnhance
            return True
        except ImportError:
            return False
    
    def preprocess(self, image_path: str, output_path: str) -> Tuple[str, List[str]]:
        """Preprocess image for better OCR results."""
        if not self._available:
            return image_path, []
        
        applied = []
        
        try:
            from PIL import Image, ImageFilter, ImageEnhance
            
            img = Image.open(image_path)
            
            if img.mode != "L":
                img = img.convert("L")
                applied.append("grayscale_conversion")
            
            img = img.filter(ImageFilter.SHARPEN)
            applied.append("sharpening")
            
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.5)
            applied.append("contrast_enhancement")
            
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.1)
            applied.append("brightness_adjustment")
            
            img.save(output_path)
            
            return output_path, applied
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}")
            return image_path, []


class TesseractOCR:
    """Tesseract OCR engine wrapper."""
    
    def __init__(self, tesseract_path: Optional[str] = None):
        self._tesseract_path = tesseract_path or self._find_tesseract()
        self._preprocessor = ImagePreprocessor()
        self._available = self._check_availability()
    
    def _find_tesseract(self) -> Optional[str]:
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            "/usr/bin/tesseract",
            "/usr/local/bin/tesseract",
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        try:
            result = subprocess.run(
                ["tesseract", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return "tesseract"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return None
    
    def _check_availability(self) -> bool:
        if not self._tesseract_path:
            return False
        
        try:
            result = subprocess.run(
                [self._tesseract_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def is_available(self) -> bool:
        return self._available
    
    def get_version(self) -> Optional[str]:
        if not self._available:
            return None
        
        try:
            result = subprocess.run(
                [self._tesseract_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if "tesseract" in line.lower():
                        return line.strip()
        except Exception:
            pass
        
        return None
    
    def get_available_languages(self) -> List[str]:
        if not self._available:
            return []
        
        try:
            result = subprocess.run(
                [self._tesseract_path, "--list-langs"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                languages = []
                for line in result.stdout.splitlines():
                    if line.strip() and not line.startswith("List"):
                        languages.append(line.strip())
                return languages
        except Exception:
            pass
        
        return []
    
    def extract_text_from_image(
        self,
        image_path: str,
        language: str = "eng",
        preprocess: bool = True,
    ) -> OCRResult:
        """Extract text from an image file."""
        if not self._available:
            return OCRResult(
                file_path=image_path,
                success=False,
                text="",
                language=language,
                confidence=0.0,
                page_count=0,
                error_message="Tesseract not available",
            )
        
        path = Path(image_path)
        if not path.exists():
            return OCRResult(
                file_path=image_path,
                success=False,
                text="",
                language=language,
                confidence=0.0,
                page_count=0,
                error_message="File not found",
            )
        
        preprocessing_applied = []
        actual_image_path = image_path
        
        if preprocess and self._preprocessor._available:
            with tempfile.NamedTemporaryFile(suffix=path.suffix, delete=False) as tmp:
                tmp_path = tmp.name
            
            actual_image_path, preprocessing_applied = self._preprocessor.preprocess(
                image_path, tmp_path
            )
        
        try:
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
                output_path = tmp.name
            
            cmd = [
                self._tesseract_path,
                actual_image_path,
                output_path.rsplit(".", 1)[0],
                "-l", language,
                "--oem", "3",
                "--psm", "3",
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )
            
            txt_path = output_path
            if os.path.exists(txt_path):
                with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                
                os.unlink(txt_path)
                
                word_count = len(text.split()) if text.strip() else 0
                confidence = 85.0 if word_count > 0 else 0.0
                
                return OCRResult(
                    file_path=image_path,
                    success=True,
                    text=text,
                    language=language,
                    confidence=confidence,
                    page_count=1,
                    preprocessing_applied=preprocessing_applied,
                )
            else:
                return OCRResult(
                    file_path=image_path,
                    success=False,
                    text="",
                    language=language,
                    confidence=0.0,
                    page_count=0,
                    preprocessing_applied=preprocessing_applied,
                    error_message="OCR output file not created",
                )
                
        except subprocess.TimeoutExpired:
            return OCRResult(
                file_path=image_path,
                success=False,
                text="",
                language=language,
                confidence=0.0,
                page_count=0,
                preprocessing_applied=preprocessing_applied,
                error_message="OCR processing timed out",
            )
        except Exception as e:
            return OCRResult(
                file_path=image_path,
                success=False,
                text="",
                language=language,
                confidence=0.0,
                page_count=0,
                preprocessing_applied=preprocessing_applied,
                error_message=str(e),
            )
        finally:
            if preprocess and actual_image_path != image_path:
                try:
                    os.unlink(actual_image_path)
                except OSError:
                    pass
    
    def extract_text_from_pdf(
        self,
        pdf_path: str,
        language: str = "eng",
        max_pages: int = 50,
    ) -> OCRResult:
        """Extract text from a scanned PDF using OCR."""
        if not self._available:
            return OCRResult(
                file_path=pdf_path,
                success=False,
                text="",
                language=language,
                confidence=0.0,
                page_count=0,
                error_message="Tesseract not available",
            )
        
        path = Path(pdf_path)
        if not path.exists():
            return OCRResult(
                file_path=pdf_path,
                success=False,
                text="",
                language=language,
                confidence=0.0,
                page_count=0,
                error_message="File not found",
            )
        
        try:
            import fitz
            
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            all_text = []
            
            for page_num in range(min(page_count, max_pages)):
                page = doc[page_num]
                
                text = page.get_text()
                if text.strip():
                    all_text.append(text)
                    continue
                
                pix = page.get_pixmap(dpi=300)
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp_path = tmp.name
                
                pix.save(tmp_path)
                
                ocr_result = self.extract_text_from_image(
                    tmp_path, language, preprocess=True
                )
                
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                
                if ocr_result.success and ocr_result.text.strip():
                    all_text.append(ocr_result.text)
            
            doc.close()
            
            full_text = "\n\n".join(all_text)
            word_count = len(full_text.split()) if full_text else 0
            
            return OCRResult(
                file_path=pdf_path,
                success=True,
                text=full_text,
                language=language,
                confidence=80.0 if word_count > 0 else 0.0,
                page_count=page_count,
            )
            
        except ImportError:
            return OCRResult(
                file_path=pdf_path,
                success=False,
                text="",
                language=language,
                confidence=0.0,
                page_count=0,
                error_message="PyMuPDF not installed for PDF page extraction",
            )
        except Exception as e:
            return OCRResult(
                file_path=pdf_path,
                success=False,
                text="",
                language=language,
                confidence=0.0,
                page_count=0,
                error_message=str(e),
            )
    
    def batch_ocr(
        self,
        file_paths: List[str],
        language: str = "eng",
    ) -> List[OCRResult]:
        """Perform OCR on multiple files."""
        results = []
        for path in file_paths:
            ext = Path(path).suffix.lower()
            if ext == ".pdf":
                results.append(self.extract_text_from_pdf(path, language))
            else:
                results.append(self.extract_text_from_image(path, language))
        return results


def create_ocr_engine(tesseract_path: Optional[str] = None) -> TesseractOCR:
    """Factory function to create a Tesseract OCR engine."""
    return TesseractOCR(tesseract_path)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ocr_subsystem.py <image_or_pdf_path> [language]")
        sys.exit(1)
    
    language = sys.argv[2] if len(sys.argv) > 2 else "eng"
    
    engine = create_ocr_engine()
    
    print(f"Tesseract available: {engine.is_available()}")
    print(f"Version: {engine.get_version()}")
    print(f"Languages: {engine.get_available_languages()}")
    
    file_path = sys.argv[1]
    ext = Path(file_path).suffix.lower()
    
    if ext == ".pdf":
        result = engine.extract_text_from_pdf(file_path, language)
    else:
        result = engine.extract_text_from_image(file_path, language)
    
    print(f"\nOCR Result:")
    print(f"  Success: {result.success}")
    print(f"  Language: {result.language}")
    print(f"  Confidence: {result.confidence:.1f}%")
    print(f"  Pages: {result.page_count}")
    if result.text:
        preview = result.text[:500] + "..." if len(result.text) > 500 else result.text
        print(f"  Text Preview:\n{preview}")
    if result.error_message:
        print(f"  Error: {result.error_message}")
