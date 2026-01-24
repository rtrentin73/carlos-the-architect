"""Document parsing utilities for extracting text from various file formats."""
import io
import os
from typing import Optional
from fastapi import UploadFile, HTTPException
from pypdf import PdfReader
from docx import Document
import openpyxl


MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB (increased for async processing)


async def extract_text_from_file(file: UploadFile) -> str:
    """
    Extract text content from uploaded file.

    Supports: PDF, DOCX, TXT, MD, XLSX, and other text-based formats.

    Args:
        file: Uploaded file from FastAPI

    Returns:
        Extracted text content

    Raises:
        HTTPException: If file is too large, empty, or cannot be processed
    """
    # Read file content
    content = await file.read()
    file_size = len(content)

    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024}MB"
        )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    # Get file extension
    filename = file.filename or ""
    extension = filename.lower().split(".")[-1] if "." in filename else ""

    try:
        # Extract text based on file type
        if extension == "pdf":
            text = _extract_from_pdf(content)
        elif extension in ["docx", "doc"]:
            text = _extract_from_docx(content)
        elif extension in ["xlsx", "xls"]:
            text = _extract_from_excel(content)
        elif extension in ["txt", "md", "markdown", "text"]:
            text = _extract_from_text(content)
        else:
            # Try to read as plain text
            text = _extract_from_text(content)

        # Validate extracted content
        if not text or not text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract any text from the document"
            )

        return text.strip()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error processing file: {str(e)}"
        )


def _extract_from_pdf(content: bytes) -> str:
    """Extract text from PDF file."""
    pdf_file = io.BytesIO(content)
    reader = PdfReader(pdf_file)

    text_parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)

    return "\n\n".join(text_parts)


def _extract_from_docx(content: bytes) -> str:
    """Extract text from DOCX file."""
    docx_file = io.BytesIO(content)
    doc = Document(docx_file)

    text_parts = []
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            text_parts.append(paragraph.text)

    # Also extract text from tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    text_parts.append(cell.text)

    return "\n\n".join(text_parts)


def _extract_from_excel(content: bytes) -> str:
    """Extract text from Excel file."""
    excel_file = io.BytesIO(content)
    workbook = openpyxl.load_workbook(excel_file, data_only=True)

    text_parts = []
    for sheet in workbook.worksheets:
        for row in sheet.iter_rows(values_only=True):
            row_text = " | ".join(str(cell) for cell in row if cell is not None)
            if row_text.strip():
                text_parts.append(row_text)

    return "\n".join(text_parts)


def _extract_from_text(content: bytes) -> str:
    """Extract text from plain text file."""
    # Try different encodings
    encodings = ["utf-8", "utf-16", "latin-1", "cp1252"]

    for encoding in encodings:
        try:
            return content.decode(encoding)
        except (UnicodeDecodeError, AttributeError):
            continue

    raise ValueError("Could not decode text file with any supported encoding")


def extract_text_from_path(file_path: str) -> str:
    """
    Extract text content from a file path (for async background processing).

    Args:
        file_path: Absolute path to the file

    Returns:
        Extracted text content

    Raises:
        ValueError: If file cannot be processed or is empty
    """
    if not os.path.exists(file_path):
        raise ValueError(f"File not found: {file_path}")

    file_size = os.path.getsize(file_path)
    if file_size == 0:
        raise ValueError("File is empty")

    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024}MB")

    # Get file extension
    extension = file_path.lower().split(".")[-1] if "." in file_path else ""

    # Read file content
    with open(file_path, "rb") as f:
        content = f.read()

    try:
        # Extract text based on file type
        if extension == "pdf":
            text = _extract_from_pdf(content)
        elif extension in ["docx", "doc"]:
            text = _extract_from_docx(content)
        elif extension in ["xlsx", "xls"]:
            text = _extract_from_excel(content)
        elif extension in ["txt", "md", "markdown", "text"]:
            text = _extract_from_text(content)
        else:
            # Try to read as plain text
            text = _extract_from_text(content)

        # Validate extracted content
        if not text or not text.strip():
            raise ValueError("Could not extract any text from the document")

        return text.strip()

    except Exception as e:
        raise ValueError(f"Error processing file: {str(e)}")
