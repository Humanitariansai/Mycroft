#!/usr/bin/env python3
"""
SEC Filing Parser
Extracts financial data from SEC filings (10-K, 10-Q, 8-K) for investment analysis.
Supports both XBRL and text-based filings.
"""

import re
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Union, Any
import requests
from bs4 import BeautifulSoup
import pandas as pd

@dataclass
class FinancialData:
    """Structure to hold extracted financial data"""
    # Income Statement
    revenue: Optional[float] = None
    cost_of_revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    research_development: Optional[float] = None
    sales_marketing: Optional[float] = None
    general_administrative: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: Optional[float] = None
    earnings_per_share: Optional[float] = None
    earnings_per_share_diluted: Optional[float] = None
    
    # Balance Sheet
    cash_equivalents: Optional[float] = None
    short_term_investments: Optional[float] = None
    accounts_receivable: Optional[float] = None
    inventories: Optional[float] = None
    total_current_assets: Optional[float] = None
    property_plant_equipment: Optional[float] = None
    goodwill: Optional[float] = None
    intangible_assets: Optional[float] = None
    total_assets: Optional[float] = None
    current_liabilities: Optional[float] = None
    long_term_debt: Optional[float] = None
    total_liabilities: Optional[float] = None
    shareholders_equity: Optional[float] = None
    
    # Cash Flow
    operating_cash_flow: Optional[float] = None
    capital_expenditures: Optional[float] = None
    free_cash_flow: Optional[float] = None
    
    # Meta information
    period_end_date: Optional[str] = None
    period_type: Optional[str] = None  # annual, quarterly
    currency: Optional[str] = None
    filing_date: Optional[str] = None
    form_type: Optional[str] = None

