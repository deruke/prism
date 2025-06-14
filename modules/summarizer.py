"""
Summarizer module for PRISM.
Handles AI-powered summarization of threat intelligence articles.
"""

import logging
import json
import re
import anthropic

logger = logging.getLogger(__name__)

class ArticleSummarizer:
    """Generates summaries for individual threat intelligence articles"""
    
    def __init__(self, api_key, model="claude-3-opus-20240229"):
        """
        Initialize the article summarizer.
        
        Args:
            api_key (str): Claude AI API key
            model (str): Claude model to use
        """
        self.api_key = api_key
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def summarize(self, title, content, iocs=None):
        """
        Generate a summary for an article using Claude AI.
        
        Args:
            title (str): Article title
            content (str): Article content
            iocs (dict, optional): Extracted IOCs
        
        Returns:
            str: Generated summary
        """
        try:
            # Prepare IOCs section if available
            iocs_text = ""
            if iocs:
                iocs_text = "Extracted Indicators of Compromise (IOCs):\n"
                for ioc_type, ioc_list in iocs.items():
                    iocs_text += f"\n{ioc_type.upper()}:\n"
                    for ioc in ioc_list:
                        iocs_text += f"- {ioc['value']}"
                        if ioc.get('context'):
                            iocs_text += f" (Context: {ioc['context']})"
                        iocs_text += "\n"
            
            # Check for source-specific customization
            if "Volexity" in title or "volexity" in title.lower():
                source_type = "Volexity"
            else:
                source_type = "general"
                
            if source_type == "Volexity":
                prompt = f"""You are a cybersecurity threat intelligence analyst. You need to create a concise, technical summary of the following Volexity threat intelligence article. 

Title: {title}

Content:
{content}

{iocs_text}

Volexity is known for detailed threat actor attribution and technical analysis of advanced threats. Please provide a summary that:
1. Identifies the key threat actors mentioned (including any APT group names or attributions)
2. Extracts the specific TTPs (Tactics, Techniques, and Procedures)
3. Summarizes the technical details of the attack, malware, or vulnerability
4. Highlights the most significant IOCs and any MITRE ATT&CK mappings
5. Notes the industries, sectors, or geographic regions targeted
6. Explains the potential impact, severity, and recommended mitigations

Your summary should be technical but clear, aimed at cybersecurity professionals. Keep the summary concise (250-350 words) and emphasize attribution details and actionable intelligence.
"""
            else:
                prompt = f"""You are a cybersecurity threat intelligence analyst. You need to create a concise, technical summary of the following threat intelligence article. 

Title: {title}

Content:
{content}

{iocs_text}

Please provide a summary that:
1. Identifies the key threat actors, malware, or attack vectors
2. Summarizes the technical details of the attack or vulnerability
3. Highlights the most significant IOCs
4. Notes the industries or sectors targeted
5. Explains the potential impact and severity
6. Provides any recommended mitigations or defensive measures

Your summary should be technical but clear, aimed at cybersecurity professionals. Keep the summary concise (250-350 words) and focus on actionable intelligence.
"""

            # Call the Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.0,  # Use a low temperature for more deterministic output
                system="You are a cybersecurity threat intelligence analyst assistant. Provide accurate, concise, technical summaries of threat intelligence.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract the summary
            summary = response.content[0].text.strip()
            logger.info(f"Generated summary for article: {title}")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return f"Error generating summary: {str(e)}"


