import io
import os
import tempfile
import pypdf
import docx2txt

def extract_text_from_pdf(file_stream):
    """Extracts text from a PDF file stream using pypdf."""
    text = ""
    try:
        # pypdf.PdfReader accepts a file-like object (BytesIO) or file path
        reader = pypdf.PdfReader(file_stream)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        raise ValueError(f"Failed to parse PDF document: {str(e)}")
    return text

def extract_text_from_docx(file_stream):
    """Extracts text from a DOCX file stream using docx2txt."""
    # docx2txt process expects a file path. We write the stream contents to a temporary file.
    temp_fd, temp_path = tempfile.mkstemp(suffix=".docx")
    try:
        with os.fdopen(temp_fd, 'wb') as tmp:
            data = file_stream.read() if hasattr(file_stream, 'read') else file_stream
            tmp.write(data)
        text = docx2txt.process(temp_path)
    except Exception as e:
        raise ValueError(f"Failed to parse Word document: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
    return text

def extract_text_from_txt(file_stream):
    """Extracts text from a plain text file stream."""
    try:
        content = file_stream.read() if hasattr(file_stream, 'read') else file_stream
        if isinstance(content, bytes):
            return content.decode('utf-8', errors='ignore')
        return str(content)
    except Exception as e:
        raise ValueError(f"Failed to parse text file: {str(e)}")

def extract_text(filename, file_stream):
    """Route file parsing based on extension."""
    if not filename:
        raise ValueError("Filename is empty")
        
    ext = filename.lower().split('.')[-1]
    
    # Ensure stream is reset to the beginning if it supports seek
    if hasattr(file_stream, 'seek'):
        file_stream.seek(0)  
    if ext == 'pdf':
        return extract_text_from_pdf(file_stream)
    elif ext == 'docx':
        return extract_text_from_docx(file_stream)
    elif ext == 'txt':
        return extract_text_from_txt(file_stream)
    else:
        raise ValueError(f"Unsupported file format: .{ext}")
