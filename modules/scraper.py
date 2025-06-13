"""
Scraper module for the CTI Aggregator.
Handles scraping of threat intelligence from various sources.
"""

import logging
import time
import random
import requests
import feedparser
from datetime import datetime
from bs4 import BeautifulSoup
import urllib.parse

logger = logging.getLogger(__name__)

class ThreatIntelScraper:
    """Scrapes threat intelligence from various sources"""
    
    def __init__(self, sources_config):
        """
        Initialize the scraper with source configurations.
        
        Args:
            sources_config (list): List of source configurations
        """
        self.sources = sources_config
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:90.0) Gecko/20100101 Firefox/90.0'
        ]
    
    def get_random_user_agent(self):
        """
        Get a random user agent to avoid being blocked.
        
        Returns:
            str: Random user agent string
        """
        return random.choice(self.user_agents)
    
    def make_request(self, url, headers=None):
        """
        Make a request to a URL with proper error handling.
        
        Args:
            url (str): URL to request
            headers (dict, optional): HTTP headers
            
        Returns:
            requests.Response or None: Response object if successful, None otherwise
        """
        if not headers:
            headers = {'User-Agent': self.get_random_user_agent()}
            
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"Request error for {url}: {str(e)}")
            return None
    
    def scrape_all_sources(self):
        """
        Scrape all configured sources.
        
        Returns:
            dict: Dictionary of articles by source
                {
                    'source_name': [article1, article2, ...],
                    ...
                }
        """
        results = {}
        
        for source in self.sources:
            source_name = source['name']
            logger.info(f"Scraping source: {source_name}")
            
            # Determine scraping method based on source type
            if source['type'] == 'rss':
                articles = self.scrape_rss_feed(source)
            elif source['type'] == 'web':
                articles = self.scrape_web_page(source)
            else:
                logger.warning(f"Unsupported source type: {source['type']}")
                continue
            
            results[source_name] = articles
            
            # Be nice to the servers
            time.sleep(random.uniform(1, 3))
        
        return results
    
    def scrape_rss_feed(self, source_config):
        """
        Scrape articles from an RSS feed.
        
        Args:
            source_config (dict): Source configuration
            
        Returns:
            list: List of article dictionaries
        """
        articles = []
        
        try:
            feed_url = source_config['feed_url']
            feed = feedparser.parse(feed_url)
            
            if not feed.entries:
                logger.warning(f"No entries found in feed: {feed_url}")
                return articles
            
            logger.info(f"Found {len(feed.entries)} entries in feed: {feed_url}")
            
            for entry in feed.entries:
                # Extract basic info from feed
                article = {
                    'source': source_config['name'],
                    'title': entry.title,
                    'url': entry.link,
                    'author': entry.get('author', ''),
                    'published_date': entry.get('published', ''),
                    'tags': [tag.term for tag in entry.get('tags', [])] if hasattr(entry, 'tags') else []
                }
                
                # Get full content
                if 'content' in entry:
                    # Some feeds include full content
                    article['content'] = entry.content[0].value
                elif hasattr(entry, 'summary'):
                    # Some feeds include summaries that might contain partial content
                    article['content'] = entry.summary
                    
                    # For feeds like Volexity that might truncate content, fetch the full article
                    if source_config['name'] == 'Volexity Blog' or len(article['content']) < 1000:
                        full_content = self.fetch_article_content(article['url'], source_config)
                        if full_content:
                            article['content'] = full_content
                else:
                    # Otherwise fetch the full article
                    article['content'] = self.fetch_article_content(article['url'], source_config)
                
                # For Volexity specifically, enhance with source-specific processing
                if source_config['name'] == 'Volexity Blog':
                    # Add common tags for Volexity articles
                    if 'tags' not in article or not article['tags']:
                        article['tags'] = ['volexity', 'threat-research']
                
                articles.append(article)
            
        except Exception as e:
            logger.error(f"Error scraping RSS feed {source_config['feed_url']}: {str(e)}")
        
        return articles
    
    def scrape_web_page(self, source_config):
        """
        Scrape articles from a web page.
        
        Args:
            source_config (dict): Source configuration
            
        Returns:
            list: List of article dictionaries
        """
        articles = []
        
        try:
            url = source_config['url']
            response = self.make_request(url)
            
            if not response:
                return articles
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract article links based on source-specific selectors
            article_selector = source_config.get('article_selector', 'a')
            article_links = soup.select(article_selector)
            
            for link in article_links:
                href = link.get('href')
                
                if not href:
                    continue
                
                # Make absolute URL if relative
                if not href.startswith(('http://', 'https://')):
                    href = urllib.parse.urljoin(url, href)
                
                # Skip non-article links
                if not self.is_article_url(href, source_config):
                    continue
                
                # Basic article info
                article = {
                    'source': source_config['name'],
                    'title': link.text.strip() if link.text else 'Unknown Title',
                    'url': href,
                    'tags': []
                }
                
                # Fetch full article content
                article['content'] = self.fetch_article_content(href, source_config)
                
                # Skip if no content was retrieved
                if not article['content']:
                    continue
                
                articles.append(article)
            
        except Exception as e:
            logger.error(f"Error scraping web page {source_config['url']}: {str(e)}")
        
        return articles
    
    def fetch_article_content(self, url, source_config):
        """
        Fetch the full content of an article.
        
        Args:
            url (str): Article URL
            source_config (dict): Source configuration
            
        Returns:
            str: Article content or empty string if failed
        """
        try:
            response = self.make_request(url)
            
            if not response:
                return ""
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract content based on source-specific content selector
            content_selector = source_config.get('content_selector', 'article')
            content_element = soup.select_one(content_selector)
            
            if not content_element:
                logger.warning(f"Content element not found for {url}")
                return ""
            
            # Remove script, style, and iframe elements
            for element in content_element.select('script, style, iframe'):
                element.decompose()
            
            return content_element.get_text(separator='\n').strip()
            
        except Exception as e:
            logger.error(f"Error fetching article content from {url}: {str(e)}")
            return ""
    
    def is_article_url(self, url, source_config):
        """
        Check if a URL is likely to be an article.
        
        Args:
            url (str): URL to check
            source_config (dict): Source configuration
            
        Returns:
            bool: True if URL is likely an article, False otherwise
        """
        # Check if URL matches any include patterns
        if 'url_include_patterns' in source_config:
            return any(pattern in url for pattern in source_config['url_include_patterns'])
        
        # Check if URL matches any exclude patterns
        if 'url_exclude_patterns' in source_config:
            return not any(pattern in url for pattern in source_config['url_exclude_patterns'])
        
        # Default to assuming it's an article
        return True
