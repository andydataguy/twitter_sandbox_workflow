import requests
from bs4 import BeautifulSoup
from xml.etree import ElementTree
from typing import List, Dict, Optional, AsyncGenerator, Tuple
import asyncio
import aiohttp
from aiohttp import ClientSession
import logging
from tqdm import tqdm
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin
import re
from pathlib import Path
from datetime import datetime

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
MAX_CONCURRENT_REQUESTS = 5  # FastAPI docs seem robust, can handle more concurrency
REQUEST_DELAY = 0.5  # Shorter delay
OUTPUT_FILE = str(Path(__file__).parent / "fastapi_docs.md")
SITEMAP_URL = "https://fastapi.tiangolo.com/sitemap.xml"
BASE_URL = "https://fastapi.tiangolo.com"  # Base URL for resolving relative URLs


def get_fastapi_docs_urls() -> List[str]:
    """Get URLs from FastAPI docs sitemap."""
    try:
        response = requests.get(SITEMAP_URL)
        response.raise_for_status()
        root = ElementTree.fromstring(response.content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [loc.text for loc in root.findall('.//ns:loc', namespace)]
        logger.info(f"Found {len(urls)} URLs in sitemap")
        return urls
    except Exception as e:
        logger.error(f"Error fetching sitemap: {e}")
        return []


def extract_sections_from_url(url: str) -> Tuple[str, Optional[str]]:
    """Extract section and subsection from URL path.  Handles language codes."""
    path = urlparse(url).path.strip('/')
    parts = path.split('/')

    # Handle language codes (e.g., /en/, /es/)
    if len(parts) > 0 and len(parts[0]) == 2:  # Likely a language code
        language_code = parts[0]
        parts = parts[1:]
    else:
        language_code = "en"  # Default to English

    if len(parts) == 0:
        return 'Home', None
    elif len(parts) == 1:
        return parts[0].replace('-', ' ').title(), None
    else:
        section = parts[0].replace('-', ' ').title()
        subsection = '/'.join(parts[1:]).replace('-', ' ').title()
        return section, subsection


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
    language: str = "en"  # Add language code


async def get_page_title(url: str, session: ClientSession, semaphore: asyncio.Semaphore, pbar: tqdm) -> Optional[PageInfo]:
    """Fetch title, structure, and language from a page."""
    async with semaphore:
        try:
            log_info(f"Fetching title from: {url}")
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Error fetching {url}: {response.status}")
                    return None

                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')

                title_tag = soup.find('meta', attrs={'property': 'og:title'}) or soup.title
                title = title_tag.get('content') if title_tag and 'content' in title_tag.attrs else (
                    title_tag.string if title_tag else url)
                title = title.replace('FastAPI', '').strip(' |:- ')

                section, subsection = extract_sections_from_url(url)
                language = urlparse(url).path.split('/')[1] if len(
                    urlparse(url).path.split('/')) > 1 and len(urlparse(url).path.split('/')[1]) == 2 else "en"

                logger.info(f"Processed title: {title} (Section: {section}, Subsection: {subsection}, Language: {language})")
                pbar.update(1)
                pbar.set_description(f"Processing {section}")

                await asyncio.sleep(REQUEST_DELAY)
                return PageInfo(url=url, title=title, section=section, subsection=subsection, language=language)
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
                soup = BeautifulSoup(html, 'lxml')

                # FastAPI uses a specific div for content.
                main_content = soup.find('div', class_='md-content__inner')
                if not main_content:
                    main_content = soup.find('div', id='main-content') or soup.find('main') # Fallbacks
                if not main_content:
                    main_content = soup.body


                if main_content:
                    content = []
                    for element in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'pre', 'code', 'table']):
                        text = clean_text(element.get_text())
                        if text:
                            content.append(text)

                    page.content = '\n\n'.join(content)
                    # Create a more robust anchor, handling special characters.
                    page.anchor = f"#{page.language}-{page.section.lower().replace(' ', '-')}-{page.title.lower().replace(' ', '-').replace('/', '-')}"
                    page.anchor = re.sub(r'[^\w\-_#]', '', page.anchor) # Remove invalid characters

                logger.info(f"Processed content for: {page.title}")
                pbar.update(1)
                pbar.set_description(f"Processing {page.section}/{page.title}")

                await asyncio.sleep(REQUEST_DELAY)
                return page

        except Exception as e:
            logger.error(f"Error getting content for {page.url}: {e}")
            return None


