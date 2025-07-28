#!/usr/bin/env python3
"""
Simplified SEC Financial Analyzer using sec-edgar-api
Extracts financial data from SEC filings for investment analysis.

Installation: pip install sec-edgar-api pandas requests
"""

import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
from sec_edgar_api import EdgarClient

class SECFinancialAnalyzer:
    def __init__(self, user_agent: str = "Financial Analyzer your.email@example.com"):
        """
        Initialize the SEC Financial Analyzer
        
        Args:
            user_agent: Required by SEC - should include your name and email
        """
        self.edgar = EdgarClient(user_agent=user_agent)
        self.ticker_to_cik_cache = {}
    
    def get_cik_from_ticker(self, ticker: str) -> Optional[str]:
        """
        Convert ticker symbol to CIK using SEC's company tickers JSON
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            CIK string or None if not found
        """
        if ticker in self.ticker_to_cik_cache:
            return self.ticker_to_cik_cache[ticker]
        
        try:
            import requests
            print(f"Looking up CIK for ticker {ticker}...")
            
            tickers_url = "https://www.sec.gov/files/company_tickers.json"
            headers = {'User-Agent': 'Financial Analyzer your.email@example.com'}
            
            response = requests.get(tickers_url, headers=headers)
            response.raise_for_status()
            
            companies = response.json()
            
            for key, company in companies.items():
                if company['ticker'].upper() == ticker.upper():
                    cik = str(company['cik_str']).zfill(10)
                    self.ticker_to_cik_cache[ticker] = cik
                    print(f"✓ Found CIK {cik} for {ticker} ({company['title']})")
                    return cik
            
            print(f"✗ Ticker {ticker} not found in SEC database")
            return None
            
        except Exception as e:
            print(f"Error looking up CIK for {ticker}: {e}")
            return None
    
    def get_company_facts(self, ticker: str) -> Dict[str, Any]:
        """
        Get comprehensive company facts from SEC
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'NVDA')
            
        Returns:
            Dictionary containing all company facts
        """
        try:
            cik = self.get_cik_from_ticker(ticker)
            if not cik:
                return {}
            
            print(f"Fetching company facts for {ticker} (CIK: {cik})...")
            company_facts = self.edgar.get_company_facts(cik)
            print(f"✓ Successfully retrieved facts for {ticker}")
            return company_facts
        except Exception as e:
            print(f"Error fetching company facts for {ticker}: {e}")
            return {}
    
    def extract_financial_metrics(self, company_facts: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """
        Extract key financial metrics from company facts
        
        Args:
            company_facts: Raw company facts from SEC
            
        Returns:
            Dictionary with financial metrics organized by type
        """
        if not company_facts or 'facts' not in company_facts:
            return {}
        
        us_gaap = company_facts.get('facts', {}).get('us-gaap', {})
        financial_data = {}
        
        metrics_mapping = {
            'revenue': ['Revenues', 'SalesRevenueNet', 'RevenueFromContractWithCustomerExcludingAssessedTax'],
            'cost_of_revenue': ['CostOfRevenue', 'CostOfGoodsAndServicesSold'],
            'gross_profit': ['GrossProfit'],
            'research_development': ['ResearchAndDevelopmentExpense'],
            'operating_income': ['OperatingIncomeLoss', 'IncomeLossFromContinuingOperations'],
            'net_income': ['NetIncomeLoss', 'NetIncomeLossAvailableToCommonStockholdersBasic'],
            'earnings_per_share': ['EarningsPerShareBasic', 'EarningsPerShareDiluted'],
            'cash_and_equivalents': ['CashAndCashEquivalentsAtCarryingValue', 'Cash'],
            'short_term_investments': ['ShortTermInvestments', 'MarketableSecuritiesCurrent'],
            'accounts_receivable': ['AccountsReceivableNetCurrent'],
            'total_current_assets': ['AssetsCurrent'],
            'total_assets': ['Assets'],
            'goodwill': ['Goodwill'],
            'intangible_assets': ['IntangibleAssetsNetExcludingGoodwill'],
            'current_liabilities': ['LiabilitiesCurrent'],
            'long_term_debt': ['LongTermDebt', 'LongTermDebtNoncurrent'],
            'total_liabilities': ['Liabilities'],
            'shareholders_equity': ['StockholdersEquity'],
            'operating_cash_flow': ['NetCashProvidedByUsedInOperatingActivities'],
            'capital_expenditures': ['PaymentsToAcquirePropertyPlantAndEquipment'],
            'free_cash_flow': ['FreeCashFlow']
        }
        
        for metric_name, possible_keys in metrics_mapping.items():
            metric_data = self._extract_metric_data(us_gaap, possible_keys)
            if metric_data:
                financial_data[metric_name] = metric_data
        
        return financial_data
    
    def _extract_metric_data(self, us_gaap: Dict, possible_keys: List[str]) -> List[Dict]:
        """
        Extract data for a specific metric from US-GAAP facts
        
        Args:
            us_gaap: US-GAAP section of company facts
            possible_keys: List of possible XBRL tags for this metric
            
        Returns:
            List of data points for this metric
        """
        for key in possible_keys:
            if key in us_gaap:
                usd_data = us_gaap[key].get('units', {}).get('USD', [])
                if usd_data:
                    cleaned_data = []
                    for item in usd_data:
                        if 'val' not in item:
                            continue
                        
                        data_point = {
                            'value': item['val'],
                            'period_end': item.get('end'),
                            'fiscal_year': item.get('fy'),
                            'fiscal_period': item.get('fp'),
                            'form': item.get('form'),
                            'filed_date': item.get('filed')
                        }
                        cleaned_data.append(data_point)
                    
                    cleaned_data.sort(key=lambda x: x.get('period_end', ''), reverse=True)
                    return cleaned_data[:10]
        
        return []
    
    def get_latest_annual_data(self, financial_data: Dict[str, List[Dict]]) -> Dict[str, float]:
        """
        Get the most recent annual data for each metric
        
        Args:
            financial_data: Financial data organized by metric
            
        Returns:
            Dictionary with latest annual values
        """
        latest_annual = {}
        
        for metric_name, metric_data in financial_data.items():
            for data_point in metric_data:
                if data_point.get('form') == '10-K' and data_point.get('value') is not None:
                    latest_annual[metric_name] = {
                        'value': data_point['value'],
                        'period_end': data_point.get('period_end'),
                        'fiscal_year': data_point.get('fiscal_year')
                    }
                    break
        
        return latest_annual
    
    def get_latest_quarterly_data(self, financial_data: Dict[str, List[Dict]]) -> Dict[str, float]:
        """
        Get the most recent quarterly data for each metric
        
        Args:
            financial_data: Financial data organized by metric
            
        Returns:
            Dictionary with latest quarterly values
        """
        latest_quarterly = {}
        
        for metric_name, metric_data in financial_data.items():
            for data_point in metric_data:
                if data_point.get('form') == '10-Q' and data_point.get('value') is not None:
                    latest_quarterly[metric_name] = {
                        'value': data_point['value'],
                        'period_end': data_point.get('period_end'),
                        'fiscal_year': data_point.get('fiscal_year'),
                        'fiscal_period': data_point.get('fiscal_period')
                    }
                    break
        
        return latest_quarterly
    
    def calculate_financial_ratios(self, annual_data: Dict[str, Dict]) -> Dict[str, float]:
        """
        Calculate key financial ratios from annual data
        
        Args:
            annual_data: Latest annual financial data
            
        Returns:
            Dictionary of calculated ratios
        """
        ratios = {}
        
        def get_value(metric_name):
            return annual_data.get(metric_name, {}).get('value', 0) or 0
        
        revenue = get_value('revenue')
        gross_profit = get_value('gross_profit')
        operating_income = get_value('operating_income')
        net_income = get_value('net_income')
        total_assets = get_value('total_assets')
        shareholders_equity = get_value('shareholders_equity')
        total_liabilities = get_value('total_liabilities')
        
        if revenue > 0:
            if gross_profit > 0:
                ratios['gross_margin'] = (gross_profit / revenue) * 100
            if operating_income != 0:
                ratios['operating_margin'] = (operating_income / revenue) * 100
            if net_income != 0:
                ratios['net_margin'] = (net_income / revenue) * 100
        
        if total_assets > 0 and net_income != 0:
            ratios['return_on_assets'] = (net_income / total_assets) * 100
        
        if shareholders_equity > 0 and net_income != 0:
            ratios['return_on_equity'] = (net_income / shareholders_equity) * 100
        
        if shareholders_equity > 0:
            ratios['debt_to_equity'] = total_liabilities / shareholders_equity
        
        return ratios
    
    def analyze_ai_mentions(self, company_facts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze AI-related content in company filings
        This is a basic implementation - would need actual filing text for thorough analysis
        
        Args:
            company_facts: Company facts from SEC
            
        Returns:
            Dictionary with AI analysis results
        """
        ai_analysis = {
            'note': 'AI analysis requires access to full filing text, not just structured data',
            'structured_data_available': bool(company_facts.get('facts')),
            'recommendation': 'Use filing text analysis for comprehensive AI metrics'
        }
        
        return ai_analysis
    
    def create_comprehensive_report(self, ticker: str) -> Dict[str, Any]:
        """
        Create a comprehensive financial analysis report
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Complete analysis report
        """
        print(f"\n{'='*60}")
        print(f"COMPREHENSIVE FINANCIAL ANALYSIS: {ticker}")
        print('='*60)
        
        company_facts = self.get_company_facts(ticker)
        if not company_facts:
            return {'error': f'Could not retrieve data for {ticker}'}
        
        financial_data = self.extract_financial_metrics(company_facts)
        if not financial_data:
            return {'error': f'Could not extract financial data for {ticker}'}
        
        latest_annual = self.get_latest_annual_data(financial_data)
        latest_quarterly = self.get_latest_quarterly_data(financial_data)
        
        financial_ratios = self.calculate_financial_ratios(latest_annual)
        
        ai_analysis = self.analyze_ai_mentions(company_facts)
        
        company_info = {
            'ticker': ticker,
            'company_name': company_facts.get('entityName', 'N/A'),
            'cik': company_facts.get('cik', 'N/A'),
            'sic': company_facts.get('sic', 'N/A'),
            'sic_description': company_facts.get('sicDescription', 'N/A'),
            'analysis_date': datetime.now().isoformat()
        }
        
        report = {
            'company_info': company_info,
            'latest_annual_data': latest_annual,
            'latest_quarterly_data': latest_quarterly,
            'financial_ratios': financial_ratios,
            'historical_data': financial_data,
            'ai_analysis': ai_analysis
        }
        
        return report
    
    def export_to_dataframe(self, financial_data: Dict[str, List[Dict]], ticker: str) -> pd.DataFrame:
        """
        Export financial data to pandas DataFrame
        
        Args:
            financial_data: Financial data by metric
            ticker: Stock ticker
            
        Returns:
            DataFrame with all financial data
        """
        rows = []
        
        for metric_name, metric_data in financial_data.items():
            for data_point in metric_data:
                row = {
                    'ticker': ticker,
                    'metric': metric_name,
                    'value': data_point.get('value'),
                    'period_end': data_point.get('period_end'),
                    'fiscal_year': data_point.get('fiscal_year'),
                    'fiscal_period': data_point.get('fiscal_period'),
                    'form': data_point.get('form'),
                    'filed_date': data_point.get('filed_date')
                }
                rows.append(row)
        
        return pd.DataFrame(rows)
    
    def print_summary(self, report: Dict[str, Any]):
        """Print a formatted summary of the analysis"""
        
        company_info = report.get('company_info', {})
        latest_annual = report.get('latest_annual_data', {})
        ratios = report.get('financial_ratios', {})
        
        print(f"\n{'='*60}")
        print("FINANCIAL ANALYSIS SUMMARY")
        print('='*60)
        
        print(f"\nCompany: {company_info.get('company_name', 'N/A')} ({company_info.get('ticker', 'N/A')})")
        print(f"Industry: {company_info.get('sic_description', 'N/A')}")
        print(f"CIK: {company_info.get('cik', 'N/A')}")
        
        if latest_annual:
            print(f"\nLatest Annual Financial Data:")
            
            if 'revenue' in latest_annual:
                revenue_data = latest_annual['revenue']
                print(f"  Revenue: ${revenue_data['value']:,.0f} (FY {revenue_data.get('fiscal_year', 'N/A')})")
            
            if 'net_income' in latest_annual:
                ni_data = latest_annual['net_income']
                print(f"  Net Income: ${ni_data['value']:,.0f}")
            
            if 'total_assets' in latest_annual:
                assets_data = latest_annual['total_assets']
                print(f"  Total Assets: ${assets_data['value']:,.0f}")
            
            if 'cash_and_equivalents' in latest_annual:
                cash_data = latest_annual['cash_and_equivalents']
                print(f"  Cash & Equivalents: ${cash_data['value']:,.0f}")
        
        if ratios:
            print(f"\nKey Financial Ratios:")
            for ratio_name, ratio_value in ratios.items():
                if isinstance(ratio_value, (int, float)):
                    if 'margin' in ratio_name or 'return' in ratio_name:
                        print(f"  {ratio_name.replace('_', ' ').title()}: {ratio_value:.2f}%")
                    else:
                        print(f"  {ratio_name.replace('_', ' ').title()}: {ratio_value:.2f}")

def main():
    """Example usage of the SEC Financial Analyzer"""
    
    analyzer = SECFinancialAnalyzer(user_agent="Darshan Rajopadhye rajopadhye.d@northeastern.edu")
    
    ticker = input("Enter ticker symbol (e.g., AAPL, NVDA, MSFT): ").strip().upper()
    
    if not ticker:
        print("No ticker provided")
        return
    
    try:
        report = analyzer.create_comprehensive_report(ticker)
        
        if 'error' in report:
            print(f"Error: {report['error']}")
            return
        
        analyzer.print_summary(report)
        
        print(f"\n{'='*60}")
        print("EXPORT OPTIONS")
        print('='*60)
        print("1. Save full report to JSON")
        print("2. Export to CSV (DataFrame)")
        print("3. Both")
        
        choice = input("Choose export option (1-3, or Enter to skip): ").strip()
        
        if choice in ['1', '3']:
            json_filename = f"{ticker}_financial_report_{datetime.now().strftime('%Y%m%d')}.json"
            with open(json_filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"✓ Full report saved to {json_filename}")
        
        if choice in ['2', '3']:
            df = analyzer.export_to_dataframe(report['historical_data'], ticker)
            csv_filename = f"{ticker}_financial_data_{datetime.now().strftime('%Y%m%d')}.csv"
            df.to_csv(csv_filename, index=False)
            print(f"✓ Historical data exported to {csv_filename}")
            print(f"  DataFrame shape: {df.shape}")
        
        print(f"\nAnalysis complete for {ticker}!")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()