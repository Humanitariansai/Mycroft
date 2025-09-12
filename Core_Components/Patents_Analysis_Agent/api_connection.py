#!/usr/bin/env python3
"""
USPTO Patent Intelligence Monitoring Tool
Updated to use PatentsView PatentSearch API (2025)
"""

import requests
import json
import time
import csv
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
import urllib.parse
import re
import os

class PatentsViewFetcher:
    """
    Patent data fetcher using the official PatentsView PatentSearch API
    """
    
    def __init__(self, api_key: str = None):
        # PatentsView PatentSearch API endpoints
        self.base_url = "https://search.patentsview.org/api/v1"
        
        # Main endpoints
        self.patent_endpoint = f"{self.base_url}/patent"
        self.assignee_endpoint = f"{self.base_url}/assignee"  # Currently has a bug
        self.inventor_endpoint = f"{self.base_url}/inventor"
        
        # API Configuration
        self.api_key = api_key or os.getenv('PATENTSVIEW_API_KEY')
        if not self.api_key:
            print("⚠️  WARNING: No API key provided!")
            print("   Get a free API key at: https://search.patentsview.org/docs/")
            print("   Set it as: PATENTSVIEW_API_KEY environment variable")
            print("   Or pass it to PatentsViewFetcher(api_key='your_key')")
            print("   The tool will work with limited functionality without a key.")
        
        # Headers for API requests
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'Patent-Intelligence-Tool/2.0'
        }
        
        if self.api_key:
            self.headers['X-Api-Key'] = self.api_key
        
        # Heavy hitting companies with exact assignee name variations
        self.heavy_hitting_companies = {
            "Microsoft": [
                "Microsoft Corporation",
                "Microsoft Corp", 
                "Microsoft Technology Licensing"
            ],
            "Google": [
                "Google LLC", 
                "Google Inc", 
                "Alphabet Inc",
                "DeepMind Technologies",
                "X Development LLC"
            ],
            "Apple": [
                "Apple Inc",
                "Apple Computer"
            ],
            "Amazon": [
                "Amazon.com Inc",
                "Amazon Technologies Inc", 
                "Amazon Web Services"
            ],
            "Meta": [
                "Meta Platforms Inc",
                "Facebook Inc",
                "Facebook Technologies",
                "Oculus VR"
            ],
            "OpenAI": [
                "OpenAI LP",
                "OpenAI Inc", 
                "OpenAI OpCo"
            ],
            "NVIDIA": [
                "NVIDIA Corporation",
                "NVIDIA Corp"
            ],
            "Intel": [
                "Intel Corporation",
                "Intel Corp"
            ],
            "IBM": [
                "International Business Machines", 
                "IBM Corporation"
            ],
            "Tesla": [
                "Tesla Inc",
                "Tesla Motors"
            ],
            "Anthropic": [
                "Anthropic PBC"
            ],
            "Palantir": [
                "Palantir Technologies Inc"
            ],
            "Salesforce": [
                "Salesforce Inc",
                "Salesforce.com Inc"
            ]
        }
        
        # AI/ML keywords for filtering
        self.ai_keywords = [
            "artificial intelligence", "machine learning", "neural network", 
            "deep learning", "natural language processing", "computer vision",
            "reinforcement learning", "generative", "large language model",
            "transformer", "diffusion", "autonomous", "robotics", "chatbot",
            "speech recognition", "image recognition", "predictive analytics",
            "recommendation system", "knowledge graph", "semantic search",
            "pattern recognition", "automated reasoning"
        ]
    
    def search_patents_by_assignee(self, assignee_name: str,
                                 start_date: str = None,
                                 limit: int = 100) -> List[Dict]:
        """
        Search patents by assignee using PatentsView API
        """
        try:
            # Build query - using text search since assignee endpoint has bugs
            query_parts = []
            
            # Assignee name search (using text search as workaround)
            query_parts.append(f'assignee_organization:"{assignee_name}"')
            
            # Date filter if provided
            if start_date:
                date_query = {"patent_date": {"_gte": start_date}}
                query_parts.append(json.dumps(date_query))
            
            # Combine query parts
            if len(query_parts) == 1:
                query = {"_text_phrase": {"assignee_organization": assignee_name}}
            else:
                # Use text search as primary method due to assignee endpoint bug
                query = {
                    "_and": [
                        {"_text_phrase": {"assignee_organization": assignee_name}},
                        {"patent_date": {"_gte": start_date}} if start_date else {}
                    ]
                }
                if not start_date:
                    query = {"_text_phrase": {"assignee_organization": assignee_name}}
            
            # Fields to return
            fields = [
                "patent_id", "patent_number", "patent_title", "patent_abstract",
                "patent_date", "assignees", "inventors", "cpc_at_issue"
            ]
            
            # Request parameters
            params = {
                "q": json.dumps(query),
                "f": json.dumps(fields),
                "o": json.dumps({"per_page": min(limit, 1000)})
            }
            
            print(f"   Searching: {assignee_name}")
            response = requests.get(
                self.patent_endpoint,
                params=params,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                patents = []
                
                if 'patents' in data and data['patents']:
                    for patent in data['patents']:
                        # Extract assignee info
                        assignee_orgs = []
                        if 'assignees' in patent and patent['assignees']:
                            for assignee in patent['assignees']:
                                org = assignee.get('assignee_organization', '')
                                if org:
                                    assignee_orgs.append(org)
                        
                        # Extract inventor names
                        inventor_names = []
                        if 'inventors' in patent and patent['inventors']:
                            for inventor in patent['inventors'][:5]:  # Limit to 5
                                first = inventor.get('inventor_first_name', '')
                                last = inventor.get('inventor_last_name', '')
                                if first and last:
                                    inventor_names.append(f"{first} {last}")
                        
                        # Extract CPC classifications
                        cpc_codes = []
                        if 'cpc_at_issue' in patent and patent['cpc_at_issue']:
                            for cpc in patent['cpc_at_issue'][:3]:  # Top 3
                                section = cpc.get('cpc_section_id', '')
                                class_code = cpc.get('cpc_class', '')
                                if section and class_code:
                                    cpc_codes.append(f"{section}{class_code}")
                        
                        patent_info = {
                            'patent_id': patent.get('patent_id', ''),
                            'patent_number': patent.get('patent_number', ''),
                            'title': patent.get('patent_title', ''),
                            'abstract': patent.get('patent_abstract', '')[:500] if patent.get('patent_abstract') else '',
                            'patent_date': patent.get('patent_date', ''),
                            'assignee_orgs': "; ".join(assignee_orgs),
                            'inventors': "; ".join(inventor_names),
                            'cpc_codes': "; ".join(cpc_codes),
                            'ai_related': self._is_ai_related(patent),
                            'search_assignee': assignee_name,
                            'search_date': datetime.now().isoformat()
                        }
                        patents.append(patent_info)
                
                print(f"   ✓ Found {len(patents)} patents")
                return patents
                
            elif response.status_code == 403:
                print(f"   ❌ API Key required or invalid. Status: {response.status_code}")
                return []
            elif response.status_code == 429:
                print(f"   ⏳ Rate limited. Waiting 60 seconds...")
                time.sleep(60)
                return []
            else:
                print(f"   ⚠️  API Error {response.status_code}: {response.text[:200]}")
                return []
                
        except Exception as e:
            print(f"   ❌ Error searching {assignee_name}: {str(e)}")
            return []
    
    def _is_ai_related(self, patent_data: Dict) -> bool:
        """Check if patent is AI/ML related"""
        text_to_check = ""
        
        # Combine title and abstract
        title = patent_data.get('patent_title', '') or ''
        abstract = patent_data.get('patent_abstract', '') or ''
        text_to_check = f"{title} {abstract}".lower()
        
        # Check for AI keywords
        for keyword in self.ai_keywords:
            if keyword.lower() in text_to_check:
                return True
        
        return False
    
    def monitor_companies(self, companies: Optional[List[str]] = None,
                         days_back: int = 365) -> Dict:
        """
        Monitor patent activity for specified companies
        """
        if companies is None:
            companies = list(self.heavy_hitting_companies.keys())
        
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        all_results = {}
        
        print(f"🔍 Patent Intelligence Monitoring")
        print(f"📅 Looking back: {days_back} days (since {start_date})")
        print(f"🏢 Companies: {', '.join(companies)}")
        print("="*70)
        
        for company in companies:
            print(f"\n🏢 {company}")
            print("-" * 40)
            
            assignee_variations = self.heavy_hitting_companies.get(company, [company])
            all_patents = []
            
            for assignee in assignee_variations:
                patents = self.search_patents_by_assignee(
                    assignee, 
                    start_date=start_date,
                    limit=200
                )
                all_patents.extend(patents)
                
                # Rate limiting - PatentsView allows 45 requests/minute
                time.sleep(1.5)  # ~40 requests/minute to be safe
            
            # Remove duplicates by patent number
            unique_patents = {}
            for patent in all_patents:
                patent_num = patent.get('patent_number', '')
                if patent_num and patent_num not in unique_patents:
                    unique_patents[patent_num] = patent
            
            final_patents = list(unique_patents.values())
            ai_patents = [p for p in final_patents if p.get('ai_related', False)]
            
            all_results[company] = {
                'total_patents': len(final_patents),
                'ai_patents': len(ai_patents),
                'patents': final_patents,
                'last_updated': datetime.now().isoformat()
            }
            
            print(f"   📊 Total Patents: {len(final_patents)}")
            print(f"   🤖 AI-Related: {len(ai_patents)} ({len(ai_patents)/max(len(final_patents),1)*100:.1f}%)")
        
        return all_results
    
    def export_to_csv(self, results: Dict, filename: str = None):
        """Export results to CSV"""
        if filename is None:
            filename = f"patent_intelligence_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        
        all_records = []
        
        for company, data in results.items():
            for patent in data['patents']:
                record = {
                    'company': company,
                    'patent_number': patent.get('patent_number', ''),
                    'title': patent.get('title', ''),
                    'abstract': patent.get('abstract', ''),
                    'patent_date': patent.get('patent_date', ''),
                    'assignee_orgs': patent.get('assignee_orgs', ''),
                    'inventors': patent.get('inventors', ''),
                    'cpc_codes': patent.get('cpc_codes', ''),
                    'ai_related': patent.get('ai_related', False),
                    'search_assignee': patent.get('search_assignee', '')
                }
                all_records.append(record)
        
        df = pd.DataFrame(all_records)
        df.to_csv(filename, index=False)
        
        print(f"\n📁 Results exported to: {filename}")
        return filename
    
    def generate_summary_report(self, results: Dict, days_back: int = 365):
        """Generate intelligence summary"""
        print(f"\n{'='*70}")
        print("🚀 PATENT INTELLIGENCE SUMMARY REPORT")
        print(f"📅 Report Period: Last {days_back} days")
        print(f"⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")
        
        if not results:
            print("❌ No results to analyze")
            return
        
        # Overall statistics
        total_patents = sum(data['total_patents'] for data in results.values())
        total_ai_patents = sum(data['ai_patents'] for data in results.values())
        
        print(f"\n📈 OVERALL INTELLIGENCE:")
        print(f"   🔢 Total Patents Found: {total_patents}")
        print(f"   🤖 AI/ML Patents: {total_ai_patents} ({total_ai_patents/max(total_patents,1)*100:.1f}%)")
        print(f"   🏢 Companies Monitored: {len(results)}")
        
        # Company rankings
        print(f"\n🏆 COMPANY RANKINGS (by AI Patent Activity):")
        sorted_companies = sorted(
            results.items(), 
            key=lambda x: (x[1]['ai_patents'], x[1]['total_patents']), 
            reverse=True
        )
        
        for i, (company, data) in enumerate(sorted_companies, 1):
            ai_ratio = data['ai_patents'] / max(data['total_patents'], 1) * 100
            bar_length = min(20, int(data['ai_patents'] / max(1, max(d['ai_patents'] for d in results.values())) * 20))
            bar = "█" * bar_length + "░" * (20 - bar_length)
            
            print(f"   {i:2d}. {company:<12} │ {bar} │ {data['ai_patents']:3d} AI patents ({ai_ratio:.1f}% of {data['total_patents']:3d} total)")
        
        # Technology insights
        print(f"\n🔬 KEY INSIGHTS:")
        
        # Most active company
        most_active = max(results.items(), key=lambda x: x[1]['ai_patents'])
        print(f"   🥇 Most AI-Active: {most_active[0]} with {most_active[1]['ai_patents']} AI patents")
        
        # Highest AI ratio
        highest_ratio_company = max(
            results.items(), 
            key=lambda x: x[1]['ai_patents'] / max(x[1]['total_patents'], 1)
        )
        ratio = highest_ratio_company[1]['ai_patents'] / max(highest_ratio_company[1]['total_patents'], 1) * 100
        print(f"   🎯 Highest AI Focus: {highest_ratio_company[0]} ({ratio:.1f}% AI-focused)")
        
        print(f"\n💡 Next Steps:")
        print(f"   • Analyze patent abstracts for technology trends")
        print(f"   • Track inventor movements between companies")
        print(f"   • Monitor citation patterns for innovation impact")
        print(f"   • Set up automated weekly monitoring")

def main():
    """Main execution function"""
    print("🚀 Patent Intelligence Monitoring Tool")
    print("Using PatentsView PatentSearch API (2025)")
    print("="*60)
    
    # Initialize with API key
    api_key = input("Enter your PatentsView API key (or press Enter to continue without): ").strip()
    if not api_key:
        api_key = None
    
    fetcher = PatentsViewFetcher(api_key=api_key)
    
    # Select companies to monitor
    print("\n🏢 Select companies to monitor:")
    print("Available options:", ", ".join(fetcher.heavy_hitting_companies.keys()))
    
    company_input = input("Enter company names (comma-separated) or 'all' for top AI companies: ").strip()
    
    if company_input.lower() == 'all' or not company_input:
        companies_to_monitor = ["OpenAI", "NVIDIA", "Microsoft", "Google", "Meta"]
    else:
        companies_to_monitor = [c.strip() for c in company_input.split(',')]
    
    # Select time period
    days_input = input("Enter days to look back (default: 365): ").strip()
    days_back = int(days_input) if days_input.isdigit() else 365
    
    try:
        print(f"\n🔍 Starting monitoring...")
        
        # Monitor companies
        results = fetcher.monitor_companies(
            companies_to_monitor, 
            days_back=days_back
        )
        
        # Generate reports
        fetcher.generate_summary_report(results, days_back)
        csv_filename = fetcher.export_to_csv(results)
        
        print(f"\n✅ Monitoring complete!")
        print(f"📊 View detailed results in: {csv_filename}")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Monitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Error during monitoring: {str(e)}")
        print(f"💡 This might be due to API limits or network issues")

if __name__ == "__main__":
    main()