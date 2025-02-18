import requests
from bs4 import BeautifulSoup
from xml.etree import ElementTree
from typing import List
import time
import re

def get_pydantic_ai_docs_urls() -> List[str]:
    """Get URLs from Pydantic AI docs sitemap."""
    sitemap_url = "https://ai.pydantic.dev/sitemap.xml"
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()
        
        # Parse the XML
        root = ElementTree.fromstring(response.content)
        
        # Extract all URLs from the sitemap
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [loc.text for loc in root.findall('.//ns:loc', namespace)]
        
        return urls
    except Exception as e:
        print(f"Error fetching sitemap: {e}")
        return []

def clean_text(text: str) -> str:
    """Clean and format the text content."""
    # Remove multiple newlines
    text = re.sub(r'\n\s*\n', '\n\n', text)
    # Remove trailing/leading whitespace
    text = text.strip()
    return text

def get_page_content(url: str) -> str:
    """Fetch and extract content from a single page."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove navigation, header, and footer elements
        for element in soup.select('nav, header, footer, script, style'):
            element.decompose()
        
        # Get the main content
        main_content = soup.select_one('main, article, .content, #content, .documentation')
        if not main_content:
            main_content = soup.body
        
        # Extract all text content
        content = []
        
        # Get the title
        title = soup.find('h1')
        if title:
            content.append(f"# {title.get_text().strip()}")
        
        # Process headings
        for heading in main_content.find_all(['h2', 'h3', 'h4', 'h5', 'h6']):
            level = int(heading.name[1])
            content.append(f"\n{'#' * level} {heading.get_text().strip()}")
        
        # Process paragraphs and code blocks
        for element in main_content.find_all(['p', 'pre', 'code', 'ul', 'ol']):
            if element.name == 'pre' or element.name == 'code':
                code_content = element.get_text().strip()
                if code_content:
                    content.append(f"\n```\n{code_content}\n```\n")
            elif element.name in ['ul', 'ol']:
                for li in element.find_all('li'):
                    content.append(f"- {li.get_text().strip()}")
            else:
                text = element.get_text().strip()
                if text:
                    content.append(text)
        
        return clean_text('\n\n'.join(content))
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return ""

def main():
    # Get URLs from Pydantic AI docs
    urls = get_pydantic_ai_docs_urls()
    if not urls:
        print("No URLs found to crawl")
        return
    
    print(f"Found {len(urls)} URLs to crawl")
    
    # Crawl each URL and collect markdown content
    all_content = []
    for i, url in enumerate(urls, 1):
        print(f"Processing {i}/{len(urls)}: {url}")
        content = get_page_content(url)
        if content:
            # Add URL as a header before the content
            all_content.append(f"\n\n## Source: {url}\n\n{content}")
        # Be nice to the server
        time.sleep(1)
    
    # Combine all content and write to file
    final_content = "# Pydantic AI Documentation\n\n" + "\n".join(all_content)
    
    # Write to markdown file
    with open("pydanticai_docs.md", "w", encoding="utf-8") as f:
        f.write(final_content)
    
    print("Documentation has been saved to pydanticai_docs.md")

if __name__ == "__main__":
    main()
