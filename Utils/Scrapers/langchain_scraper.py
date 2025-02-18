import requests
from bs4 import BeautifulSoup
from xml.etree import ElementTree
from typing import List, Dict, Generator, Iterator, Tuple, AsyncGenerator, Optional
import time
from datetime import datetime
import re
from pathlib import Path
from itertools import islice
import asyncio
import aiohttp
from aiohttp import ClientSession
import logging
from tqdm import tqdm
from dataclasses import dataclass
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MAX_CONCURRENT_REQUESTS = 3
REQUEST_DELAY = 2
OUTPUT_FILE = str(Path(__file__).parent / "langchain_docs.md")

def get_langchain_docs_urls() -> List[str]:
    """Get URLs from LangChain docs sitemap."""
    sitemap_url = "https://python.langchain.com/sitemap.xml"
    try:
        logger.info("Fetching sitemap from %s", sitemap_url)
        response = requests.get(sitemap_url, timeout=30)
        response.raise_for_status()
        
        # Parse the XML
        root = ElementTree.fromstring(response.content)
        
        # Extract all URLs from the sitemap
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [loc.text for loc in root.findall('.//ns:loc', namespace)]
        
        if not urls:
            logger.error("No URLs found in sitemap")
            return []
            
        logger.info("Found %d URLs in sitemap", len(urls))
        return urls
    except requests.RequestException as e:
        logger.error(f"Network error fetching sitemap: {e}")
        return []
    except ElementTree.ParseError as e:
        logger.error(f"Error parsing sitemap XML: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching sitemap: {e}")
        return []

def extract_sections_from_url(url: str) -> Tuple[str, Optional[str]]:
    """Extract section and subsection from URL path."""
    path = urlparse(url).path.strip('/').split('/')
    if len(path) >= 2:
        return path[0], path[1]
    elif len(path) == 1:
        return path[0], None
    return "misc", None

def clean_text(text: str) -> str:
    """Clean and format the text content."""
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

@dataclass
class PageInfo:
    """Store information about a documentation page."""
    url: str
    title: str
    section: str
    subsection: Optional[str] = None
    content: str = ""
    anchor: str = ""

async def get_page_title(url: str, session: ClientSession, semaphore: asyncio.Semaphore) -> Optional[PageInfo]:
    """Fetch just the title and structure from a page."""
    try:
        async with semaphore:
            await asyncio.sleep(REQUEST_DELAY)
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Get the title
                title = soup.find('h1')
                if not title:
                    title_text = url.split('/')[-1].replace('-', ' ').title()
                else:
                    title_text = title.get_text().strip()
                
                # Extract sections from URL
                section, subsection = extract_sections_from_url(url)
                
                # Create anchor
                anchor = title_text.lower().replace(' ', '-').replace('[', '').replace(']', '')
                
                return PageInfo(
                    url=url,
                    title=title_text,
                    section=section,
                    subsection=subsection,
                    anchor=anchor
                )
    except Exception as e:
        logger.error(f"Error getting title for {url}: {e}")
        return None

async def get_page_info_generator(urls: List[str]) -> AsyncGenerator[PageInfo, None]:
    """Generate page info one at a time."""
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    
    async with aiohttp.ClientSession() as session:
        with tqdm(total=len(urls), desc="Indexing pages", unit="page") as pbar:
            tasks = [get_page_title(url, session, semaphore) for url in urls]
            for completed_task in asyncio.as_completed(tasks):
                page_info = await completed_task
                if page_info:
                    pbar.update(1)
                    yield page_info

async def get_page_content(page: PageInfo, session: ClientSession, semaphore: asyncio.Semaphore, pbar: tqdm) -> Optional[str]:
    """Fetch the full content of a page."""
    try:
        async with semaphore:
            await asyncio.sleep(REQUEST_DELAY)
            async with session.get(page.url) as response:
                if response.status != 200:
                    pbar.update(1)
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Remove navigation, header, and footer elements
                for element in soup.select('nav, header, footer, script, style'):
                    element.decompose()
                
                main_content = soup.select_one('main, article, .prose, .markdown')
                if not main_content:
                    main_content = soup.body
                
                content = []
                
                # Add title and source
                content.append(f"# {page.title}")
                content.append(f"\n*Source: [{page.url}]({page.url})*\n")
                
                # Process headings and maintain hierarchy
                for heading in main_content.find_all(['h2', 'h3', 'h4', 'h5', 'h6']):
                    level = int(heading.name[1])
                    content.append(f"\n{'#' * level} {heading.get_text().strip()}")
                
                # Process content
                for element in main_content.find_all(['p', 'pre', 'code', 'ul', 'ol']):
                    if element.name in ['pre', 'code']:
                        code_content = element.get_text().strip()
                        if code_content:
                            classes = element.get('class', [])
                            lang = next((cls for cls in classes if cls.startswith('language-')), '')
                            lang = lang.replace('language-', '') if lang else 'python'
                            content.append(f"\n```{lang}\n{code_content}\n```\n")
                    elif element.name in ['ul', 'ol']:
                        content.append("")
                        for li in element.find_all('li'):
                            content.append(f"- {li.get_text().strip()}")
                        content.append("")
                    else:
                        text = element.get_text().strip()
                        if text:
                            content.append(f"\n{text}\n")
                
                pbar.update(1)
                return clean_text('\n'.join(content))
                
    except Exception as e:
        logger.error(f"Error processing {page.url}: {e}")
        pbar.update(1)
        return None

