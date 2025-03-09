from bs4 import BeautifulSoup
import re

def extract_text_from_html(html_content: str) -> str:
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(['script', 'style']):
            script.decompose()
        raw_html_text = soup.get_text(separator='\n', strip=True)
        return ' '.join(re.findall(r'\b\w+\b', raw_html_text))
    except Exception as e:
        return str(e)