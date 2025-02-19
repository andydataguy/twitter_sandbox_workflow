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
    format='%(asctime)s - %(levelname)s - %(message)s',
    force=True
)
logger = logging.getLogger(__name__)

# Force immediate output for both print and logging
import sys
sys.stdout.reconfigure(line_buffering=True)
print = lambda *args, **kwargs: __builtins__.print(*args, **kwargs, flush=True)

def log_info(msg: str):
    """Log a message and print it to ensure visibility."""
    logger.info(msg)
    print(msg)

# Constants
MAX_CONCURRENT_REQUESTS = 6
REQUEST_DELAY = 1
OUTPUT_FILE = str(Path(__file__).parent / "langgraph_docs.md")

def get_langgraph_docs_urls() -> List[str]:
    """Get URLs from LangGraph docs sitemap."""
    sitemap_url = "https://langchain-ai.github.io/langgraph/sitemap.xml"
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()
        
        # Parse XML
        root = ElementTree.fromstring(response.content)
        
        # Extract URLs from sitemap
        urls = [
            url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text
            for url in root.findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url')
        ]
        
        logger.info(f"Found {len(urls)} URLs in sitemap")
        return urls
    except Exception as e:
        logger.error(f"Error fetching sitemap: {e}")
        return []

def extract_sections_from_url(url: str) -> Tuple[str, Optional[str]]:
    """Extract section and subsection from URL path."""
    path = urlparse(url).path.strip('/')
    parts = path.split('/')
    
    if len(parts) == 0:
        return 'Home', None
    elif len(parts) == 1:
        return parts[0].replace('-', ' ').title(), None
    else:
        return (
            parts[0].replace('-', ' ').title(),
            '/'.join(parts[1:]).replace('-', ' ').title()
        )

def clean_text(text: str) -> str:
    """Clean and format the text content."""
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('¶', '')
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

async def get_page_title(url: str, session: ClientSession, semaphore: asyncio.Semaphore, pbar: tqdm) -> Optional[PageInfo]:
    """Fetch just the title and structure from a page."""
    async with semaphore:
        try:
            log_info(f"Fetching title from: {url}")
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Error fetching {url}: {response.status}")
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Get title
                title = soup.title.string if soup.title else ''
                if 'LangGraph' in title:
                    title = title.replace('LangGraph', '').strip(' |')
                
                # Get section and subsection
                section, subsection = extract_sections_from_url(url)
                
                logger.info(f"Processed title: {title} (Section: {section}, Subsection: {subsection})")
                pbar.update(1)
                pbar.set_description(f"Processing {section}")
                
                await asyncio.sleep(REQUEST_DELAY)
                return PageInfo(url=url, title=title, section=section, subsection=subsection)
                
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            return None

async def get_page_info_generator(urls: List[str]) -> AsyncGenerator[PageInfo, None]:
    """Generate page info one at a time."""
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        with tqdm(total=len(urls), desc="Fetching page titles", unit="page") as pbar:
            tasks = [get_page_title(url, session, semaphore, pbar) for url in urls]
            
            for completed in asyncio.as_completed(tasks):
                result = await completed
                if result:
                    yield result

async def get_page_content(page: PageInfo, session: ClientSession, semaphore: asyncio.Semaphore, pbar: tqdm) -> Optional[PageInfo]:
    """Fetch the full content of a page."""
    async with semaphore:
        try:
            logger.info(f"Fetching content from: {page.url}")
            async with session.get(page.url) as response:
                if response.status != 200:
                    logger.error(f"Error fetching content for {page.url}: {response.status}")
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find main content
                main_content = soup.find('article')
                if not main_content:
                    main_content = soup.find('main')
                
                if main_content:
                    # Extract text content
                    content = []
                    for element in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li']):
                        text = clean_text(element.get_text())
                        if text:
                            content.append(text)
                    
                    page.content = '\n\n'.join(content)
                    
                    # Get anchor for table of contents
                    page.anchor = f"#{page.title.lower().replace(' ', '-')}"  # Use title for anchor
                
                logger.info(f"Processed content for: {page.title}")
                pbar.update(1)
                pbar.set_description(f"Processing {page.section}/{page.title}")
                
                await asyncio.sleep(REQUEST_DELAY)
                return page
                
        except Exception as e:
            logger.error(f"Error getting content for {page.url}: {e}")
            return None

async def process_section_pages(pages: List[PageInfo], session: ClientSession, semaphore: asyncio.Semaphore, pbar: tqdm) -> AsyncGenerator[PageInfo, None]:
    """Process pages in a section and yield results one at a time."""
    tasks = [get_page_content(page, session, semaphore, pbar) for page in pages]
    for completed in asyncio.as_completed(tasks):
        result = await completed
        if result:
            yield result
            
