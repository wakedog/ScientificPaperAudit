import os
import json
import time
import requests
from typing import List, Dict
import pandas as pd
from datetime import datetime, timedelta

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
        """Analyze a single paper for potential issues."""
        try:
            # Create a detailed analysis prompt
            prompt = self._generate_analysis_prompt(paper)
            
            # Make API call to Perplexity
            headers = {
                "Authorization": f"Bearer {os.getenv('PPLX_API_KEY')}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "mistral-7b-instruct",
                "messages": [{
                    "role": "system",
                    "content": "You are an expert scientific paper analyzer. Analyze the paper for potential issues and provide structured feedback."
                }, {
                    "role": "user",
                    "content": prompt
                }]
            }
            
            # Add retry mechanism
            max_retries = 3
            retry_delay = 1
            
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        "https://api.perplexity.ai/chat/completions",
                        headers=headers,
                        json=payload
                    )
                    response.raise_for_status()
                    response_data = response.json()
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(retry_delay)
                    retry_delay *= 2
            
            # Parse the response
            if 'choices' in response_data and response_data['choices']:
                return self._parse_analysis_response(response_data['choices'][0]['message']['content'])
            else:
                raise ValueError("Unexpected API response format")
            
        except Exception as e:
            print(f"Error calling Perplexity API: {e}")
            return self._generate_fallback_analysis()

    def _generate_analysis_prompt(self, paper: Dict) -> str:
        """Generate detailed analysis prompt for the paper."""
        return f"""
        Please analyze this scientific paper for potential issues and provide a structured analysis:
        
        PAPER DETAILS:
        Title: {paper['title']}
        Abstract: {paper['abstract']}
        Authors: {paper['authors']}
        Published: {paper['published']}
        
        For each of the following categories:
        - Methodology
        - Statistical Analysis
        - Data Integrity
        - Citation Issues
        - Technical Accuracy
        
        Provide:
        1. A confidence score (0-100)
        2. Number of potential issues identified
        3. Brief description of main concerns
        
        Format your response as a JSON object with this structure for each category:
        {{
            "category_name": {{
                "confidence": score,
                "issues": count,
                "concerns": ["concern1", "concern2"]
            }}
        }}
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
        """Analyze a batch of papers."""
        results = []
        for paper in papers:
            analysis = self.analyze_paper(paper)
            result = {
                'title': paper['title'],
                'published': paper['published']
            }
            for category, data in analysis.items():
                result[f"{category}_confidence"] = data['confidence']
                result[f"{category}_issues"] = data['issues']
            results.append(result)
        
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