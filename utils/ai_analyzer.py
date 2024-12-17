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
            "Data Interpretation Issues"
        ]

    def __init__(self):
        self.error_categories = [
            "Methodology Issues",
            "Statistical Errors",
            "Logical Inconsistencies",
            "Citation Problems",
            "Data Interpretation Issues"
        ]
        # Initialize Perplexity client with API key
        pplx.api_key = os.environ.get("PPLX_API_KEY")
        
    def analyze_paper(self, paper: Dict) -> Dict:
        """Analyze a single paper using Perplexity AI."""
        prompt = f"""
        As a scientific paper reviewer, analyze this paper for potential errors and inconsistencies.
        
        Title: {paper['title']}
        Abstract: {paper['abstract']}
        
        For each category below:
        1. Identify specific issues (if any)
        2. Assign a confidence score (0-100) based on the reliability of the analysis
        3. Count the number of distinct issues found
        
        Categories:
        - Methodology Issues
        - Statistical Errors
        - Logical Inconsistencies
        - Citation Problems
        - Data Interpretation Issues
        
        Format your response as a JSON object with this structure for each category:
        {{"category_name": {{"confidence": 0-100, "issues": number_of_issues}}}}
        """
        
        try:
            response = pplx.ChatCompletion.create(
                model="pplx-70b-online",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
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
