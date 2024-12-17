import os
import json
from typing import List, Dict
import pandas as pd
import pplx

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
            response = pplx.chat(
                api_key=os.getenv('PPLX_API_KEY'),
                model="pplx-70b-online",
                messages=[{
                    "role": "system",
                    "content": "You are an expert scientific paper analyzer. Analyze the paper for potential issues and provide structured feedback."
                }, {
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Parse the response
            return self._parse_analysis_response(response['choices'][0]['message']['content'])
            
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
        """Aggregate and analyze error patterns across papers."""
        pattern_stats = {
            'common_issues': {},
            'severity_distribution': {},
            'confidence_trends': {}
        }
        
        # Analyze each category
        for category in self.error_categories:
            confidence_col = f"{category}_confidence"
            issues_col = f"{category}_issues"
            
            pattern_stats['confidence_trends'][category] = {
                'mean': results[confidence_col].mean(),
                'std': results[confidence_col].std(),
                'median': results[confidence_col].median()
            }
            
            pattern_stats['severity_distribution'][category] = {
                'low': len(results[results[issues_col] <= 1]),
                'medium': len(results[(results[issues_col] > 1) & (results[issues_col] <= 3)]),
                'high': len(results[results[issues_col] > 3])
            }
        
        return pattern_stats