def generate_anchor(title: str, existing_anchors: Dict[str, int]) -> str:
    """Generates a unique anchor link for a title."""
    # Basic cleaning: lowercase, replace spaces with hyphens, remove special chars
    anchor = title.lower().replace(" ", "-").replace(":", "").replace("(", "").replace(")", "").replace("/", "").replace("'", "").replace('"', "").replace(".", "").replace(",", "")
    
    # Handle duplicates by appending a counter
    count = existing_anchors.get(anchor, 0) + 1
    existing_anchors[anchor] = count
    if count > 1:
        anchor = f"{anchor}-{count}"  # Append counter for duplicates
    return f"#{anchor}"
            
def write_section_header(f, section: str, pages: List[PageInfo]):
    """Write a section header to the markdown file."""
    f.write(f"\n## {section}\n\n")

    # Keep track of used anchors to prevent duplicates
    existing_anchors: Dict[str, int] = {}
    
    # Write table of contents for section
    if any(page.subsection for page in pages):
        subsections = {}
        for page in pages:
            if page.subsection:
                subsection = page.subsection.split('/')[0] #Take the first part if they are multi-level
                if subsection not in subsections:
                    subsections[subsection] = []
                subsections[subsection].append(page)
        
        for subsection, subpages in sorted(subsections.items()): #Added sorting.
            f.write(f"### {subsection}\n\n")
            for page in sorted(subpages, key=lambda x: x.title): #Added sorting.
                title = page.title or page.subsection.split('/')[-1]
                page.anchor = generate_anchor(title, existing_anchors)  # Generate and store
                f.write(f"- [{title}]({page.anchor})\n")
        f.write("\n")
    else:
        for page in pages:
            title = page.title or page.section #Or section so something populates.
            page.anchor = generate_anchor(title, existing_anchors) #Generate and store.
            f.write(f"- [{title}]({page.anchor})\n")
        f.write("\n")

    # Write actual content with headers using generated anchors.
    for page in pages:
        if page.subsection:
            # If its a subsection, we want to do an H3
             f.write(f"\n### <a name='{page.anchor[1:]}'></a>{page.title}\n\n")  # Create an anchor tag.
        else:
            f.write(f"\n### <a name='{page.anchor[1:]}'></a>{page.title}\n\n") # Create an anchor tag.
        if page.content:
            f.write(f"{page.content}\n\n")
    f.write("---\n")  # Separator between pages
    f.flush() #Flush

async def process_urls_streaming(urls: List[str]):
    """Process URLs in a streaming fashion to minimize memory usage."""
    # Get basic info for all pages
    pages_by_section: Dict[str, List[PageInfo]] = {}
    
    logger.info("Starting to fetch page titles and structure...")
    async for page in get_page_info_generator(urls):
        if page.section not in pages_by_section:
            pages_by_section[page.section] = []
        pages_by_section[page.section].append(page)
    
    logger.info(f"Found {len(pages_by_section)} sections")
    for section, pages in pages_by_section.items():
        logger.info(f"Section '{section}' has {len(pages)} pages")
    
    # Process each section
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("# LangGraph Documentation\n\n")
        f.write("Generated on: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")
        
        # Write main table of contents
        f.write("## Table of Contents\n\n")
        for section in pages_by_section:
             f.write(f"- [{section}](#{section.lower().replace(' ', '-')})\n") #Added the section title
        f.write("\n")
        
        # Process each section
        total_pages = sum(len(pages) for pages in pages_by_section.values())
        logger.info(f"Starting to fetch content for {total_pages} pages...")
        
        with tqdm(total=total_pages, desc="Fetching page content", unit="page") as pbar:
            async with aiohttp.ClientSession() as session:
                semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
                
                for section, pages in sorted(pages_by_section.items()): #Sorted
                    logger.info(f"Processing section: {section}")
                    
                    # Write section header with table of contents
                    write_section_header(f, section, pages)
                    
                    # Process pages in this section
                    async for page in process_section_pages(pages, session, semaphore, pbar):
                        # Write page content
                        if page.title:
                            f.write(f"\n### {page.title}\n\n")  # Write the title again for each page.
                        if page.content:
                            f.write(f"{page.content}\n\n")

                    logger.info(f"Completed section: {section}")

async def main():
    """Main execution function."""
    log_info("Starting LangGraph documentation scraper")
    
    urls = get_langgraph_docs_urls()
    if not urls:
        logger.error("No URLs found in sitemap")
        return
    
    log_info(f"Found {len(urls)} URLs in sitemap")
    log_info("Starting to process URLs and generate documentation...")
    
    await process_urls_streaming(urls)
    
    log_info(f"Documentation has been written to {OUTPUT_FILE}")
    log_info("Scraping completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())