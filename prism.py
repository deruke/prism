#!/usr/bin/env python3
"""
PRISM: Predictive Reconnaissance & Intelligence Security Monitoring

This tool scrapes threat intelligence from various sources, extracts IOCs, 
stores data in SQLite, and generates executive summaries.
"""

import argparse
import logging
import os
import sys
from datetime import datetime

from modules.config import load_config
from modules.database import DatabaseManager
from modules.scraper import ThreatIntelScraper
from modules.ioc_extractor import IOCExtractor
from modules.summarizer import ArticleSummarizer, ExecutiveSummarizer
from modules.reporting import ReportGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("prism.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='PRISM: Predictive Reconnaissance & Intelligence Security Monitoring')
    parser.add_argument('--config', type=str, default='config.yaml', 
                        help='Path to configuration file')
    parser.add_argument('--scrape', action='store_true', 
                        help='Scrape new intelligence from sources')
    parser.add_argument('--analyze', action='store_true', 
                        help='Analyze and summarize scraped intelligence')
    parser.add_argument('--report', action='store_true', 
                        help='Generate executive summary report')
    parser.add_argument('--full-run', action='store_true', 
                        help='Run complete workflow (scrape, analyze, report)')
    return parser.parse_args()

def main():
    """Main function to orchestrate the PRISM workflow"""
    args = parse_arguments()
    
    try:
        # Load configuration
        config = load_config(args.config)
        logger.info(f"Configuration loaded from {args.config}")
        
        # Initialize database
        db_manager = DatabaseManager(config['database']['path'])
        db_manager.initialize_database()
        logger.info("Database initialized successfully")
        
        # Determine which operations to perform
        run_scrape = args.scrape or args.full_run
        run_analyze = args.analyze or args.full_run
        run_report = args.report or args.full_run
        
        # If no specific operation was requested, show help
        if not (run_scrape or run_analyze or run_report):
            logger.info("No operation specified. Use --scrape, --analyze, --report, or --full-run")
            print("No operation specified. Use --scrape, --analyze, --report, or --full-run")
            return
        
        # 1. Scrape new intelligence
        if run_scrape:
            logger.info("Starting scraping operation")
            scraper = ThreatIntelScraper(config['sources'])
            
            for source_name, articles in scraper.scrape_all_sources().items():
                logger.info(f"Scraped {len(articles)} articles from {source_name}")
                
                for article in articles:
                    # Extract IOCs
                    ioc_extractor = IOCExtractor()
                    iocs = ioc_extractor.extract_from_text(article['content'])
                    article['iocs'] = iocs
                    
                    # Store article in database
                    article_id = db_manager.store_article(article)
                    
                    # Store IOCs in database
                    if iocs:
                        db_manager.store_iocs(article_id, iocs)
            
            logger.info("Scraping operation completed")
        
        # 2. Analyze and summarize articles
        if run_analyze:
            logger.info("Starting analysis operation")
            
            # Get articles without summaries
            articles = db_manager.get_articles_without_summary()
            logger.info(f"Found {len(articles)} articles to analyze")
            
            if articles:
                article_summarizer = ArticleSummarizer(config['ai']['api_key'])
                
                for article in articles:
                    article_id = article['id']
                    logger.info(f"Analyzing article ID: {article_id}")
                    
                    # Generate summary using AI
                    summary = article_summarizer.summarize(
                        title=article['title'],
                        content=article['content'],
                        iocs=db_manager.get_iocs_for_article(article_id)
                    )
                    
                    # Store summary in database
                    db_manager.update_article_summary(article_id, summary)
                    
                logger.info("Analysis operation completed")
            else:
                logger.info("No articles require analysis")
        
        # 3. Generate executive summary report
        if run_report:
            logger.info("Starting report generation")
            
            # Get recent articles with summaries
            recent_articles = db_manager.get_recent_articles_with_summary(
                days=config['reporting']['time_window_days']
            )
            
            if recent_articles:
                # Generate executive summary
                executive_summarizer = ExecutiveSummarizer(config['ai']['api_key'])
                executive_summary = executive_summarizer.create_summary(recent_articles)
                
                # Generate report file
                report_generator = ReportGenerator()
                report_path = report_generator.generate_report(
                    executive_summary=executive_summary,
                    articles=recent_articles,
                    output_dir=config['reporting']['output_directory']
                )
                
                logger.info(f"Report generated: {report_path}")
            else:
                logger.info("No recent articles with summaries available for reporting")
        
                logger.info("PRISM analysis completed successfully")
    
    except Exception as e:
        logger.error(f"Error in PRISM: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
