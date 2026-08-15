#!/usr/bin/env python3
"""
FileCustra Magika File Type Router
Integrates Google Magika deep learning content-type detection with extension fallback routing
and risk categorization for file management operations.
"""

import os
import mimetypes
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import magika
    MAGIKA_AVAILABLE = True
except ImportError:
    MAGIKA_AVAILABLE = False


class FileCategory(Enum):
    """File risk categories."""
    DOCUMENT = "document"
    CODE = "code"
    ARCHIVE = "archive"
    EXECUTABLE = "executable"
    MEDIA = "media"
    SYSTEM = "system"
    DATA = "data"
    UNKNOWN = "unknown"


@dataclass
class FileTypeResult:
    """Result of file type detection."""
    path: str
    file_name: str
    extension: str
    magika_label: Optional[str]
    magika_mime: Optional[str]
    magika_confidence: float
    extension_mime: Optional[str]
    category: FileCategory
    risk_level: str
    mismatch_warning: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "file_name": self.file_name,
            "extension": self.extension,
            "magika_label": self.magika_label,
            "magika_mime": self.magika_mime,
            "magika_confidence": self.magika_confidence,
            "extension_mime": self.extension_mime,
            "category": self.category.value,
            "risk_level": self.risk_level,
            "mismatch_warning": self.mismatch_warning,
        }


EXTENSION_TO_CATEGORY: Dict[str, FileCategory] = {
    # Documents
    "pdf": FileCategory.DOCUMENT,
    "doc": FileCategory.DOCUMENT,
    "docx": FileCategory.DOCUMENT,
    "xls": FileCategory.DOCUMENT,
    "xlsx": FileCategory.DOCUMENT,
    "ppt": FileCategory.DOCUMENT,
    "pptx": FileCategory.DOCUMENT,
    "odt": FileCategory.DOCUMENT,
    "ods": FileCategory.DOCUMENT,
    "odp": FileCategory.DOCUMENT,
    "rtf": FileCategory.DOCUMENT,
    "tex": FileCategory.DOCUMENT,
    "epub": FileCategory.DOCUMENT,
    
    # Code
    "py": FileCategory.CODE,
    "js": FileCategory.CODE,
    "ts": FileCategory.CODE,
    "jsx": FileCategory.CODE,
    "tsx": FileCategory.CODE,
    "rs": FileCategory.CODE,
    "go": FileCategory.CODE,
    "java": FileCategory.CODE,
    "cpp": FileCategory.CODE,
    "c": FileCategory.CODE,
    "h": FileCategory.CODE,
    "hpp": FileCategory.CODE,
    "cs": FileCategory.CODE,
    "rb": FileCategory.CODE,
    "php": FileCategory.CODE,
    "swift": FileCategory.CODE,
    "kt": FileCategory.CODE,
    "scala": FileCategory.CODE,
    "html": FileCategory.CODE,
    "css": FileCategory.CODE,
    "scss": FileCategory.CODE,
    "json": FileCategory.DATA,
    "xml": FileCategory.DATA,
    "yaml": FileCategory.DATA,
    "yml": FileCategory.DATA,
    "toml": FileCategory.DATA,
    
    # Archives
    "zip": FileCategory.ARCHIVE,
    "rar": FileCategory.ARCHIVE,
    "7z": FileCategory.ARCHIVE,
    "tar": FileCategory.ARCHIVE,
    "gz": FileCategory.ARCHIVE,
    "bz2": FileCategory.ARCHIVE,
    "xz": FileCategory.ARCHIVE,
    "tgz": FileCategory.ARCHIVE,
    
    # Executables
    "exe": FileCategory.EXECUTABLE,
    "msi": FileCategory.EXECUTABLE,
    "bat": FileCategory.EXECUTABLE,
    "cmd": FileCategory.EXECUTABLE,
    "com": FileCategory.EXECUTABLE,
    "scr": FileCategory.EXECUTABLE,
    "pif": FileCategory.EXECUTABLE,
    "dll": FileCategory.SYSTEM,
    "sys": FileCategory.SYSTEM,
    "drv": FileCategory.SYSTEM,
    "app": FileCategory.EXECUTABLE,
    "deb": FileCategory.EXECUTABLE,
    "rpm": FileCategory.EXECUTABLE,
    
    # Media
    "png": FileCategory.MEDIA,
    "jpg": FileCategory.MEDIA,
    "jpeg": FileCategory.MEDIA,
    "gif": FileCategory.MEDIA,
    "bmp": FileCategory.MEDIA,
    "webp": FileCategory.MEDIA,
    "svg": FileCategory.MEDIA,
    "ico": FileCategory.MEDIA,
    "tiff": FileCategory.MEDIA,
    "mp3": FileCategory.MEDIA,
    "wav": FileCategory.MEDIA,
    "flac": FileCategory.MEDIA,
    "ogg": FileCategory.MEDIA,
    "aac": FileCategory.MEDIA,
    "wma": FileCategory.MEDIA,
    "mp4": FileCategory.MEDIA,
    "avi": FileCategory.MEDIA,
    "mkv": FileCategory.MEDIA,
    "mov": FileCategory.MEDIA,
    "wmv": FileCategory.MEDIA,
    "webm": FileCategory.MEDIA,
    "flv": FileCategory.MEDIA,
    
    # System
    "ini": FileCategory.SYSTEM,
    "cfg": FileCategory.SYSTEM,
    "conf": FileCategory.SYSTEM,
    "log": FileCategory.DATA,
    "tmp": FileCategory.SYSTEM,
    "bak": FileCategory.SYSTEM,
    "old": FileCategory.SYSTEM,
    "swp": FileCategory.SYSTEM,
    
    # Data
    "csv": FileCategory.DATA,
    "sql": FileCategory.DATA,
    "db": FileCategory.DATA,
    "sqlite": FileCategory.DATA,
    "md": FileCategory.DOCUMENT,
    "txt": FileCategory.DOCUMENT,
}

