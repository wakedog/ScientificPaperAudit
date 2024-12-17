import arxiv
import pandas as pd
from typing import List, Dict
import random

class PaperFetcher:
    def __init__(self):
        self.client = arxiv.Client()

    def fetch_random_papers(self, count: int = 1000) -> List[Dict]:
        """Fetch random papers from arXiv."""
        # Search with broad categories to get diverse papers
        search = arxiv.Search(
            query="cat:cs.* OR cat:physics.* OR cat:math.*",
            max_results=count * 2  # Fetch more to randomly sample
        )

        papers = []
        for result in self.client.results(search):
            papers.append({
                'title': result.title,
                'abstract': result.summary,
                'authors': ', '.join([author.name for author in result.authors]),
                'published': result.published,
                'url': result.pdf_url,
                'categories': result.categories
            })

        # Randomly sample required number of papers
        if len(papers) > count:
            papers = random.sample(papers, count)

        return papers

    def create_dataframe(self, papers: List[Dict]) -> pd.DataFrame:
        """Convert papers list to DataFrame."""
        return pd.DataFrame(papers)
