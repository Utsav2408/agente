import re
import requests
import io
from urllib.parse import urlparse, parse_qs

def _extract_drive_file_id(shared_link: str) -> str:
    """
    Given a Google Drive “share” URL, extract the file ID.
    Supports URLs of the forms:
        • https://drive.google.com/file/d/FILE_ID/view?usp=…
        • https://drive.google.com/open?id=FILE_ID
        • https://drive.google.com/uc?id=FILE_ID&export=download
    """
    # Try to parse common patterns
    patterns = [
        r"https?://drive\.google\.com/file/d/([^/]+)",          # /file/d/FILE_ID/…
        r"https?://drive\.google\.com/open\?id=([^&]+)",        # /open?id=FILE_ID
        r"https?://drive\.google\.com/uc\?id=([^&]+)",          # /uc?id=FILE_ID
    ]
    for pat in patterns:
        m = re.search(pat, shared_link)
        if m:
            return m.group(1)

    # If none matched, try to fall back on parsing query params
    parsed = urlparse(shared_link)
    qs = parse_qs(parsed.query)
    if "id" in qs:
        return qs["id"][0]

    raise ValueError(f"Could not extract a Google Drive file ID from: {shared_link}")


def _get_confirm_token(response: requests.Response) -> str | None:
    """
    When Drive thinks a file is “too large” to scan, it returns an intermediate
    page with a warning and a “download_warning” cookie/token. This looks for that token.
    """
    for key, val in response.cookies.items():
        if key.startswith("download_warning"):
            return val
    return None


def download_pdf_from_gdrive_in_memory(shared_link: str) -> io.BytesIO:
    """
    Given a Google Drive shared link for a PDF, fetch its contents into a BytesIO
    buffer and return that buffer. The buffer's cursor will be set at the end of the stream,
    so if you need to read from it, remember to `.seek(0)` first.
    
    Usage:
        pdf_buffer = download_pdf_from_gdrive_in_memory("https://drive.google.com/…")
        pdf_bytes = pdf_buffer.getvalue()
        # or
        pdf_buffer.seek(0)
        some_other_function_accepting_a_file_like(pdf_buffer)
    """
    file_id = _extract_drive_file_id(shared_link)
    download_url = "https://docs.google.com/uc?export=download"
    session = requests.Session()

    # Initial request to get any confirmation token
    response = session.get(download_url, params={"id": file_id}, stream=True)
    token = _get_confirm_token(response)

    if token:
        # Second request with the confirmation token
        response = session.get(
            download_url,
            params={"id": file_id, "confirm": token},
            stream=True
        )

    # Read into BytesIO
    buffer = io.BytesIO()
    for chunk in response.iter_content(chunk_size=32768):
        if chunk:  # filter out keep-alive chunks
            buffer.write(chunk)

    return buffer