class SECFilingParser:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Financial Analysis Tool contact@example.com'
        }
        
        # Common patterns for financial statement items
        self.income_statement_patterns = {
            'revenue': [
                r'(?:Total\s+)?(?:Net\s+)?(?:Sales|Revenue)s?\b(?:\s+and\s+services)?',
                r'(?:Total\s+)?(?:Net\s+)?(?:Operating\s+)?Revenue',
                r'Sales\s+and\s+services',
                r'Net\s+sales',
                r'Total\s+revenues?'
            ],
            'cost_of_revenue': [
                r'Cost\s+of\s+(?:sales|revenue|goods\s+sold)',
                r'Cost\s+of\s+products\s+and\s+services',
                r'Total\s+cost\s+of\s+revenue'
            ],
            'research_development': [
                r'Research\s+and\s+development',
                r'R&D',
                r'Research\s+and\s+engineering'
            ],
            'sales_marketing': [
                r'Sales\s+and\s+marketing',
                r'Sales,\s+general\s+and\s+administrative',
                r'Marketing\s+and\s+sales'
            ],
            'operating_income': [
                r'(?:Total\s+)?Operating\s+income',
                r'Income\s+from\s+operations',
                r'Operating\s+profit'
            ],
            'net_income': [
                r'Net\s+income',
                r'Net\s+earnings',
                r'Net\s+income\s+\(loss\)'
            ]
        }
        
        self.balance_sheet_patterns = {
            'cash_equivalents': [
                r'Cash\s+and\s+cash\s+equivalents',
                r'Cash\s+and\s+equivalents',
                r'Cash\s+and\s+short-term\s+investments'
            ],
            'total_assets': [
                r'Total\s+assets',
                r'Total\s+consolidated\s+assets'
            ],
            'total_liabilities': [
                r'Total\s+liabilities',
                r'Total\s+consolidated\s+liabilities'
            ],
            'shareholders_equity': [
                r'(?:Total\s+)?(?:Shareholders?\'?\s+|Stockholders?\'?\s+)?equity',
                r'Total\s+equity'
            ]
        }
        
        self.cash_flow_patterns = {
            'operating_cash_flow': [
                r'(?:Net\s+)?Cash\s+(?:provided\s+by|from)\s+operating\s+activities',
                r'Operating\s+cash\s+flow',
                r'Cash\s+flows?\s+from\s+operations'
            ],
            'capital_expenditures': [
                r'Capital\s+expenditures?',
                r'Purchases?\s+of\s+property\s+and\s+equipment',
                r'Investments?\s+in\s+property\s+and\s+equipment'
            ]
        }

    def parse_filing(self, content: str, form_type: str = None) -> Dict[str, FinancialData]:
        """
        Main parsing function that handles different filing types
        Returns a dictionary with period as key and FinancialData as value
        """
        try:
            # First, try to determine if this is an XBRL filing
            if self._is_xbrl_filing(content):
                return self._parse_xbrl_filing(content, form_type)
            else:
                return self._parse_text_filing(content, form_type)
        except Exception as e:
            print(f"Error parsing filing: {e}")
            return {}

    def _is_xbrl_filing(self, content: str) -> bool:
        """Check if filing contains XBRL data"""
        return '<xbrl' in content.lower() or 'xmlns:' in content and 'xbrl' in content.lower()

    def _parse_xbrl_filing(self, content: str, form_type: str = None) -> Dict[str, FinancialData]:
        """Parse XBRL-formatted filing"""
        results = {}
        
        try:
            # Parse XML content
            soup = BeautifulSoup(content, 'xml')
            
            # Common XBRL namespaces
            namespaces = {
                'us-gaap': 'http://fasb.org/us-gaap/',
                'dei': 'http://xbrl.sec.gov/dei/',
                'xbrli': 'http://www.xbrl.org/2003/instance'
            }
            
            # Extract context information for different periods
            contexts = self._extract_xbrl_contexts(soup)
            
            for context_id, context_info in contexts.items():
                financial_data = FinancialData()
                financial_data.period_end_date = context_info.get('end_date')
                financial_data.period_type = context_info.get('period_type')
                financial_data.form_type = form_type
                
                # Extract financial metrics using XBRL tags
                financial_data = self._extract_xbrl_metrics(soup, financial_data, context_id)
                
                if context_info.get('end_date'):
                    results[context_info['end_date']] = financial_data
                    
        except Exception as e:
            print(f"Error parsing XBRL filing: {e}")
            
        return results

    def _extract_xbrl_contexts(self, soup) -> Dict[str, Dict]:
        """Extract context information from XBRL filing"""
        contexts = {}
        
        for context in soup.find_all('context'):
            context_id = context.get('id', '')
            
            # Get period information
            period = context.find('period')
            if period:
                instant = period.find('instant')
                start_date = period.find('startdate')
                end_date = period.find('enddate')
                
                context_info = {
                    'context_id': context_id,
                    'period_type': 'instant' if instant else 'duration'
                }
                
                if instant:
                    context_info['end_date'] = instant.text
                elif end_date:
                    context_info['end_date'] = end_date.text
                    if start_date:
                        context_info['start_date'] = start_date.text
                
                contexts[context_id] = context_info
                
        return contexts

    def _extract_xbrl_metrics(self, soup, financial_data: FinancialData, context_id: str) -> FinancialData:
        """Extract financial metrics from XBRL tags"""
        
        # Define XBRL tag mappings
        xbrl_mappings = {
            'revenue': ['Revenues', 'SalesRevenueNet', 'RevenueFromContractWithCustomerExcludingAssessedTax'],
            'cost_of_revenue': ['CostOfRevenue', 'CostOfGoodsAndServicesSold'],
            'research_development': ['ResearchAndDevelopmentExpense'],
            'operating_income': ['OperatingIncomeLoss', 'IncomeLossFromContinuingOperations'],
            'net_income': ['NetIncomeLoss', 'NetIncomeLossAvailableToCommonStockholdersBasic'],
            'total_assets': ['Assets'],
            'total_liabilities': ['Liabilities'],
            'shareholders_equity': ['StockholdersEquity'],
            'operating_cash_flow': ['NetCashProvidedByUsedInOperatingActivities'],
            'capital_expenditures': ['PaymentsToAcquirePropertyPlantAndEquipment']
        }
        
        for field_name, xbrl_tags in xbrl_mappings.items():
            value = self._find_xbrl_value(soup, xbrl_tags, context_id)
            if value is not None:
                setattr(financial_data, field_name, value)
        
        # Calculate derived metrics
        if financial_data.revenue and financial_data.cost_of_revenue:
            financial_data.gross_profit = financial_data.revenue - financial_data.cost_of_revenue
            
        if financial_data.operating_cash_flow and financial_data.capital_expenditures:
            financial_data.free_cash_flow = financial_data.operating_cash_flow - financial_data.capital_expenditures
        
        return financial_data

    def _find_xbrl_value(self, soup, tags: List[str], context_id: str) -> Optional[float]:
        """Find value for XBRL tags with specific context"""
        for tag in tags:
            # Try different namespace prefixes
            for prefix in ['us-gaap:', 'gaap:', '']:
                elements = soup.find_all(f'{prefix}{tag.lower()}')
                for element in elements:
                    if element.get('contextref') == context_id:
                        try:
                            value = float(element.text.replace(',', ''))
                            return value
                        except (ValueError, AttributeError):
                            continue
        return None

    def _parse_text_filing(self, content: str, form_type: str = None) -> Dict[str, FinancialData]:
        """Parse text-based SEC filing"""
        results = {}
        
        try:
            # Clean and prepare content
            cleaned_content = self._clean_filing_content(content)
            
            # Extract financial statements sections
            sections = self._extract_financial_sections(cleaned_content)
            
            # Extract data from each section
            for section_name, section_content in sections.items():
                if 'income' in section_name.lower() or 'operations' in section_name.lower():
                    financial_data = self._extract_income_statement_data(section_content)
                elif 'balance' in section_name.lower() or 'financial position' in section_name.lower():
                    balance_data = self._extract_balance_sheet_data(section_content)
                    if section_name not in results:
                        results[section_name] = FinancialData()
                    results[section_name] = self._merge_financial_data(results.get(section_name, FinancialData()), balance_data)
                elif 'cash flow' in section_name.lower():
                    cash_flow_data = self._extract_cash_flow_data(section_content)
                    if section_name not in results:
                        results[section_name] = FinancialData()
                    results[section_name] = self._merge_financial_data(results.get(section_name, FinancialData()), cash_flow_data)
            
            # If no specific sections found, try to extract from entire content
            if not results:
                financial_data = FinancialData()
                financial_data.form_type = form_type
                
                financial_data = self._extract_income_statement_data(cleaned_content, financial_data)
                financial_data = self._extract_balance_sheet_data(cleaned_content, financial_data)
                financial_data = self._extract_cash_flow_data(cleaned_content, financial_data)
                
                results['main'] = financial_data
                
        except Exception as e:
            print(f"Error parsing text filing: {e}")
            
        return results

    def _clean_filing_content(self, content: str) -> str:
        """Clean and normalize filing content"""
        # Remove HTML tags
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers/footers
        text = re.sub(r'Page\s+\d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\d+\s*$', '', text, flags=re.MULTILINE)
        
        return text

    def _extract_financial_sections(self, content: str) -> Dict[str, str]:
        """Extract different financial statement sections"""
        sections = {}
        
        # Common section headers
        section_patterns = {
            'income_statement': [
                r'CONSOLIDATED\s+STATEMENTS?\s+OF\s+(?:INCOME|OPERATIONS|EARNINGS)',
                r'STATEMENTS?\s+OF\s+(?:INCOME|OPERATIONS|EARNINGS)',
                r'CONSOLIDATED\s+(?:INCOME|OPERATIONS)\s+STATEMENTS?'
            ],
            'balance_sheet': [
                r'CONSOLIDATED\s+BALANCE\s+SHEETS?',
                r'BALANCE\s+SHEETS?',
                r'CONSOLIDATED\s+STATEMENTS?\s+OF\s+FINANCIAL\s+POSITION'
            ],
            'cash_flow': [
                r'CONSOLIDATED\s+STATEMENTS?\s+OF\s+CASH\s+FLOWS?',
                r'STATEMENTS?\s+OF\s+CASH\s+FLOWS?',
                r'CASH\s+FLOW\s+STATEMENTS?'
            ]
        }
        
        for section_name, patterns in section_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    start_pos = match.start()
                    # Find the end of this section (next major section or end of content)
                    end_pos = len(content)
                    
                    # Look for next major financial statement
                    for next_patterns in section_patterns.values():
                        for next_pattern in next_patterns:
                            next_match = re.search(next_pattern, content[start_pos + 100:], re.IGNORECASE)
                            if next_match:
                                end_pos = min(end_pos, start_pos + 100 + next_match.start())
                    
                    sections[section_name] = content[start_pos:end_pos]
                    break
        
        return sections

    def _extract_income_statement_data(self, content: str, financial_data: FinancialData = None) -> FinancialData:
        """Extract income statement data from text"""
        if financial_data is None:
            financial_data = FinancialData()
        
        for field_name, patterns in self.income_statement_patterns.items():
            value = self._extract_financial_value(content, patterns)
            if value is not None:
                setattr(financial_data, field_name, value)
        
        # Calculate gross profit if not found directly
        if financial_data.gross_profit is None and financial_data.revenue and financial_data.cost_of_revenue:
            financial_data.gross_profit = financial_data.revenue - financial_data.cost_of_revenue
        
        return financial_data

    def _extract_balance_sheet_data(self, content: str, financial_data: FinancialData = None) -> FinancialData:
        """Extract balance sheet data from text"""
        if financial_data is None:
            financial_data = FinancialData()
        
        for field_name, patterns in self.balance_sheet_patterns.items():
            value = self._extract_financial_value(content, patterns)
            if value is not None:
                setattr(financial_data, field_name, value)
        
        return financial_data

    def _extract_cash_flow_data(self, content: str, financial_data: FinancialData = None) -> FinancialData:
        """Extract cash flow data from text"""
        if financial_data is None:
            financial_data = FinancialData()
        
        for field_name, patterns in self.cash_flow_patterns.items():
            value = self._extract_financial_value(content, patterns)
            if value is not None:
                setattr(financial_data, field_name, value)
        
        # Calculate free cash flow
        if financial_data.free_cash_flow is None and financial_data.operating_cash_flow and financial_data.capital_expenditures:
            financial_data.free_cash_flow = financial_data.operating_cash_flow - financial_data.capital_expenditures
        
        return financial_data

    def _extract_financial_value(self, content: str, patterns: List[str]) -> Optional[float]:
        """Extract financial value using regex patterns"""
        for pattern in patterns:
            # Create comprehensive regex to capture the financial line item
            full_pattern = rf'{pattern}\s*[:\-\s]*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million|thousand|M|K)?'
            
            matches = re.finditer(full_pattern, content, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                try:
                    value_str = match.group(1).replace(',', '')
                    value = float(value_str)
                    
                    # Check for scale indicators
                    context = match.group(0).lower()
                    if 'million' in context or ' m ' in context:
                        value *= 1_000_000
                    elif 'thousand' in context or ' k ' in context:
                        value *= 1_000
                    elif 'billion' in context or ' b ' in context:
                        value *= 1_000_000_000
                    
                    return value
                except (ValueError, AttributeError):
                    continue
        
        return None

    def _merge_financial_data(self, data1: FinancialData, data2: FinancialData) -> FinancialData:
        """Merge two FinancialData objects"""
        merged = FinancialData()
        
        for field in data1.__dataclass_fields__:
            value1 = getattr(data1, field)
            value2 = getattr(data2, field)
            
            # Use non-None value, preferring data2 if both exist
            if value2 is not None:
                setattr(merged, field, value2)
            elif value1 is not None:
                setattr(merged, field, value1)
        
        return merged

    def extract_ai_specific_metrics(self, content: str) -> Dict[str, Any]:
        """Extract AI-specific metrics and mentions from filings"""
        ai_metrics = {
            'ai_mentions': 0,
            'ai_revenue_mentions': [],
            'ai_investment_mentions': [],
            'ai_risks_mentioned': [],
            'ai_partnerships': [],
            'compute_investments': [],
            'ai_talent_mentions': []
        }
        
        # AI-related keywords
        ai_keywords = [
            'artificial intelligence', 'machine learning', 'deep learning',
            'neural network', 'AI', 'ML', 'generative AI', 'large language model',
            'LLM', 'computer vision', 'natural language processing', 'NLP'
        ]
        
        # Count AI mentions
        for keyword in ai_keywords:
            ai_metrics['ai_mentions'] += len(re.findall(keyword, content, re.IGNORECASE))
        
        # Look for AI revenue mentions
        ai_revenue_patterns = [
            r'AI.*revenue.*\$?([\d,]+(?:\.\d+)?)\s*(?:million|thousand|billion)?',
            r'artificial intelligence.*revenue.*\$?([\d,]+(?:\.\d+)?)\s*(?:million|thousand|billion)?'
        ]
        
        for pattern in ai_revenue_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                ai_metrics['ai_revenue_mentions'].append(match.group(0))
        
        # Look for AI investments
        ai_investment_patterns = [
            r'AI.*(?:investment|spend|expenditure).*\$?([\d,]+(?:\.\d+)?)\s*(?:million|thousand|billion)?',
            r'(?:investment|spend|expenditure).*AI.*\$?([\d,]+(?:\.\d+)?)\s*(?:million|thousand|billion)?'
        ]
        
        for pattern in ai_investment_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                ai_metrics['ai_investment_mentions'].append(match.group(0))
        
        return ai_metrics

    def generate_analysis_report(self, financial_data_dict: Dict[str, FinancialData], 
                               company_name: str, ticker: str) -> str:
        """Generate a formatted analysis report"""
        
        report = f"""
# SEC Filing Analysis Report

**Company:** {company_name}
**Ticker:** {ticker}
**Analysis Date:** {datetime.now().strftime('%Y-%m-%d')}

## Financial Data Summary

"""
        
        for period, data in financial_data_dict.items():
            report += f"\n### Period: {period}\n"
            report += f"**Form Type:** {data.form_type or 'N/A'}\n"
            report += f"**Period End:** {data.period_end_date or 'N/A'}\n\n"
            
            # Income Statement
            if any([data.revenue, data.operating_income, data.net_income]):
                report += "#### Income Statement\n"
                if data.revenue:
                    report += f"- Revenue: ${data.revenue:,.0f}\n"
                if data.gross_profit:
                    report += f"- Gross Profit: ${data.gross_profit:,.0f}\n"
                if data.operating_income:
                    report += f"- Operating Income: ${data.operating_income:,.0f}\n"
                if data.net_income:
                    report += f"- Net Income: ${data.net_income:,.0f}\n"
                report += "\n"
            
            # Balance Sheet
            if any([data.total_assets, data.total_liabilities, data.shareholders_equity]):
                report += "#### Balance Sheet\n"
                if data.cash_equivalents:
                    report += f"- Cash & Equivalents: ${data.cash_equivalents:,.0f}\n"
                if data.total_assets:
                    report += f"- Total Assets: ${data.total_assets:,.0f}\n"
                if data.total_liabilities:
                    report += f"- Total Liabilities: ${data.total_liabilities:,.0f}\n"
                if data.shareholders_equity:
                    report += f"- Shareholders' Equity: ${data.shareholders_equity:,.0f}\n"
                report += "\n"
            
            # Cash Flow
            if any([data.operating_cash_flow, data.free_cash_flow]):
                report += "#### Cash Flow\n"
                if data.operating_cash_flow:
                    report += f"- Operating Cash Flow: ${data.operating_cash_flow:,.0f}\n"
                if data.capital_expenditures:
                    report += f"- Capital Expenditures: ${data.capital_expenditures:,.0f}\n"
                if data.free_cash_flow:
                    report += f"- Free Cash Flow: ${data.free_cash_flow:,.0f}\n"
                report += "\n"
        
        return report

def main():
    """Example usage of the SEC Filing Parser"""
    parser = SECFilingParser()
    
    # Example: Parse a filing
    print("SEC Filing Parser - Example Usage")
    print("=" * 50)
    
    # You would typically get this content from the EDGAR fetcher
    # content = fetcher.fetch_latest_filing(ticker)['content']
    
    # For demo purposes, let's show how to use the parser
    print("To use this parser:")
    print("1. Get filing content using the EDGAR fetcher")
    print("2. Call parser.parse_filing(content, form_type)")
    print("3. Use parser.generate_analysis_report() for formatted output")
    print("4. Use parser.extract_ai_specific_metrics() for AI analysis")
    
    print("\nExample structure:")
    example_data = FinancialData(
        revenue=1000000000,
        operating_income=200000000,
        net_income=150000000,
        total_assets=5000000000,
        cash_equivalents=800000000,
        operating_cash_flow=300000000,
        form_type="10-K",
        period_end_date="2023-12-31"
    )
    
    print(f"Sample Financial Data Structure:")
    for field, value in asdict(example_data).items():
        if value is not None:
            print(f"  {field}: {value}")

if __name__ == "__main__":
    main()