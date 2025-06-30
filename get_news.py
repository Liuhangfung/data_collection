import os
import requests
from datetime import datetime
from dotenv import load_dotenv
import json
import time
from supabase import create_client, Client

# Load environment variables
load_dotenv()

PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def clean_headline(headline):
    """
    Clean the headline by removing 'Headline:' prefix and extra whitespace
    """
    # Remove 'Headline:' prefix if it exists
    if headline.lower().startswith('headline:'):
        headline = headline[len('headline:'):]
    # Remove any leading/trailing whitespace
    return headline.strip()

def get_financial_news():
    """
    Get cryptocurrency news from Perplexity API
    """
    url = "https://api.perplexity.ai/chat/completions"
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}"
    }
    
    prompt = """Please provide 10 separate cryptocurrency news items from the last 24-48 hours. For each news item, include:

1. A one-sentence summary
2. Detailed information including:
   - Price movements and market data
   - Trading volume and market cap changes
   - Regulatory updates
   - Technology developments
   - Institutional adoption news
   - DeFi and NFT market updates
   - Source URL

Format each news item as:
NEWS ITEM 1:
SUMMARY: [one sentence]
DETAILS:
- [point 1 with source URL]
- [point 2 with source URL]

NEWS ITEM 2:
[Same format as above]

... and so on for all 10 items.

Focus on:
- Major cryptocurrencies (Bitcoin, Ethereum, etc.)
- Significant market movements
- Regulatory developments
- Institutional adoption
- DeFi and NFT market trends
- Technology updates
- Market analysis and predictions

Each news item should be distinct and significant, with verified information and source links."""

    data = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "system",
                "content": "You are a cryptocurrency market expert. Provide accurate, well-sourced information about recent crypto market developments, focusing on significant price movements, regulatory updates, and technological advancements."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error getting news from Perplexity: {e}")
        if hasattr(e, 'response'):
            print(f"Response content: {e.response.text}")
        return None

def process_news_item_with_chatgpt(news_item):
    """
    Process a single crypto news item through ChatGPT to create a detailed, blog-style article with a headline, subtitle, and table of contents, all in Markdown.
    """
    url = "https://api.openai.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f'''Write a professional, blog-style cryptocurrency news article based on the following news item.
- The headline should be the first line, written as plain text only (no Markdown formatting, no prefix, no heading symbols).
- All other output (subtitle, table of contents, and article content) must be formatted in Markdown, as it will be stored and rendered as Markdown.
- On the second line, write a one-sentence subtitle/summary of the article (no prefix), using Markdown (e.g., bold or italic).
- Then include a Table of Contents after the subtitle, formatted as a Markdown list.
- **Dynamically generate unique and relevant section titles for the Table of Contents and article, based on the specific content and context of the news item. Do not use the same set of section titles every time.**
- Use clear subheadings for each section, using Markdown headings (## Subtitle).
- Each sub section must be at least 300 words.
- Use Markdown formatting for all structure (headings, bullet points, links, emphasis, etc.).
- Use blank lines between sections.
- The article should be engaging, informative, and suitable for a crypto news website.
- Include all source links from the original news, formatted as Markdown links.
- The headline should be the first line (plain text), the subtitle should be the second line (Markdown), the table of contents should be the third line (Markdown), followed by the rest of the article (Markdown).

Here is the news item:
{news_item}'''

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error processing news item with ChatGPT: {e}")
        if hasattr(e, 'response'):
            print(f"Response content: {e.response.text}")
        return None

def extract_urls(text):
    """
    Extract URLs from the text
    """
    # Simple URL extraction - you might want to use a more robust method
    import re
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    return urls[0] if urls else None

def save_to_supabase(headline, subtitle, table_content, article, url_link):
    """
    Save article to Supabase, including subtitle and table_content
    """
    try:
        # Clean the headline before saving
        clean_headline_text = clean_headline(headline)
        
        data = {
            'headline': clean_headline_text,
            'subtitle': subtitle,
            'table_content': table_content,
            'article': article,
            'url_link': url_link,
            'created_at': datetime.now().isoformat()
        }
        
        result = supabase.table('news').insert(data).execute()
        print(f"Successfully saved article: {clean_headline_text}")
        return True
    except Exception as e:
        print(f"Error saving to Supabase: {e}")
        return False

def split_news_items(news_content):
    """
    Split the news content into individual news items
    """
    # Split by "NEWS ITEM" markers
    items = news_content.split("NEWS ITEM")
    # Remove empty items and clean up
    return [item.strip() for item in items if item.strip()]

def main():
    # Get news from Perplexity
    print("Fetching financial news...")
    news_content = get_financial_news()
    
    if news_content:
        # Split into individual news items
        news_items = split_news_items(news_content)
        
        print(f"Processing {len(news_items)} news items...")
        
        # Process each news item separately
        for i, news_item in enumerate(news_items, 1):
            print(f"Processing news item {i}...")
            article = process_news_item_with_chatgpt(news_item)
            
            if article:
                # Extract headline (first line), subtitle (second line), table of contents (third line), and URL
                lines = article.split('\n')
                headline = lines[0].strip() if len(lines) > 0 else ""
                subtitle = lines[1].strip() if len(lines) > 1 else ""
                table_content = lines[2].strip() if len(lines) > 2 else ""
                url_link = extract_urls(news_item)
                
                # Save to Supabase
                if save_to_supabase(headline, subtitle, table_content, article, url_link):
                    print(f"Successfully processed and saved news item {i}")
                else:
                    print(f"Failed to save news item {i}")
            else:
                print(f"Failed to process news item {i}")
            
            # Add a small delay between API calls to avoid rate limiting
            time.sleep(1)
        
        print("Done! Check your Supabase database for the new articles.")
    else:
        print("Failed to fetch news from Perplexity")

if __name__ == "__main__":
    main()