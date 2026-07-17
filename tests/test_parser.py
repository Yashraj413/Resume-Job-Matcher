import io
import pytest
from unittest.mock import MagicMock, patch
from app.services.parser import extract_text, extract_text_from_txt

def test_extract_text_from_txt():
    """Verify that plain text file extraction works as expected."""
    stream = io.BytesIO(b"Candidate Profile Info\nPython Developer experience")
    text = extract_text_from_txt(stream)
    assert "Python Developer" in text
    assert "Candidate Profile" in text

@patch('app.services.parser.pypdf.PdfReader')
def test_extract_text_from_pdf(mock_pdf_reader):
    """Verify that PDF parsing behaves correctly using mock pages."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "PDF Candidate Profile Details"
    
    mock_reader_instance = MagicMock()
    mock_reader_instance.pages = [mock_page]
    mock_pdf_reader.return_value = mock_reader_instance
    
    stream = io.BytesIO(b"mock pdf binary stream")
    text = extract_text("resume.pdf", stream)
    assert "PDF Candidate Profile Details" in text
    mock_pdf_reader.assert_called_once()

@patch('app.services.parser.docx2txt.process')
def test_extract_text_from_docx(mock_docx_process):
    """Verify that Word document parsing isolates file streams onto temporary paths correctly."""
    mock_docx_process.return_value = "DOCX Candidate Experience"
    
    stream = io.BytesIO(b"mock word binary stream")
    text = extract_text("resume.docx", stream)
    assert "DOCX Candidate Experience" in text
    mock_docx_process.assert_called_once()

def test_unsupported_format_raises_value_error():
    """Verify that files with unsupported extensions raise ValueError exceptions."""
    stream = io.BytesIO(b"executable data")
    with pytest.raises(ValueError) as exc:
        extract_text("script.py", stream)
    assert "Unsupported file format" in str(exc.value)
