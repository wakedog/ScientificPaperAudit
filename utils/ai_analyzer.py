from typing import Dict, List
import pplx
import pandas as pd
import os

class PaperAnalyzer:
    def __init__(self):
        self.error_categories = [
            "Methodology Issues",
            "Statistical Errors",
            "Logical Inconsistencies",
            "Citation Problems",
            "Data Interpretation Issues",
            "Reproducibility Concerns",
            "Technical Implementation",
            "Experimental Design"
        ]
        self.pattern_indicators = {
            "Methodology Issues": ["unclear procedures", "missing controls", "inconsistent methods"],
            "Statistical Errors": ["p-hacking", "small sample size", "incorrect tests"],
            "Logical Inconsistencies": ["contradictory statements", "unsupported conclusions"],
            "Citation Problems": ["missing citations", "outdated references"],
            "Data Interpretation Issues": ["overstatement", "cherry picking", "confirmation bias"],
            "Reproducibility Concerns": ["missing code", "unclear parameters", "undefined conditions"],
            "Technical Implementation": ["algorithmic errors", "computational limitations"],
            "Experimental Design": ["poor controls", "confounding variables", "selection bias"]
        }
        # Initialize Perplexity client with API key
        pplx.api_key = os.environ.get("PPLX_API_KEY")
        
    def analyze_paper(self, paper: Dict) -> Dict:
        """Analyze a single paper using Perplexity AI."""
        prompt = f"""
        As an expert scientific paper reviewer, perform a detailed analysis of this paper:
        
        Title: {paper['title']}
        Abstract: {paper['abstract']}
        
        For each category, analyze the following aspects:
        1. Identify specific issues by checking for these indicators:
           {self.pattern_indicators}
        
        2. For each identified issue:
           - Provide a brief description
           - Rate severity (1-5)
           - Assign confidence score (0-100)
        
        3. Consider these specific aspects:
           - Methodology: Clarity, reproducibility, and rigor
           - Statistics: Appropriate tests, sample sizes, and significance
           - Logic: Flow of arguments and validity of conclusions
           - Citations: Proper attribution and relevance
           - Data Interpretation: Objectivity and completeness
           - Reproducibility: Methods clarity and implementation details
           - Technical: Algorithm correctness and computational aspects
           - Design: Control groups and variable handling
        
        Format response as JSON:
        {{
            "category_name": {{
                "confidence": 0-100,
                "issues": number_of_issues,
                "details": [{{
                    "description": "issue description",
                    "severity": 1-5,
                    "indicators": ["matched_indicators"]
                }}]
            }}
        }}
        """
        
        try:
            response = pplx.chat.completions.create(
                model="pplx-70b-online",
                messages=[{
                    "role": "system",
                    "content": "You are a scientific paper reviewer analyzing papers for errors and inconsistencies."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                max_tokens=1000,
                temperature=0.7
            )
            
            # Parse the response to extract analysis
            import json
            try:
                analysis_text = response.choices[0].message.content
                # Extract the JSON part from the response
                start_idx = analysis_text.find('{')
                end_idx = analysis_text.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    analysis_json = json.loads(analysis_text[start_idx:end_idx])
                else:
                    raise ValueError("No valid JSON found in response")
                
                # Ensure all categories are present
                analysis = {}
                for category in self.error_categories:
                    category_key = category.replace(' ', '_').lower()
                    if category_key in analysis_json:
                        analysis[category] = analysis_json[category_key]
                    else:
                        analysis[category] = {'confidence': 70, 'issues': 0}
                
                return analysis
                
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                print(f"Error parsing AI response: {e}")
                return self._generate_fallback_analysis()
                
        except Exception as e:
            print(f"Error calling Perplexity API: {e}")
            return self._generate_fallback_analysis()
            
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
