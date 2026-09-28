"""
Document parsing service for ResumeLens AI.
Supports PDF, DOCX, and TXT files with safe memory handling,
validation against malformed files, and structured line extraction.
"""

import io
import os
import re
from typing import Dict, List, Tuple, Any, Optional


class DocumentParseError(Exception):
    """Custom exception raised when document parsing fails."""
    pass


class DocumentParser:
    """
    Parses PDF, DOCX, and TXT resume files into cleaned text and line segments.
    Applies privacy safeguards by not writing unencrypted documents to persistent disk.
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}
    MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

    @classmethod
    def validate_file(cls, filename: str, file_bytes: bytes):
        """Validates file extension and size constraints."""
        if not filename:
            raise DocumentParseError("Filename cannot be empty.")

        ext = os.path.splitext(filename)[1].lower()
        if ext not in cls.SUPPORTED_EXTENSIONS:
            raise DocumentParseError(
                f"Unsupported file format '{ext}'. Allowed formats: {', '.join(cls.SUPPORTED_EXTENSIONS)}"
            )

        if len(file_bytes) == 0:
            raise DocumentParseError("Uploaded file is empty (0 bytes).")

        if len(file_bytes) > cls.MAX_FILE_SIZE_BYTES:
            max_mb = cls.MAX_FILE_SIZE_BYTES // (1024 * 1024)
            raise DocumentParseError(f"File size exceeds the {max_mb} MB limit.")

    @classmethod
    def parse_pdf(cls, file_bytes: bytes) -> str:
        """Extracts text from PDF bytes using pypdf."""
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(file_bytes))
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    raise DocumentParseError("The PDF document is password-protected or encrypted.")

            pages_text = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    pages_text.append(text)

            full_text = "\n".join(pages_text).strip()
            if not full_text:
                raise DocumentParseError(
                    "No extractable text was found in the PDF. The document might be scanned as an image or empty."
                )
            return full_text
        except DocumentParseError:
            raise
        except Exception as e:
            raise DocumentParseError(f"Failed to parse PDF document: {str(e)}")

    @classmethod
    def parse_docx(cls, file_bytes: bytes) -> str:
        """Extracts text from DOCX bytes using python-docx."""
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                    if row_text:
                        paragraphs.append(row_text)

            full_text = "\n".join(paragraphs).strip()
            if not full_text:
                raise DocumentParseError("No readable text found in the DOCX document.")
            return full_text
        except DocumentParseError:
            raise
        except Exception as e:
            raise DocumentParseError(f"Failed to parse DOCX document: {str(e)}")

    @classmethod
    def parse_txt(cls, file_bytes: bytes) -> str:
        """Extracts text from TXT bytes with multi-encoding fallback."""
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        for enc in encodings:
            try:
                text = file_bytes.decode(enc).strip()
                if text:
                    return text
            except (UnicodeDecodeError, LookupError):
                continue
        raise DocumentParseError("Could not decode plain text file using standard character encodings.")

    @classmethod
    def parse_bytes(cls, filename: str, file_bytes: bytes) -> Dict[str, Any]:
        """
        Main entry point for parsing document bytes into cleaned text and segmented lines.
        """
        cls.validate_file(filename, file_bytes)
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".pdf":
            raw_text = cls.parse_pdf(file_bytes)
        elif ext == ".docx":
            raw_text = cls.parse_docx(file_bytes)
        elif ext == ".txt":
            raw_text = cls.parse_txt(file_bytes)
        else:
            raise DocumentParseError(f"Unhandled file extension: {ext}")

        # Clean text
        normalized_lines = []
        for line in raw_text.splitlines():
            cleaned_line = line.strip()
            if cleaned_line:
                # Normalize internal spaces while preserving punctuation
                cleaned_line = re.sub(r"[ \t]+", " ", cleaned_line)
                normalized_lines.append(cleaned_line)

        clean_text = "\n".join(normalized_lines)

        return {
            "filename": filename,
            "file_type": ext,
            "byte_size": len(file_bytes),
            "raw_text": raw_text,
            "clean_text": clean_text,
            "lines": normalized_lines,
            "line_count": len(normalized_lines),
            "word_count": len(clean_text.split())
        }
