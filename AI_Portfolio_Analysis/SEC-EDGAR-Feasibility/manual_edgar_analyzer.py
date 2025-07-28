#!/usr/bin/env python3
"""
Integrated SEC Filing Financial Analyzer
Combines EDGAR fetching with financial data parsing for investment analysis.
"""

import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import requests
import time

# Import the classes from previous modules
from edgar_fetcher import EDGARFetcher
from filing_parser import SECFilingParser, FinancialData

class FinancialAnalyzer:
    def __init__(self):
        self.fetcher = EDGARFetcher()
        self.parser = SECFilingParser()
    
    def analyze_company(self, ticker: str, include_forms: List[str] = None) -> Dict:
        """
        Complete analysis of a company's SEC filings
        
        Args:
            ticker: Stock ticker symbol
            include_forms: List of form types to analyze (default: ['10-K', '10-Q'])
        
        Returns:
            Dictionary containing comprehensive financial analysis
        """
        if include_forms is None:
            include_forms = ['10-K', '10-Q']
        
        print(f"\n{'='*60}")
        print(f"COMPREHENSIVE FINANCIAL ANALYSIS: {ticker}")
        print('='*60)
        
        # Get company information
        cik, company_name = self.fetcher.get_company_info(ticker)
        if not cik:
            return None
        
        # Get recent filings
        recent_filings = self.fetcher.get_most_recent_by_form_type(cik, include_forms)
        
        if not recent_filings:
            print("No recent filings found")
            return None
        
        analysis_results = {
            'company_info': {
                'ticker': ticker,
                'company_name': company_name,
                'cik': cik,
                'analysis_date': datetime.now().isoformat()
            },
            'filings_analyzed': {},
            'financial_summary': {},
            'ai_analysis': {},
            'trends': {},
            'ratios': {}
        }
        
        # Analyze each form type
        for form_type, filing_info in recent_filings.items():
            print(f"\nAnalyzing {form_type} from {filing_info['filing_date']}...")
            
            # Fetch filing content
            content = self.fetcher.fetch_document_content(filing_info['document_url'])
            if not content:
                print(f"Failed to fetch {form_type} content")
                continue
            
            # Parse financial data
            financial_data_dict = self.parser.parse_filing(content, form_type)
            
            # Extract AI-specific metrics
            ai_metrics = self.parser.extract_ai_specific_metrics(content)
            
            # Store results
            analysis_results['filings_analyzed'][form_type] = {
                'filing_date': filing_info['filing_date'],
                'url': filing_info['document_url'],
                'financial_data': financial_data_dict,
                'ai_metrics': ai_metrics
            }
            
            print(f"✓ Completed analysis of {form_type}")
            time.sleep(0.2)  # Be respectful to SEC servers
        
        # Generate comprehensive analysis
        analysis_results['financial_summary'] = self._generate_financial_summary(analysis_results)
        analysis_results['trends'] = self._analyze_trends(analysis_results)
        analysis_results['ratios'] = self._calculate_ratios(analysis_results)
        analysis_results['ai_analysis'] = self._consolidate_ai_analysis(analysis_results)
        
        return analysis_results
    
    def _generate_financial_summary(self, analysis_results: Dict) -> Dict:
        """Generate financial summary across all filings"""
        summary = {
            'latest_annual': {},
            'latest_quarterly': {},
            'key_metrics': {}
        }
        
        # Find most recent 10-K and 10-Q
        latest_10k = None
        latest_10q = None
        
        for form_type, filing_data in analysis_results['filings_analyzed'].items():
            if form_type == '10-K' and not latest_10k:
                latest_10k = filing_data
            elif form_type == '10-Q' and not latest_10q:
                latest_10q = filing_data
        
        # Extract key metrics from latest filings
        if latest_10k:
            annual_data = self._extract_primary_financial_data(latest_10k['financial_data'])
            summary['latest_annual'] = {
                'filing_date': latest_10k['filing_date'],
                'data': annual_data
            }
        
        if latest_10q:
            quarterly_data = self._extract_primary_financial_data(latest_10q['financial_data'])
            summary['latest_quarterly'] = {
                'filing_date': latest_10q['filing_date'],
                'data': quarterly_data
            }
        
        return summary
    
    def _extract_primary_financial_data(self, financial_data_dict: Dict) -> Dict:
        """Extract primary financial metrics from parsed data"""
        primary_data = {}
        
        # Get the most complete dataset
        best_data = None
        max_fields = 0
        
        for period, data in financial_data_dict.items():
            non_null_fields = sum(1 for field in data.__dataclass_fields__ 
                                if getattr(data, field) is not None)
            if non_null_fields > max_fields:
                max_fields = non_null_fields
                best_data = data
        
        if best_data:
            # Extract key metrics
            metrics = [
                'revenue', 'gross_profit', 'operating_income', 'net_income',
                'total_assets', 'cash_equivalents', 'total_liabilities',
                'shareholders_equity', 'operating_cash_flow', 'free_cash_flow'
            ]
            
            for metric in metrics:
                value = getattr(best_data, metric)
                if value is not None:
                    primary_data[metric] = value
        
        return primary_data
    
    def _analyze_trends(self, analysis_results: Dict) -> Dict:
        """Analyze trends across multiple periods"""
        trends = {
            'revenue_trend': {},
            'profitability_trend': {},
            'balance_sheet_trend': {}
        }
        
        # This would require historical data analysis
        # For now, return placeholder structure
        trends['analysis_note'] = "Trend analysis requires multiple periods of data"
        
        return trends
    
    def _calculate_ratios(self, analysis_results: Dict) -> Dict:
        """Calculate key financial ratios"""
        ratios = {}
        
        # Get latest annual data
        latest_annual = analysis_results['financial_summary'].get('latest_annual', {}).get('data', {})
        
        if latest_annual:
            # Profitability ratios
            if 'gross_profit' in latest_annual and 'revenue' in latest_annual and latest_annual['revenue']:
                ratios['gross_margin'] = (latest_annual['gross_profit'] / latest_annual['revenue']) * 100
            
            if 'operating_income' in latest_annual and 'revenue' in latest_annual and latest_annual['revenue']:
                ratios['operating_margin'] = (latest_annual['operating_income'] / latest_annual['revenue']) * 100
            
            if 'net_income' in latest_annual and 'revenue' in latest_annual and latest_annual['revenue']:
                ratios['net_margin'] = (latest_annual['net_income'] / latest_annual['revenue']) * 100
            
            # Balance sheet ratios
            if 'total_liabilities' in latest_annual and 'shareholders_equity' in latest_annual and latest_annual['shareholders_equity']:
                ratios['debt_to_equity'] = latest_annual['total_liabilities'] / latest_annual['shareholders_equity']
            
            # Efficiency ratios
            if 'net_income' in latest_annual and 'total_assets' in latest_annual and latest_annual['total_assets']:
                ratios['roa'] = (latest_annual['net_income'] / latest_annual['total_assets']) * 100
            
            if 'net_income' in latest_annual and 'shareholders_equity' in latest_annual and latest_annual['shareholders_equity']:
                ratios['roe'] = (latest_annual['net_income'] / latest_annual['shareholders_equity']) * 100
        
        return ratios
    
    def _consolidate_ai_analysis(self, analysis_results: Dict) -> Dict:
        """Consolidate AI-specific analysis across all filings"""
        consolidated_ai = {
            'total_ai_mentions': 0,
            'ai_revenue_indicators': [],
            'ai_investment_indicators': [],
            'ai_strategic_mentions': []
        }
        
        for form_type, filing_data in analysis_results['filings_analyzed'].items():
            ai_metrics = filing_data.get('ai_metrics', {})
            
            consolidated_ai['total_ai_mentions'] += ai_metrics.get('ai_mentions', 0)
            consolidated_ai['ai_revenue_indicators'].extend(ai_metrics.get('ai_revenue_mentions', []))
            consolidated_ai['ai_investment_indicators'].extend(ai_metrics.get('ai_investment_mentions', []))
        
        return consolidated_ai
    
    def export_to_dataframe(self, analysis_results: Dict) -> pd.DataFrame:
        """Export financial data to pandas DataFrame for further analysis"""
        rows = []
        
        for form_type, filing_data in analysis_results['filings_analyzed'].items():
            for period, financial_data in filing_data['financial_data'].items():
                row = {
                    'ticker': analysis_results['company_info']['ticker'],
                    'company_name': analysis_results['company_info']['company_name'],
                    'form_type': form_type,
                    'filing_date': filing_data['filing_date'],
                    'period': period
                }
                
                # Add all financial metrics
                for field in financial_data.__dataclass_fields__:
                    row[field] = getattr(financial_data, field)
                
                rows.append(row)
        
        return pd.DataFrame(rows)
    
    def export_to_json(self, analysis_results: Dict, filename: str = None) -> str:
        """Export analysis results to JSON file"""
        if filename is None:
            ticker = analysis_results['company_info']['ticker']
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{ticker}_financial_analysis_{timestamp}.json"
        
        # Convert FinancialData objects to dictionaries for JSON serialization
        json_data = self._prepare_for_json(analysis_results)
        
        with open(filename, 'w') as f:
            json.dump(json_data, f, indent=2, default=str)
        
        print(f"Analysis results exported to {filename}")
        return filename
    
    def _prepare_for_json(self, data):
        """Prepare data for JSON serialization"""
        if isinstance(data, dict):
            return {key: self._prepare_for_json(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._prepare_for_json(item) for item in data]
        elif isinstance(data, FinancialData):
            return {field: getattr(data, field) for field in data.__dataclass_fields__}
        else:
            return data
    
    def generate_investment_template_data(self, analysis_results: Dict) -> Dict:
        """Generate data formatted for the AI investment analysis template"""
        template_data = {
            'company_info': analysis_results['company_info'],
            'financial_analysis': {},
            'ai_metrics': analysis_results['ai_analysis']
        }
        
        # Format financial data for template
        latest_annual = analysis_results['financial_summary'].get('latest_annual', {}).get('data', {})
        ratios = analysis_results['ratios']
        
        if latest_annual:
            template_data['financial_analysis'] = {
                'income_statement': {
                    'revenue': latest_annual.get('revenue'),
                    'gross_profit': latest_annual.get('gross_profit'),
                    'operating_income': latest_annual.get('operating_income'),
                    'net_income': latest_annual.get('net_income')
                },
                'balance_sheet': {
                    'total_assets': latest_annual.get('total_assets'),
                    'cash_equivalents': latest_annual.get('cash_equivalents'),
                    'total_liabilities': latest_annual.get('total_liabilities'),
                    'shareholders_equity': latest_annual.get('shareholders_equity')
                },
                'cash_flow': {
                    'operating_cash_flow': latest_annual.get('operating_cash_flow'),
                    'free_cash_flow': latest_annual.get('free_cash_flow')
                },
                'ratios': ratios
            }
        
        return template_data

def main():
    """Example usage of the integrated financial analyzer"""
    analyzer = FinancialAnalyzer()
    
    ticker = input("Enter ticker symbol (e.g., NVDA, MSFT, AAPL): ").strip().upper()
    
    if not ticker:
        print("No ticker provided")
        return
    
    # Analyze the company
    results = analyzer.analyze_company(ticker)
    
    if results:
        print(f"\n{'='*60}")
        print("ANALYSIS COMPLETE")
        print('='*60)
        
        # Display summary
        company_name = results['company_info']['company_name']
        print(f"\nCompany: {company_name} ({ticker})")
        
        # Show financial summary
        if 'latest_annual' in results['financial_summary']:
            annual_data = results['financial_summary']['latest_annual']['data']
            filing_date = results['financial_summary']['latest_annual']['filing_date']
            
            print(f"\nLatest Annual Results (Filed: {filing_date}):")
            if 'revenue' in annual_data:
                print(f"  Revenue: ${annual_data['revenue']:,.0f}")
            if 'operating_income' in annual_data:
                print(f"  Operating Income: ${annual_data['operating_income']:,.0f}")
            if 'net_income' in annual_data:
                print(f"  Net Income: ${annual_data['net_income']:,.0f}")
        
        # Show key ratios
        if results['ratios']:
            print(f"\nKey Financial Ratios:")
            for ratio_name, ratio_value in results['ratios'].items():
                if isinstance(ratio_value, float):
                    print(f"  {ratio_name.replace('_', ' ').title()}: {ratio_value:.2f}{'%' if 'margin' in ratio_name or ratio_name in ['roa', 'roe'] else ''}")
        
        # Show AI analysis
        ai_analysis = results['ai_analysis']
        print(f"\nAI-Related Analysis:")
        print(f"  Total AI mentions across filings: {ai_analysis['total_ai_mentions']}")
        print(f"  AI revenue indicators found: {len(ai_analysis['ai_revenue_indicators'])}")
        print(f"  AI investment indicators found: {len(ai_analysis['ai_investment_indicators'])}")
        
        # Export options
        print(f"\nExport Options:")
        print("1. Export to JSON file")
        print("2. Export to DataFrame (CSV)")
        print("3. Generate investment template data")
        
        choice = input("Choose export option (1-3, or Enter to skip): ").strip()
        
        if choice == "1":
            filename = analyzer.export_to_json(results)
            print(f"Exported to {filename}")
        elif choice == "2":
            df = analyzer.export_to_dataframe(results)
            csv_filename = f"{ticker}_financial_data.csv"
            df.to_csv(csv_filename, index=False)
            print(f"Exported to {csv_filename}")
            print(f"DataFrame shape: {df.shape}")
        elif choice == "3":
            template_data = analyzer.generate_investment_template_data(results)
            template_filename = f"{ticker}_investment_template_data.json"
            with open(template_filename, 'w') as f:
                json.dump(template_data, f, indent=2, default=str)
            print(f"Investment template data exported to {template_filename}")
    
    else:
        print("Analysis failed")

if __name__ == "__main__":
    main()