"""
Reporting module for the CTI Aggregator.
Handles generation of reports and executive summaries.
"""

import os
import logging
from datetime import datetime
import markdown
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates reports from executive summaries and article data"""
    
    def __init__(self, template_dir=None):
        """
        Initialize the report generator.
        
        Args:
            template_dir (str, optional): Directory containing report templates
        """
        # If template_dir not provided, use module directory's templates subfolder
        if template_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            template_dir = os.path.join(os.path.dirname(current_dir), 'templates')
        
        # Ensure template directory exists
        os.makedirs(template_dir, exist_ok=True)
        
        # Create default template if it doesn't exist
        default_template_path = os.path.join(template_dir, 'executive_summary.html')
        if not os.path.exists(default_template_path):
            self.create_default_template(default_template_path)
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    def create_default_template(self, template_path):
        """
        Create a default HTML template for executive summaries.
        
        Args:
            template_path (str): Path to save the template
        """
        default_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #ddd;
        }
        .logo {
            max-width: 200px;
            margin-bottom: 20px;
        }
        h1 {
            color: #2c3e50;
            margin-bottom: 10px;
        }
        h2 {
            color: #3498db;
            margin-top: 30px;
            margin-bottom: 15px;
            padding-bottom: 5px;
            border-bottom: 1px solid #eee;
        }
        h3 {
            color: #2c3e50;
        }
        .date {
            color: #7f8c8d;
            font-style: italic;
        }
        .executive-summary {
            background-color: #f9f9f9;
            padding: 20px;
            border-left: 4px solid #3498db;
            margin-bottom: 30px;
        }
        .key-section {
            background-color: #f5f5f5;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        .recommendations {
            background-color: #e8f4fc;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        .actor {
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px dotted #ddd;
        }
        .ioc {
            font-family: monospace;
            background-color: #f0f0f0;
            padding: 2px 5px;
            border-radius: 3px;
        }
        .article {
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #eee;
        }
        .article-source {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        .article-summary {
            margin-top: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        table, th, td {
            border: 1px solid #ddd;
        }
        th, td {
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 0.9em;
            color: #7f8c8d;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ title }}</h1>
        <p class="date">Generated on {{ date }}</p>
    </div>

    <div class="executive-summary">
        <h2>Executive Summary</h2>
        {{ executive_summary|safe }}
    </div>

    <div class="key-section">
        <h2>Key Threat Actors</h2>
        {% if key_actors %}
            {% for actor in key_actors %}
                <div class="actor">
                    <h3>{{ actor.name }}</h3>
                    <p>{{ actor.description }}</p>
                </div>
            {% endfor %}
        {% else %}
            <p>No key threat actors identified in this reporting period.</p>
        {% endif %}
    </div>

    <div class="key-section">
        <h2>Critical Indicators of Compromise</h2>
        {% if critical_iocs %}
            <table>
                <tr>
                    <th>Type</th>
                    <th>Value</th>
                    <th>Description</th>
                </tr>
                {% for ioc in critical_iocs %}
                    <tr>
                        <td>{{ ioc.type }}</td>
                        <td class="ioc">{{ ioc.value }}</td>
                        <td>{{ ioc.description }}</td>
                    </tr>
                {% endfor %}
            </table>
        {% else %}
            <p>No critical IOCs identified in this reporting period.</p>
        {% endif %}
    </div>

    <div class="recommendations">
        <h2>Strategic Recommendations</h2>
        {% if recommendations %}
            <ol>
                {% for rec in recommendations %}
                    <li>{{ rec }}</li>
                {% endfor %}
            </ol>
        {% else %}
            <p>No strategic recommendations for this reporting period.</p>
        {% endif %}
    </div>

    <h2>Recent Threat Intelligence</h2>
    {% if articles %}
        {% for article in articles %}
            <div class="article">
                <h3><a href="{{ article.url }}">{{ article.title }}</a></h3>
                <p class="article-source">Source: {{ article.source }} | {{ article.published_date }}</p>
                <div class="article-summary">
                    {{ article.summary|safe }}
                </div>
            </div>
        {% endfor %}
    {% else %}
        <p>No recent articles available.</p>
    {% endif %}

    <div class="footer">
        <p>This report was automatically generated by the Cyber Threat Intelligence Aggregator.</p>
        <p>Confidential - For internal use only</p>
    </div>
</body>
</html>
"""
        os.makedirs(os.path.dirname(template_path), exist_ok=True)
        with open(template_path, 'w') as f:
            f.write(default_template)
            
        logger.info(f"Created default template at {template_path}")
    
    def generate_report(self, executive_summary, articles, output_dir, format='html'):
        """
        Generate a report from an executive summary and articles.
        
        Args:
            executive_summary (dict): Executive summary data
            articles (list): List of article dictionaries
            output_dir (str): Directory to save the report
            format (str): Report format ('html', 'markdown', or 'json')
        
        Returns:
            str: Path to the generated report
        """
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate timestamp for filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create report based on format
        if format == 'html':
            return self.generate_html_report(executive_summary, articles, output_dir, timestamp)
        elif format == 'markdown':
            return self.generate_markdown_report(executive_summary, articles, output_dir, timestamp)
        elif format == 'json':
            return self.generate_json_report(executive_summary, articles, output_dir, timestamp)
        else:
            logger.warning(f"Unsupported format: {format}, defaulting to HTML")
            return self.generate_html_report(executive_summary, articles, output_dir, timestamp)
    
    def generate_html_report(self, executive_summary, articles, output_dir, timestamp):
        """
        Generate an HTML report.
        
        Args:
            executive_summary (dict): Executive summary data
            articles (list): List of article dictionaries
            output_dir (str): Directory to save the report
            timestamp (str): Timestamp for the filename
        
        Returns:
            str: Path to the generated report
        """
        try:
            # Convert markdown to HTML in article summaries
            for article in articles:
                if 'summary' in article and article['summary']:
                    article['summary'] = markdown.markdown(article['summary'])
            
            # Prepare template data
            template_data = {
                'title': f"PRISM Intelligence Executive Summary - {datetime.now().strftime('%B %d, %Y')}",
                'date': datetime.now().strftime('%B %d, %Y %H:%M'),
                'executive_summary': markdown.markdown(executive_summary.get('executive_summary', '')),
                'key_actors': executive_summary.get('key_actors', []),
                'critical_iocs': executive_summary.get('critical_iocs', []),
                'recommendations': executive_summary.get('recommendations', []),
                'articles': articles
            }
            
            # Debug log to see what's being passed to the template
            logger.debug(f"Template data - key_actors: {template_data['key_actors']}")
            logger.debug(f"Template data - critical_iocs: {template_data['critical_iocs']}")
            logger.debug(f"Template data - recommendations: {template_data['recommendations']}")
            
            # Add fallback data if sections are empty
            if not template_data['key_actors'] or len(template_data['key_actors']) == 0:
                template_data['key_actors'] = [
                    {
                        "name": "No Specific Threat Actors Identified",
                        "description": "The analyzed reports did not contain specific threat actor attributions."
                    }
                ]
                
            if not template_data['critical_iocs'] or len(template_data['critical_iocs']) == 0:
                template_data['critical_iocs'] = [
                    {
                        "type": "N/A",
                        "value": "N/A",
                        "description": "No critical IOCs were identified in the analyzed reports."
                    }
                ]
                
            if not template_data['recommendations'] or len(template_data['recommendations']) == 0:
                template_data['recommendations'] = [
                    "Maintain regular security patches and updates for all systems",
                    "Implement multi-factor authentication for critical services",
                    "Conduct regular security awareness training for employees",
                    "Review and update incident response plans",
                    "Maintain offline backups of critical data"
                ]
            
            # Render the template
            template = self.env.get_template('executive_summary.html')
            html_content = template.render(**template_data)
            
            # Save the HTML report
            output_path = os.path.join(output_dir, f'prism_report_{timestamp}.html')
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Generated HTML report: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating HTML report: {str(e)}")
            return None
    
    def generate_markdown_report(self, executive_summary, articles, output_dir, timestamp):
        """
        Generate a Markdown report.
        
        Args:
            executive_summary (dict): Executive summary data
            articles (list): List of article dictionaries
            output_dir (str): Directory to save the report
            timestamp (str): Timestamp for the filename
        
        Returns:
            str: Path to the generated report
        """
        try:
            # Build Markdown content
            md_content = f"# PRISM Intelligence Executive Summary\n\n"
            md_content += f"Generated: {datetime.now().strftime('%B %d, %Y %H:%M')}\n\n"
            
            # Executive Summary
            md_content += "## Executive Summary\n\n"
            md_content += executive_summary.get('executive_summary', 'No executive summary available.') + "\n\n"
            
            # Key Threat Actors
            md_content += "## Key Threat Actors\n\n"
            key_actors = executive_summary.get('key_actors', [])
            if key_actors:
                for actor in key_actors:
                    md_content += f"### {actor.get('name', 'Unknown Actor')}\n\n"
                    md_content += f"{actor.get('description', 'No description available.')}\n\n"
            else:
                md_content += "No key threat actors identified in this reporting period.\n\n"
            
            # Critical IOCs
            md_content += "## Critical Indicators of Compromise\n\n"
            critical_iocs = executive_summary.get('critical_iocs', [])
            if critical_iocs:
                md_content += "| Type | Value | Description |\n"
                md_content += "|------|-------|-------------|\n"
                for ioc in critical_iocs:
                    md_content += f"| {ioc.get('type', 'Unknown')} | `{ioc.get('value', 'N/A')}` | {ioc.get('description', 'No description')} |\n"
                md_content += "\n"
            else:
                md_content += "No critical IOCs identified in this reporting period.\n\n"
            
            # Strategic Recommendations
            md_content += "## Strategic Recommendations\n\n"
            recommendations = executive_summary.get('recommendations', [])
            if recommendations:
                for i, rec in enumerate(recommendations, 1):
                    md_content += f"{i}. {rec}\n"
                md_content += "\n"
            else:
                md_content += "No strategic recommendations for this reporting period.\n\n"
            
            # Recent Articles
            md_content += "## Recent Threat Intelligence\n\n"
            if articles:
                for article in articles:
                    md_content += f"### [{article['title']}]({article['url']})\n\n"
                    md_content += f"Source: {article.get('source', 'Unknown')} | {article.get('published_date', 'Unknown date')}\n\n"
                    md_content += article.get('summary', 'No summary available.') + "\n\n"
                    md_content += "---\n\n"
            else:
                md_content += "No recent articles available.\n\n"
            
            # Footer
            md_content += "---\n\n"
            md_content += "*This report was automatically generated by PRISM - Predictive Reconnaissance & Intelligence Security Monitoring.*\n\n"
            md_content += "**Confidential - For internal use only**\n"
            
            # Save the Markdown report
            output_path = os.path.join(output_dir, f'prism_report_{timestamp}.md')
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            logger.info(f"Generated Markdown report: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating Markdown report: {str(e)}")
            return None
    
    def generate_json_report(self, executive_summary, articles, output_dir, timestamp):
        """
        Generate a JSON report.
        
        Args:
            executive_summary (dict): Executive summary data
            articles (list): List of article dictionaries
            output_dir (str): Directory to save the report
            timestamp (str): Timestamp for the filename
        
        Returns:
            str: Path to the generated report
        """
        try:
            # Prepare report data
            report_data = {
                'title': f"PRISM Intelligence Executive Summary - {datetime.now().strftime('%B %d, %Y')}",
                'generated_date': datetime.now().isoformat(),
                'executive_summary': executive_summary,
                'articles': [{
                    'id': article.get('id'),
                    'title': article.get('title'),
                    'url': article.get('url'),
                    'source': article.get('source'),
                    'published_date': article.get('published_date'),
                    'summary': article.get('summary'),
                    'iocs': article.get('iocs', {})
                } for article in articles]
            }
            
            # Save the JSON report
            output_path = os.path.join(output_dir, f'prism_report_{timestamp}.json')
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2)
            
            logger.info(f"Generated JSON report: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating JSON report: {str(e)}")
            return None