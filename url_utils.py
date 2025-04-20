import requests
from bs4 import BeautifulSoup

def extract_text_from_url(url: str) -> str:
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    paragraphs = [p.get_text(separator=" ", strip=True) for p in soup.find_all("p")]
    return " ".join(paragraphs)