MAGIKA_LABEL_TO_CATEGORY: Dict[str, FileCategory] = {
    "pdf": FileCategory.DOCUMENT,
    "doc": FileCategory.DOCUMENT,
    "docx": FileCategory.DOCUMENT,
    "xls": FileCategory.DOCUMENT,
    "xlsx": FileCategory.DOCUMENT,
    "ppt": FileCategory.DOCUMENT,
    "pptx": FileCategory.DOCUMENT,
    "txt": FileCategory.DOCUMENT,
    "html": FileCategory.CODE,
    "xml": FileCategory.DATA,
    "json": FileCategory.DATA,
    "javascript": FileCategory.CODE,
    "python": FileCategory.CODE,
    "c": FileCategory.CODE,
    "cpp": FileCategory.CODE,
    "java": FileCategory.CODE,
    "php": FileCategory.CODE,
    "ruby": FileCategory.CODE,
    "go": FileCategory.CODE,
    "rust": FileCategory.CODE,
    "typescript": FileCategory.CODE,
    "zip": FileCategory.ARCHIVE,
    "rar": FileCategory.ARCHIVE,
    "7z": FileCategory.ARCHIVE,
    "tar": FileCategory.ARCHIVE,
    "gz": FileCategory.ARCHIVE,
    "png": FileCategory.MEDIA,
    "jpeg": FileCategory.MEDIA,
    "gif": FileCategory.MEDIA,
    "bmp": FileCategory.MEDIA,
    "webp": FileCategory.MEDIA,
    "svg": FileCategory.MEDIA,
    "mp3": FileCategory.MEDIA,
    "wav": FileCategory.MEDIA,
    "flac": FileCategory.MEDIA,
    "mp4": FileCategory.MEDIA,
    "avi": FileCategory.MEDIA,
    "mkv": FileCategory.MEDIA,
    "mov": FileCategory.MEDIA,
    "exe": FileCategory.EXECUTABLE,
    "dll": FileCategory.SYSTEM,
}


