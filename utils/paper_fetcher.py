import arxiv
import pandas as pd
from typing import List, Dict
import random
import time
import streamlit as st

class PaperFetcher:
    def __init__(self):
        self.client = arxiv.Client()

    def fetch_papers(self, count: int = 1000, topic: str = None) -> List[Dict]:
        """Fetch papers from arXiv based on topic or randomly if no topic provided."""
        papers = []
        batch_size = 25  # Smaller batch size to avoid rate limits
        max_retries = 3
        categories = ["cs", "physics", "math"]
        retry_delay = 2  # Initial delay between retries in seconds
        
        st.progress(0.0, text="Initializing paper fetch...")
        
        while len(papers) < count and max_retries > 0:
            try:
                if topic:
                    # Search by topic across all categories
                    query = f"all:{topic}"
                else:
                    # Randomly select a category for diversity
                    category = random.choice(categories)
                    query = f"cat:{category}.*"
                
                search = arxiv.Search(
                    query=query,
                    max_results=min(batch_size, count - len(papers)),
                    sort_by=arxiv.SortCriterion.Relevance if topic else arxiv.SortCriterion.SubmittedDate
                )
                
                batch_papers = []
                for result in self.client.results(search):
                    batch_papers.append({
                        'title': result.title,
                        'abstract': result.summary,
                        'authors': ', '.join([author.name for author in result.authors]),
                        'published': result.published,
                        'url': result.pdf_url,
                        'categories': result.categories
                    })
                    
                papers.extend(batch_papers)
                progress = len(papers) / count
                st.progress(progress, text=f"Fetched {len(papers)}/{count} papers...")
                
                if topic:
                    print(f"Successfully fetched {len(batch_papers)} papers for topic: {topic}")
                else:
                    print(f"Successfully fetched {len(batch_papers)} papers from category: {query}")
                    
                # Add delay between batches to avoid rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"Error fetching papers: {str(e)}")
                max_retries -= 1
                time.sleep(1)  # Add delay between retries
        
        # Ensure we don't exceed the requested count
        if len(papers) > count:
            papers = random.sample(papers, count)
        elif len(papers) < count:
            print(f"Warning: Only able to fetch {len(papers)} papers out of {count} requested")
            
        return papers

    def create_dataframe(self, papers: List[Dict]) -> pd.DataFrame:
        """Convert papers list to DataFrame."""
        return pd.DataFrame(papers)