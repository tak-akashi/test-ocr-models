"""HTML processing and normalization utilities."""

from bs4 import BeautifulSoup
import chardet


def normalize_html_content(content):
    """
    Normalize HTML content with proper encoding and structure.

    Args:
        content: HTML content as string or bytes

    Returns:
        str: Normalized HTML string with UTF-8 encoding
    """
    # Handle bytes encoding
    if isinstance(content, (bytes, bytearray)):
        enc = chardet.detect(content).get("encoding") or "utf-8"
        text = content.decode(enc, errors="replace")
    else:
        text = content

    # Ensure proper HTML structure
    soup = BeautifulSoup(text, "html.parser")
    if soup.head is None:
        # Create proper HTML structure if missing
        html = soup.new_tag("html")
        head = soup.new_tag("head")
        body = soup.new_tag("body")
        body.append(soup)
        html.append(head)
        html.append(body)
        soup = BeautifulSoup(str(html), "html.parser")

    # Ensure UTF-8 meta tag
    if not soup.head.find("meta", attrs={"charset": True}):
        meta = soup.new_tag("meta", charset="utf-8")
        soup.head.insert(0, meta)
    else:
        soup.head.find("meta", attrs={"charset": True})["charset"] = "utf-8"

    # Add CSS styles for tables
    style = soup.new_tag("style")
    style.string = """
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 10px 0;
    }
    table, th, td {
        border: 1px solid #000;
    }
    th, td {
        padding: 8px;
        text-align: left;
    }
    th {
        background-color: #f2f2f2;
        font-weight: bold;
    }
    """
    soup.head.append(style)

    return str(soup)