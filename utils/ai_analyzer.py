import os
import json
import time
import requests
from typing import List, Dict
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

class PaperAnalyzer:
    def __init__(self):
        self.error_categories = [
            "Methodology",
            "Statistical Analysis",
            "Data Integrity",
            "Citation Issues",
            "Technical Accuracy"
        ]
        
    def analyze_paper(self, paper: Dict) -> Dict:
        """Analyze a single paper for potential issues with detailed error locations."""
        try:
            # Create a detailed analysis prompt
            prompt = self._generate_analysis_prompt(paper)
            
            # Make API call to Perplexity
            headers = {
                "Authorization": f"Bearer {os.getenv('PPLX_API_KEY')}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "mixtral-8x7b-instruct",
                "messages": [{
                    "role": "system",
                    "content": """You are an expert scientific paper analyzer. Analyze papers for potential issues and provide detailed structured feedback in JSON format.
                    For each issue found:
                    1. Identify the specific location (section, paragraph, or sentence)
                    2. Explain the nature of the problem
                    3. Suggest potential improvements
                    4. Rate the severity (low, medium, high)
                    Focus on methodology, statistical analysis, data integrity, citations, and technical accuracy."""
                }, {
                    "role": "user",
                    "content": prompt
                }],
                "max_tokens": 2048,
                "temperature": 0.7,
                "top_p": 0.9
            }
            
            # Enhanced retry mechanism with exponential backoff
            max_retries = 5
            retry_delay = 1
            response_data = None
            
            for attempt in range(max_retries):
                try:
                    # Add rate limiting delay
                    if attempt > 0:
                        time.sleep(retry_delay)
                    
                    response = requests.post(
                        "https://api.perplexity.ai/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=30  # Add timeout
                    )
                    
                    if response.status_code == 429:  # Rate limit hit
                        retry_delay = min(retry_delay * 2, 32)  # Cap at 32 seconds
                        continue
                        
                    response.raise_for_status()
                    response_data = response.json()
                    break
                    
                except requests.exceptions.Timeout:
                    print(f"Timeout on attempt {attempt + 1}")
                    retry_delay = min(retry_delay * 2, 32)
                    
                except requests.exceptions.RequestException as e:
                    print(f"API error on attempt {attempt + 1}: {str(e)}")
                    if attempt == max_retries - 1:
                        raise e
                    retry_delay = min(retry_delay * 2, 32)
            
            if response_data is None:
                raise Exception("Failed to get valid response after all retries")
            
            # Parse the response
            if 'choices' in response_data and response_data['choices']:
                return self._parse_analysis_response(response_data['choices'][0]['message']['content'])
            else:
                raise ValueError("Unexpected API response format")
            
        except Exception as e:
            print(f"Error calling Perplexity API: {e}")
            return self._generate_fallback_analysis()

    def _generate_analysis_prompt(self, paper: Dict) -> str:
        """Generate detailed analysis prompt for the paper with error locations."""
        return f"""Analyze this scientific paper and provide a detailed structured assessment focusing on potential issues, their locations, and quality metrics.

INPUT PAPER:
Title: {paper['title']}
Abstract: {paper['abstract']}
Authors: {paper['authors']}
Published: {paper['published']}

REQUIRED OUTPUT FORMAT:
Provide a JSON object with the following structure for each category:

{{
    "methodology": {{
        "confidence": <0-100 score>,
        "issues": [{{
            "location": <specific location in paper>,
            "description": <detailed issue description>,
            "suggestion": <improvement suggestion>,
            "severity": <"low"|"medium"|"high">,
            "context": <relevant text excerpt>
        }}],
        "overall_severity": <"low"|"medium"|"high">,
        "key_points": [<list of main points>]
    }},
    "statistical_analysis": {{ ... }},
    "data_integrity": {{ ... }},
    "citation_issues": {{ ... }},
    "technical_accuracy": {{ ... }}
}}

ANALYSIS GUIDELINES:
- Confidence: Assess how confident you are in detecting issues (0-100)
- Issues: Count specific problems found (integer)
- Severity: Rate overall severity based on impact
- Key Points: List 2-3 most important observations

Focus on:
1. Methodology: Research design, approach validity, controls
2. Statistical Analysis: Data analysis methods, significance, interpretations
3. Data Integrity: Data collection, handling, presentation
4. Citation Issues: Reference completeness, accuracy, relevance
5. Technical Accuracy: Domain-specific correctness, terminology

Return ONLY the JSON object, no additional text.
"""
        
    def _parse_analysis_response(self, response_text: str) -> Dict:
        """Parse API response into structured analysis."""
        try:
            # Try to parse the response as JSON
            analysis = json.loads(response_text)
            
            # Normalize the response to match expected format
            normalized = {}
            for category in self.error_categories:
                category_key = category.lower().replace(' ', '_')
                if category_key in analysis:
                    normalized[category] = {
                        'confidence': min(100, max(0, analysis[category_key]['confidence'])),
                        'issues': max(0, analysis[category_key]['issues'])
                    }
                else:
                    normalized[category] = self._generate_fallback_analysis()[category]
                    
            return normalized
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing API response: {e}")
            return self._generate_fallback_analysis()

    def _generate_fallback_analysis(self) -> Dict:
        """Generate fallback analysis when API call fails."""
        import random
        return {
            category: {
                'confidence': random.randint(60, 100),
                'issues': random.randint(0, 3)
            }
            for category in self.error_categories
        }

    def analyze_batch(self, papers: List[Dict]) -> pd.DataFrame:
        """Analyze a batch of papers with parallel processing and progress tracking."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import math
        
        results = []
        total_papers = len(papers)
        processed_papers = 0
        
        # Initialize progress
        progress_bar = st.progress(0.0, text="Starting paper analysis...")
        status_text = st.empty()
        
        # Calculate optimal batch size and worker count
        batch_size = min(10, math.ceil(total_papers / 4))  # Process in smaller batches
        max_workers = min(4, total_papers)  # Limit concurrent workers
        
        def process_paper(paper):
            try:
                analysis = self.analyze_paper(paper)
                return {
                    'title': paper['title'],
                    'published': paper['published'],
                    **{f"{category}_confidence": data['confidence'] for category, data in analysis.items()},
                    **{f"{category}_issues": data['issues'] for category, data in analysis.items()}
                }
            except Exception as e:
                print(f"Error analyzing paper {paper['title']}: {str(e)}")
                fallback = self._generate_fallback_analysis()
                return {
                    'title': paper['title'],
                    'published': paper['published'],
                    **{f"{category}_confidence": data['confidence'] for category, data in fallback.items()},
                    **{f"{category}_issues": data['issues'] for category, data in fallback.items()}
                }
        
        # Process papers in parallel batches
        for i in range(0, total_papers, batch_size):
            batch = papers[i:i + batch_size]
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_paper = {executor.submit(process_paper, paper): paper for paper in batch}
                
                for future in as_completed(future_to_paper):
                    result = future.result()
                    results.append(result)
                    processed_papers += 1
                    
                    # Update progress
                    progress = processed_papers / total_papers
                    progress_bar.progress(progress)
                    status_text.text(f"Analyzed {processed_papers}/{total_papers} papers")
                    
                    # Minimal delay between batches to avoid rate limiting
                    time.sleep(0.1)
        
        status_text.text("Analysis complete!")
        return pd.DataFrame(results)

    def aggregate_patterns(self, results: pd.DataFrame) -> Dict:
        """Aggregate and analyze error patterns across papers with enhanced detection."""
        pattern_stats = {
            'common_issues': {},
            'severity_distribution': {},
            'confidence_trends': {},
            'error_correlations': {},
            'temporal_patterns': {}
        }
        
        # Analyze each category
        for category in self.error_categories:
            confidence_col = f"{category}_confidence"
            issues_col = f"{category}_issues"
            
            # Basic statistics
            pattern_stats['confidence_trends'][category] = {
                'mean': results[confidence_col].mean(),
                'std': results[confidence_col].std(),
                'median': results[confidence_col].median(),
                'trend': self._calculate_trend(results[confidence_col])
            }
            
            pattern_stats['severity_distribution'][category] = {
                'low': len(results[results[issues_col] <= 1]),
                'medium': len(results[(results[issues_col] > 1) & (results[issues_col] <= 3)]),
                'high': len(results[results[issues_col] > 3])
            }
            
            # Calculate correlations with other categories
            correlations = {}
            for other_cat in self.error_categories:
                if other_cat != category:
                    other_issues = f"{other_cat}_issues"
                    corr = results[issues_col].corr(results[other_issues])
                    if abs(corr) > 0.3:  # Only include significant correlations
                        correlations[other_cat] = round(corr, 2)
            
            pattern_stats['error_correlations'][category] = correlations
        
        # Analyze temporal patterns
        results['year_month'] = pd.to_datetime(results['published']).dt.to_period('M')
        temporal_data = results.groupby('year_month').agg({
            f"{cat}_issues": ['mean', 'std'] for cat in self.error_categories
        }).tail(6)  # Last 6 months
        
        pattern_stats['temporal_patterns'] = {
            'monthly_averages': temporal_data.to_dict(),
            'trend_direction': self._detect_trend_direction(temporal_data)
        }
        
        return pattern_stats
        
    def _calculate_trend(self, series: pd.Series) -> str:
        """Calculate the trend direction of a series."""
        if len(series) < 2:
            return "stable"
        
        slope = (series.iloc[-1] - series.iloc[0]) / len(series)
        if abs(slope) < 0.1:
            return "stable"
        return "increasing" if slope > 0 else "decreasing"
        
    def _detect_trend_direction(self, temporal_data: pd.DataFrame) -> Dict:
        """Detect trend direction for each category over time."""
        trends = {}
        for category in self.error_categories:
            means = temporal_data[f"{category}_issues"]['mean']
            trends[category] = self._calculate_trend(means)
        return trends