class MagikaFileRouter:
    """Content-based file type router using Magika with extension fallback."""
    
    def __init__(self):
        self._magika_client = None
        if MAGIKA_AVAILABLE:
            try:
                self._magika_client = magika.Magika()
            except Exception:
                pass
    
    def classify_file(self, file_path: str) -> FileTypeResult:
        """Classify a file using Magika and extension fallback."""
        path = Path(file_path)
        file_name = path.name
        extension = path.suffix.lstrip(".").lower()
        
        magika_label = None
        magika_mime = None
        magika_confidence = 0.0
        
        if self._magika_client and path.exists():
            try:
                result = self._magika_client.identify_bytes(path.read_bytes()[:65536])
                if result and result.output:
                    magika_label = result.output.label
                    magika_mime = result.output.mime_type
                    magika_confidence = result.output.score
            except Exception:
                pass
        
        extension_mime = mimetypes.guess_type(file_name)[0]
        
        category = self._determine_category(extension, magika_label)
        risk_level = self._assess_risk(extension, category)
        mismatch_warning = self._check_mismatch(extension, magika_label, magika_mime, extension_mime)
        
        return FileTypeResult(
            path=str(path.absolute()),
            file_name=file_name,
            extension=extension,
            magika_label=magika_label,
            magika_mime=magika_mime,
            magika_confidence=magika_confidence,
            extension_mime=extension_mime,
            category=category,
            risk_level=risk_level,
            mismatch_warning=mismatch_warning,
        )
    
    def _determine_category(self, extension: str, magika_label: Optional[str]) -> FileCategory:
        """Determine file category from extension and Magika label."""
        if magika_label:
            magika_category = MAGIKA_LABEL_TO_CATEGORY.get(magika_label.lower())
            if magika_category:
                return magika_category
        
        ext_category = EXTENSION_TO_CATEGORY.get(extension.lower())
        if ext_category:
            return ext_category
        
        return FileCategory.UNKNOWN
    
    def _assess_risk(self, extension: str, category: FileCategory) -> str:
        """Assess file risk level based on extension and category."""
        high_risk_extensions = {"exe", "bat", "cmd", "com", "msi", "scr", "pif", "vbs", "vbe", "js", "jse", "ws", "wsc", "wsh", "ps1", "psm1", "psd1", "psc1", "reg", "inf"}
        
        medium_risk_extensions = {"dll", "sys", "drv", "ocx", "so", "dylib"}
        
        low_risk_extensions = {"zip", "rar", "7z", "tar", "gz", "bz2", "xz", "tgz"}
        
        if extension.lower() in high_risk_extensions:
            return "high"
        
        if extension.lower() in medium_risk_extensions:
            return "medium"
        
        if extension.lower() in low_risk_extensions:
            return "low"
        
        if category == FileCategory.EXECUTABLE:
            return "high"
        
        if category == FileCategory.SYSTEM:
            return "medium"
        
        if category == FileCategory.ARCHIVE:
            return "low"
        
        return "safe"
    
    def _check_mismatch(
        self,
        extension: str,
        magika_label: Optional[str],
        magika_mime: Optional[str],
        extension_mime: Optional[str],
    ) -> Optional[str]:
        """Check for extension-Magika content mismatch."""
        if not magika_label or not extension:
            return None
        
        magika_ext_map = {
            "pdf": "pdf",
            "doc": "doc",
            "docx": "docx",
            "xls": "xls",
            "xlsx": "xlsx",
            "ppt": "ppt",
            "pptx": "pptx",
            "html": "html",
            "xml": "xml",
            "json": "json",
            "javascript": "js",
            "python": "py",
            "c": "c",
            "cpp": "cpp",
            "java": "java",
            "png": "png",
            "jpeg": "jpg",
            "gif": "gif",
            "bmp": "bmp",
            "webp": "webp",
            "svg": "svg",
            "zip": "zip",
            "rar": "rar",
            "7z": "7z",
            "tar": "tar",
            "gz": "gz",
            "exe": "exe",
            "dll": "dll",
            "txt": "txt",
            "md": "md",
        }
        
        expected_ext = magika_ext_map.get(magika_label.lower())
        if expected_ext and extension.lower() != expected_ext:
            return (
                f"Extension mismatch: file has .{extension} extension but Magika detected "
                f"{magika_label} content. The file may have been renamed or have incorrect content."
            )
        
        return None
    
    def classify_batch(self, file_paths: List[str]) -> List[FileTypeResult]:
        """Classify multiple files."""
        return [self.classify_file(path) for path in file_paths]
    
    def get_extension_mapping(self) -> Dict[str, str]:
        """Get extension to category mapping."""
        return {ext: cat.value for ext, cat in EXTENSION_TO_CATEGORY.items()}
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions."""
        return list(EXTENSION_TO_CATEGORY.keys())


def create_file_router() -> MagikaFileRouter:
    """Factory function to create a Magika file router."""
    return MagikaFileRouter()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python magika_router.py <file_path>")
        sys.exit(1)
    
    router = create_file_router()
    result = router.classify_file(sys.argv[1])
    
    print(f"File: {result.file_name}")
    print(f"Extension: .{result.extension}")
    print(f"Category: {result.category.value}")
    print(f"Risk Level: {result.risk_level}")
    print(f"Magika Label: {result.magika_label}")
    print(f"Magika MIME: {result.magika_mime}")
    print(f"Magika Confidence: {result.magika_confidence:.4f}")
    print(f"Extension MIME: {result.extension_mime}")
    if result.mismatch_warning:
        print(f"WARNING: {result.mismatch_warning}")
