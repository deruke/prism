# PRISM: Predictive Reconnaissance & Intelligence Security Monitoring

A Python-based tool to aggregate data from multiple cyber threat intelligence sources, store that data over time in a SQLite database, and generate executive summaries of key findings to assist human analysts in tracking and analyzing threat actor campaigns. This is a proof of concept tool meant to be and example and a starting point for analysts to solve problems with AI assistance.

## Features

- Scrapes data from various cyber threat intelligence blogs, articles, and RSS feeds
- Extracts Indicators of Compromise (IOCs) such as IP addresses, domains, hashes, and more
- Stores raw data and IOCs in a SQLite database for historical tracking
- Generates AI-powered summaries for each article using Claude AI
- Creates executive summaries highlighting critical findings for non-technical stakeholders
- Supports multiple output formats (HTML, Markdown, JSON)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup

1. Clone the repository or download the source code:

```bash
git clone https://github.com/yourusername/cti-aggregator.git
cd cti-aggregator
```

2. Create a virtual environment (recommended):

With Python Virtual Environment: 

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
With conda:

```bash
conda create -n "prism" python=3.12
conda activate prism
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

4. Create a configuration file:

```bash
cp config.yaml.example config.yaml
```

5. Edit the configuration file with your settings:
   - Add your Anthropic API key
   - Configure your preferred intelligence sources
   - Adjust database and reporting settings as needed

## Usage

The Cyber Threat Intelligence Aggregator can be run in several modes:

### Scrape new intelligence

To collect new threat intelligence from the configured sources:

```bash
python main.py --scrape
```

### Analyze intelligence

To generate AI summaries for articles that don't have summaries yet:

```bash
python main.py --analyze
```

### Generate report

To create an executive summary report from recent intelligence:

```bash
python main.py --report
```

### Complete workflow

To run the entire workflow (scrape, analyze, and report) in a single command:

```bash
python main.py --full-run
```

### Help

To see all available options:

```bash
python main.py --help
```

## Configuration

The `config.yaml` file contains all the settings for the CTI Aggregator:

### Database Settings

```yaml
database:
  path: data/cti.db  # Path to SQLite database file
```

### Intelligence Sources

You can configure multiple sources of different types:

#### RSS Feeds

```yaml
sources:
  - name: Krebs on Security
    url: https://krebsonsecurity.com
    type: rss
    feed_url: https://krebsonsecurity.com/feed/
```

#### Web Pages

```yaml
sources:
  - name: CISA Alerts
    url: https://www.cisa.gov/news-events/cybersecurity-advisories
    type: web
    article_selector: a.usa-link
    content_selector: div.usa-prose
    url_include_patterns:
      - /cybersecurity-advisories/
```

### AI Settings

```yaml
ai:
  api_key: YOUR_ANTHROPIC_API_KEY_HERE
  model: claude-3-opus-20240229
```

### Reporting Settings

```yaml
reporting:
  output_directory: reports
  time_window_days: 30  # How many days of data to include in reports
```

## Database Schema

The tool uses a SQLite database with the following structure:

### Articles Table

Stores the raw articles and their summaries:

- `id`: Unique identifier
- `source`: Source name
- `title`: Article title
- `url`: Article URL
- `author`: Author name
- `published_date`: Publication date
- `content`: Article content
- `summary`: AI-generated summary
- `scraped_date`: Date when article was scraped
- `analyzed_date`: Date when article was analyzed

### IOCs Table

Stores Indicators of Compromise extracted from articles:

- `id`: Unique identifier
- `article_id`: Reference to the article
- `type`: IOC type (ip, domain, hash, etc.)
- `value`: IOC value
- `context`: Context around the IOC

### Tags Table

Stores additional metadata tags for articles:

- `id`: Unique identifier
- `article_id`: Reference to the article
- `tag`: Tag value

## Example Reports

The tool can generate reports in multiple formats:

### HTML Report

A formatted HTML report suitable for viewing in a browser with structured sections for:
- Executive Summary
- Key Threat Actors
- Critical IOCs
- Strategic Recommendations
- Recent Threat Intelligence

### Markdown Report

A Markdown-formatted report that can be viewed on GitHub or converted to other formats.

### JSON Report

A structured JSON format that can be ingested by other tools or applications.

## Requirements

The following Python libraries are required:

- requests
- beautifulsoup4
- feedparser
- pyyaml
- anthropic
- markdown
- jinja2

See `requirements.txt` for specific versions.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