async def process_section_pages(pages: List[PageInfo], session: ClientSession, semaphore: asyncio.Semaphore, pbar: tqdm) -> AsyncGenerator[Tuple[PageInfo, str], None]:
    """Process pages in a section and yield results one at a time."""
    for page in pages:
        content = await get_page_content(page, session, semaphore, pbar)
        if content:
            yield page, content

def write_section_header(f, section: str, pages: List[PageInfo]):
    """Write a section header to the markdown file."""
    f.write(f"\n### {section.title()}\n\n")
    
    # Group by subsection
    subsections: Dict[str, List[PageInfo]] = {}
    for page in pages:
        if page.subsection:
            if page.subsection not in subsections:
                subsections[page.subsection] = []
            subsections[page.subsection].append(page)
        else:
            if "main" not in subsections:
                subsections["main"] = []
            subsections["main"].append(page)
    
    # Write subsection links
    for subsection, subpages in sorted(subsections.items()):
        if subsection != "main":
            f.write(f"\n#### {subsection.title()}\n")
        for page in sorted(subpages, key=lambda x: x.title):
            f.write(f"- [{page.title}](#{page.anchor})\n")
    f.write("\n")

async def process_urls_streaming(urls: List[str]):
    """Process URLs in a streaming fashion to minimize memory usage."""
    try:
        # Initialize structures
        sections: Dict[str, List[PageInfo]] = {}
        total_pages = 0
        
        # First pass: Index pages and build TOC structure
        logger.info("Building table of contents...")
        async for page_info in get_page_info_generator(urls):
            if page_info.section not in sections:
                sections[page_info.section] = []
            sections[page_info.section].append(page_info)
            total_pages += 1
        
        if total_pages == 0:
            logger.error("No pages were indexed successfully")
            return
        
        logger.info(f"Successfully indexed {total_pages} pages across {len(sections)} sections")
        
        # Write initial header and TOC
        logger.info(f"Writing table of contents to {OUTPUT_FILE}...")
        try:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                f.write("# LangChain Documentation\n\n")
                f.write(f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
                f.write(f"*Total pages: {total_pages}*\n\n")
                f.write("## Table of Contents\n\n")
                
                # Write TOC sections
                for section, pages in sorted(sections.items()):
                    write_section_header(f, section, pages)
                
                f.write("\n---\n\n## Content\n\n")
                f.flush()
                logger.info("Table of contents written successfully")
        except Exception as e:
            logger.error(f"Error writing table of contents: {e}")
            return
        
        # Second pass: Process content
        logger.info("Processing content...")
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        async with aiohttp.ClientSession() as session:
            with tqdm(total=total_pages, desc="Downloading content", unit="page") as pbar:
                for section, pages in sorted(sections.items()):
                    logger.info(f"Processing section: {section} ({len(pages)} pages)")
                    
                    try:
                        # Write section header in content
                        with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
                            f.write(f"\n## {section.title()}\n\n")
                        
                        # Process pages in section
                        async for page, content in process_section_pages(pages, session, semaphore, pbar):
                            try:
                                with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
                                    f.write(f"{content}\n\n---\n\n")
                                    f.flush()
                            except Exception as e:
                                logger.error(f"Error writing content for {page.url}: {e}")
                                continue
                    except Exception as e:
                        logger.error(f"Error processing section {section}: {e}")
                        continue
        
        logger.info(f"Documentation written to {OUTPUT_FILE}")
    except Exception as e:
        logger.error(f"Error in process_urls_streaming: {e}")

async def main():
    """Main execution function."""
    start_time = time.time()
    logger.info("Starting LangChain documentation scraper...")
    
    # Get URLs from sitemap
    urls = get_langchain_docs_urls()
    if not urls:
        logger.error("No URLs found. Exiting.")
        return
    
    # Process everything in a streaming fashion
    await process_urls_streaming(urls)
    
    elapsed_time = time.time() - start_time
    logger.info(f"Scraping completed in {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())