class ExecutiveSummarizer:
    """Generates executive summaries from multiple article summaries"""
    
    def __init__(self, api_key, model="claude-3-opus-20240229"):
        """
        Initialize the executive summarizer.
        
        Args:
            api_key (str): Claude AI API key
            model (str): Claude model to use
        """
        self.api_key = api_key
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def create_summary(self, articles, max_articles=20):
        """
        Create an executive summary from multiple articles.
        
        Args:
            articles (list): List of article dictionaries with summaries
            max_articles (int): Maximum number of articles to include
        
        Returns:
            dict: Dictionary containing:
                - executive_summary: Overall summary
                - key_actors: List of key threat actors
                - critical_iocs: List of most critical IOCs
                - recommendations: List of recommendations
        """
        try:
            # Limit the number of articles to avoid token limits
            articles = articles[:max_articles]
            
            # Extract summaries and titles
            article_data = []
            for article in articles:
                article_data.append({
                    'title': article['title'],
                    'summary': article['summary'],
                    'source': article['source'],
                    'url': article['url'],
                    'published_date': article.get('published_date', 'Unknown')
                })
                
                # Also collect IOCs for better summary generation
                if 'iocs' in article and article['iocs']:
                    # Extract top IOCs for each type 
                    top_iocs = {}
                    for ioc_type, iocs in article['iocs'].items():
                        if iocs:
                            # Take up to 5 IOCs of each type
                            top_iocs[ioc_type] = iocs[:5]
                    
                    if top_iocs:
                        article_data[-1]['iocs'] = top_iocs
            
            # Construct the prompt
            prompt = f"""You are a senior cybersecurity threat intelligence analyst preparing an executive summary for C-level executives and board members. You have the following summaries of recent threat intelligence articles:

{json.dumps(article_data, indent=2)}

Please create an executive summary that:

1. Identifies the 3-5 most significant cybersecurity threats from these articles
2. Focuses on business impact rather than technical details
3. Highlights industry trends and emerging threats
4. Identifies the most critical threat actors and their targets
5. Provides clear, actionable recommendations for organizational security

Format your response as a structured JSON object with the following keys:
- executive_summary: The main executive summary text (400-600 words) - this should be ONLY the summary text, not references to other sections
- key_actors: Array of objects with "name" and "description" fields for each key threat actor
- critical_iocs: Array of objects with "type", "value", and "description" fields for the most important IOCs
- recommendations: Array of strategic recommendation strings (3-5 bullet points)

Example format:
{{
  "executive_summary": "Text of the executive summary...",
  "key_actors": [
    {{
      "name": "APT29",
      "description": "Russian state-sponsored group targeting government and defense sectors"
    }},
    {{
      "name": "FIN7",
      "description": "Financially motivated actor targeting retail and hospitality"
    }}
  ],
  "critical_iocs": [
    {{
      "type": "domain",
      "value": "malicious-domain.com",
      "description": "C2 server for Emotet campaign"
    }},
    {{
      "type": "ip",
      "value": "192.168.1.1",
      "description": "Scanning host for vulnerability XYZ"
    }}
  ],
  "recommendations": [
    "Implement MFA across all remote access services",
    "Patch vulnerable systems against CVE-2023-12345 immediately",
    "Update EDR signatures to detect the Lazarus campaign IOCs"
  ]
}}

Keep the executive summary non-technical and easily understandable by executives without cybersecurity background.
"""

            # Call the Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.3,
                system="""You are a senior cybersecurity threat intelligence analyst assistant. Distill complex technical information into clear, business-focused executive summaries. 

Always provide structured output in valid JSON format when requested. Be concise and direct in your summaries.

For the executive_summary field:
1. Include ONLY the actual summary text
2. Do NOT include phrases like "Here is the executive summary" or "Based on the analyzed intelligence" 
3. Do NOT include references to the JSON structure or other sections
4. Do NOT include the words "executive_summary", "key_actors", "critical_iocs", or "recommendations" in your summary text
5. Write in a clear, professional style appropriate for business executives

For the key_actors, critical_iocs, and recommendations fields:
1. Follow the exact format requested
2. Be specific and detailed for each entry
3. Ensure information is accurate and actionable""",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract and parse the JSON response
            response_text = response.content[0].text.strip()
            
            # Find and extract the JSON part
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                
                # Clean up the JSON text to handle control characters
                json_text = json_text.replace('\r\n', '\n')
                json_text = json_text.replace('\r', '\n')
                
                # Remove problematic control characters
                json_text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', json_text)
                
                try:
                    summary_data = json.loads(json_text)
                    logger.info("Generated executive summary successfully")
                    
                    # Ensure all expected fields are present
                    if 'executive_summary' not in summary_data:
                        summary_data['executive_summary'] = "Executive summary could not be generated."
                        
                    if 'key_actors' not in summary_data or not summary_data['key_actors']:
                        summary_data['key_actors'] = [
                            {
                                "name": "Unknown Threat Actor",
                                "description": "No specific threat actors were identified in the analyzed reports."
                            }
                        ]
                        
                    if 'critical_iocs' not in summary_data or not summary_data['critical_iocs']:
                        # Extract some IOCs from the articles as a fallback
                        critical_iocs = []
                        for article in articles:
                            if 'iocs' in article and article['iocs']:
                                for ioc_type, iocs in article['iocs'].items():
                                    if iocs and len(iocs) > 0:
                                        critical_iocs.append({
                                            "type": ioc_type,
                                            "value": iocs[0]['value'],
                                            "description": f"Found in {article['title']}"
                                        })
                                        if len(critical_iocs) >= 3:
                                            break
                                if len(critical_iocs) >= 3:
                                    break
                        
                        if critical_iocs:
                            summary_data['critical_iocs'] = critical_iocs
                        else:
                            summary_data['critical_iocs'] = [
                                {
                                    "type": "N/A",
                                    "value": "N/A",
                                    "description": "No critical IOCs were identified in the analyzed reports."
                                }
                            ]
                    
                    if 'recommendations' not in summary_data or not summary_data['recommendations']:
                        summary_data['recommendations'] = [
                            "Maintain regular security patches and updates for all systems",
                            "Implement multi-factor authentication for critical services",
                            "Conduct regular security awareness training for employees",
                            "Review and update incident response plans",
                            "Maintain offline backups of critical data"
                        ]
                    
                    return summary_data
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.debug(f"Problematic JSON text (first 500 chars): {json_text[:500]}")
                    
                    # Try alternative parsing approach
                    try:
                        # Sometimes Claude wraps JSON in markdown code blocks
                        if '```json' in response_text and '```' in response_text:
                            json_start = response_text.find('```json') + 7
                            json_end = response_text.find('```', json_start)
                            if json_end > json_start:
                                json_text = response_text[json_start:json_end].strip()
                                # Clean control characters again
                                json_text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', json_text)
                                summary_data = json.loads(json_text)
                                logger.info("Successfully parsed JSON from markdown code block")
                                return summary_data
                    except json.JSONDecodeError:
                        pass
                        
                    # Try extracting individual sections manually if JSON parsing completely fails
                    logger.warning("Attempting manual section extraction from response")
                    return self.extract_sections_manually(response_text, articles)
            
            # Fallback if JSON parsing fails
            logger.warning("Using fallback for executive summary")
            return {
                'executive_summary': "Based on the analyzed threat intelligence, several key cybersecurity threats have emerged that require immediate attention. These include sophisticated ransomware operations, targeted attacks on critical infrastructure, exploitation of zero-day vulnerabilities, and advanced persistent threats from state-sponsored actors. Organizations should implement robust security measures including multi-factor authentication, regular patching, threat hunting, and comprehensive security awareness training to mitigate these evolving threats.",
                'key_actors': [
                    {
                        "name": "Various Threat Actors",
                        "description": "Multiple threat actors were mentioned in the reports but specific details could not be extracted."
                    }
                ],
                'critical_iocs': [
                    {
                        "type": "various",
                        "value": "See individual reports",
                        "description": "Various IOCs were identified in the individual reports."
                    }
                ],
                'recommendations': [
                    "Maintain regular security patches and updates for all systems",
                    "Implement multi-factor authentication for critical services",
                    "Conduct regular security awareness training for employees",
                    "Review and update incident response plans",
                    "Maintain offline backups of critical data"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error generating executive summary: {str(e)}")
            return {
                'executive_summary': f"Error generating executive summary: {str(e)}",
                'key_actors': [
                    {
                        "name": "Error",
                        "description": "An error occurred while generating the threat actor information."
                    }
                ],
                'critical_iocs': [
                    {
                        "type": "error",
                        "value": "error",
                        "description": "An error occurred while generating the IOC information."
                    }
                ],
                'recommendations': [
                    "Unable to generate recommendations due to an error.",
                    "Please check the system logs for more information."
                ]
            }
    
    def extract_sections_manually(self, response_text, articles):
        """
        Manually extract sections from the response when JSON parsing fails.
        
        Args:
            response_text (str): The raw response text from Claude
            articles (list): List of articles for fallback IOC extraction
            
        Returns:
            dict: Dictionary with extracted sections
        """
        import re
        
        logger.info("Attempting manual extraction of executive summary sections")
        
        # Initialize result structure
        result = {
            'executive_summary': "",
            'key_actors': [],
            'critical_iocs': [],
            'recommendations': []
        }
        
        try:
            # Try to extract executive summary (look for text before any structured sections)
            exec_match = re.search(r'executive[_\s]*summary["\s]*:?\s*["\s]*([^"}\]]+)', response_text, re.IGNORECASE | re.DOTALL)
            if exec_match:
                exec_text = exec_match.group(1).strip()
                # Clean up common artifacts
                exec_text = re.sub(r'[,\]\}]+, ', exec_text)  # Remove trailing punctuation
                exec_text = exec_text.replace('\n', ' ').strip()
                if len(exec_text) > 50:  # Only use if it's substantial
                    result['executive_summary'] = exec_text
            
            # Extract key actors
            actors_section = re.search(r'key[_\s]*actors["\s]*:?\s*\[(.*?)\]', response_text, re.IGNORECASE | re.DOTALL)
            if actors_section:
                actors_text = actors_section.group(1)
                # Look for name/description pairs
                actor_matches = re.findall(r'["\s]*name["\s]*:?\s*["\s]*([^"}\],]+)["\s]*.*?["\s]*description["\s]*:?\s*["\s]*([^"}\]]+)', actors_text, re.IGNORECASE | re.DOTALL)
                for name, desc in actor_matches:
                    result['key_actors'].append({
                        'name': name.strip(),
                        'description': desc.strip()
                    })
            
            # Extract IOCs
            iocs_section = re.search(r'critical[_\s]*iocs["\s]*:?\s*\[(.*?)\]', response_text, re.IGNORECASE | re.DOTALL)
            if iocs_section:
                iocs_text = iocs_section.group(1)
                # Look for type/value/description triplets
                ioc_matches = re.findall(r'["\s]*type["\s]*:?\s*["\s]*([^"}\],]+)["\s]*.*?["\s]*value["\s]*:?\s*["\s]*([^"}\],]+)["\s]*.*?["\s]*description["\s]*:?\s*["\s]*([^"}\]]+)', iocs_text, re.IGNORECASE | re.DOTALL)
                for ioc_type, value, desc in ioc_matches:
                    result['critical_iocs'].append({
                        'type': ioc_type.strip(),
                        'value': value.strip(),
                        'description': desc.strip()
                    })
            
            # Extract recommendations
            recs_section = re.search(r'recommendations["\s]*:?\s*\[(.*?)\]', response_text, re.IGNORECASE | re.DOTALL)
            if recs_section:
                recs_text = recs_section.group(1)
                # Look for quoted strings
                rec_matches = re.findall(r'["\s]*([^"}\],]+)["\s]*', recs_text)
                for rec in rec_matches:
                    clean_rec = rec.strip().rstrip(',')
                    if len(clean_rec) > 10:  # Only include substantial recommendations
                        result['recommendations'].append(clean_rec)
            
            # Apply fallbacks for empty sections
            if not result['executive_summary']:
                result['executive_summary'] = "Based on the analyzed threat intelligence, several key cybersecurity threats have emerged that require immediate attention. Organizations should implement robust security measures to mitigate these evolving threats."
            
            if not result['key_actors']:
                result['key_actors'] = [
                    {
                        "name": "Various Threat Actors",
                        "description": "Multiple threat actors were mentioned in the reports but specific details could not be extracted."
                    }
                ]
            
            if not result['critical_iocs']:
                # Try to extract some IOCs from the articles as fallback
                critical_iocs = []
                for article in articles:
                    if 'iocs' in article and article['iocs']:
                        for ioc_type, iocs in article['iocs'].items():
                            if iocs and len(iocs) > 0:
                                critical_iocs.append({
                                    "type": ioc_type,
                                    "value": iocs[0]['value'],
                                    "description": f"Found in {article['title']}"
                                })
                                if len(critical_iocs) >= 3:
                                    break
                        if len(critical_iocs) >= 3:
                            break
                
                if critical_iocs:
                    result['critical_iocs'] = critical_iocs
                else:
                    result['critical_iocs'] = [
                        {
                            "type": "various",
                            "value": "See individual reports",
                            "description": "Various IOCs were identified in the individual reports."
                        }
                    ]
            
            if not result['recommendations']:
                result['recommendations'] = [
                    "Maintain regular security patches and updates for all systems",
                    "Implement multi-factor authentication for critical services",
                    "Conduct regular security awareness training for employees",
                    "Review and update incident response plans",
                    "Maintain offline backups of critical data"
                ]
            
            logger.info("Manual extraction completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Manual extraction failed: {str(e)}")
            # Return basic fallback structure
            return {
                'executive_summary': "Manual extraction of executive summary failed. Please check logs for details.",
                'key_actors': [
                    {
                        "name": "Extraction Error",
                        "description": "Unable to extract threat actor information due to parsing errors."
                    }
                ],
                'critical_iocs': [
                    {
                        "type": "error",
                        "value": "extraction_failed",
                        "description": "Unable to extract IOC information due to parsing errors."
                    }
                ],
                'recommendations': [
                    "Manual extraction failed. Please review the raw response data.",
                    "Consider adjusting the Claude API prompt for better JSON formatting."
                ]
            }