async def process_section_pages(pages: List[PageInfo], session: ClientSession, semaphore: asyncio.Semaphore,
                                pbar: tqdm) -> AsyncGenerator[PageInfo, None]:
    """Process pages in a section and yield results one at a time."""
    tasks = [get_page_content(page, session, semaphore, pbar) for page in pages]
    for completed in asyncio.as_completed(tasks):
        result = await completed
        if result:
            yield result


def write_section_header(f, section: str, pages: List[PageInfo], current_language: str):
    """Write a section header and table of contents, handling languages."""
    # Use HTML comments to separate languages, for clarity in the Markdown.
    f.write(f"\n<!-- Language: {current_language} -->\n")
    f.write(f"\n## {section}\n\n")

    if any(page.subsection for page in pages):
        subsections = {}
        for page in pages:
            if page.subsection:
                subsection = page.subsection.split('/')[0]
                if subsection not in subsections:
                    subsections[subsection] = []
                subsections[subsection].append(page)

        for subsection, subpages in subsections.items():
            f.write(f"### {subsection}\n\n")
            for page in subpages:
                title = page.title or page.subsection.split('/')[-1]
                f.write(f"- [{title}]({page.anchor})\n")
        f.write("\n")
    else:
        for page in pages:
            title = page.title or page.section
            f.write(f"- [{title}]({page.anchor})\n")
        f.write("\n")


async def process_urls_streaming(urls: List[str]):
    """Process URLs, handling multiple languages and creating a combined TOC."""
    pages_by_section_and_language: Dict[str, Dict[str, List[PageInfo]]] = {}

    logger.info("Starting to fetch page titles and structure...")
    async for page in get_page_info_generator(urls):
        if page.language not in pages_by_section_and_language:
            pages_by_section_and_language[page.language] = {}
        if page.section not in pages_by_section_and_language[page.language]:
            pages_by_section_and_language[page.language][page.section] = []
        pages_by_section_and_language[page.language][page.section].append(page)

    logger.info(f"Found languages: {list(pages_by_section_and_language.keys())}")
    for language, sections in pages_by_section_and_language.items():
        logger.info(f"Language '{language}' has {len(sections)} sections")
        for section, pages in sections.items():
            logger.info(f"  Section '{section}' has {len(pages)} pages")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("# FastAPI Documentation\n\n")
        f.write("Generated on: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")

        # --- Combined Table of Contents ---
        f.write("## Table of Contents\n\n")
        for language, sections in pages_by_section_and_language.items():
            f.write(f"### {language.upper()}\n\n")  # Language heading
            for section in sections:
                # Create valid anchor links, including language and handling special characters.
                anchor_link = f"#{language}-{section.lower().replace(' ', '-').replace('/', '-')}"
                anchor_link = re.sub(r'[^\w\-_#]', '', anchor_link)
                f.write(f"- [{section} ({language.upper()})]({anchor_link})\n")
        f.write("\n")

        total_pages = sum(len(pages) for sections in pages_by_section_and_language.values() for pages in sections.values())
        logger.info(f"Starting to fetch content for {total_pages} pages...")

        with tqdm(total=total_pages, desc="Fetching page content", unit="page") as pbar:
            async with aiohttp.ClientSession() as session:
                semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

                for language, sections in pages_by_section_and_language.items():
                    current_language = language # Keep track of the current language
                    for section, pages in sections.items():
                        logger.info(f"Processing section: {section} ({language})")
                        write_section_header(f, section, pages, current_language)
                        async for page in process_section_pages(pages, session, semaphore, pbar):
                            if page.title:
                                f.write(f"\n### {page.title}\n\n")
                            if page.content:
                                f.write(f"{page.content}\n\n")
                        logger.info(f"Completed section: {section} ({language})")
                        f.write("\n---\n")

async def main():
    """Main execution function."""
    log_info("Starting FastAPI documentation scraper")
    urls = get_fastapi_docs_urls()
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