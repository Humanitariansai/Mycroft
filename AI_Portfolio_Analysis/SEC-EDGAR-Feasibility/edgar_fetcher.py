#!/usr/bin/env python3
"""
SEC EDGAR Document Fetcher - Enhanced Version
This script fetches the latest SEC filings for a given company ticker symbol.
It retrieves the company's CIK, lists recent filings, and can fetch the most recent
filing for each form type (10-K, 10-Q, 8-K, etc.). The content can be saved to files.
"""

import requests
import json
import time
from datetime import datetime
from collections import defaultdict

class EDGARFetcher:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Darshan Rajopadhye rajopadhye.d@northeastern.edu'
        }
        self.base_url = "https://data.sec.gov/submissions/"
    
    def get_company_info(self, ticker):
        print(f"Looking up company information for {ticker}...")
        
        tickers_url = "https://www.sec.gov/files/company_tickers.json"
        
        try:
            response = requests.get(tickers_url, headers=self.headers)
            response.raise_for_status()
            companies = response.json()
            
            cik = None
            company_name = None
            
            for key, company in companies.items():
                if company['ticker'].upper() == ticker.upper():
                    cik = str(company['cik_str']).zfill(10)
                    company_name = company['title']
                    break
            
            if not cik:
                raise ValueError(f"Ticker {ticker} not found")
            
            print(f"Found: {company_name} (CIK: {cik})")
            return cik, company_name
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching company info: {e}")
            return None, None
    
    def get_filings_list(self, cik, form_types=None):
        """
        Get filings list, optionally filtered by form types
        
        Args:
            cik: Company CIK number
            form_types: List of form types to include (e.g., ['10-K', '10-Q', '8-K'])
                       If None, includes common SEC forms
        """
        print(f"Fetching filings list for CIK {cik}...")
        
        if form_types is None:
            form_types = ['10-K', '10-Q', '8-K', '10-K/A', '10-Q/A', '8-K/A', 'DEF 14A', '13F-HR', 'SC 13G', 'SC 13D']
        
        url = f"{self.base_url}CIK{cik}.json"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            filings = []
            recent_filings = data.get('filings', {}).get('recent', {})
            
            if recent_filings:
                forms = recent_filings.get('form', [])
                filing_dates = recent_filings.get('filingDate', [])
                accession_numbers = recent_filings.get('accessionNumber', [])
                
                for i, form in enumerate(forms):
                    if form in form_types:
                        filings.append({
                            'form_type': form,
                            'filing_date': filing_dates[i],
                            'accession_number': accession_numbers[i],
                            'document_url': self._build_document_url(cik, accession_numbers[i])
                        })
                
                # Sort by filing date (most recent first)
                filings.sort(key=lambda x: x['filing_date'], reverse=True)
            
            return filings
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching filings: {e}")
            return []
    
    def get_most_recent_by_form_type(self, cik, form_types=None):
        """
        Get the most recent filing for each form type
        
        Returns:
            dict: Dictionary with form_type as key and filing info as value
        """
        filings = self.get_filings_list(cik, form_types)
        
        # Group filings by form type and get the most recent for each
        most_recent = {}
        
        for filing in filings:
            form_type = filing['form_type']
            if form_type not in most_recent:
                most_recent[form_type] = filing
            # Since filings are sorted by date (newest first), 
            # the first occurrence is the most recent
        
        return most_recent
    
    def _build_document_url(self, cik, accession_number):
        acc_no_dashes = accession_number.replace('-', '')
        return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_no_dashes}/{accession_number}.txt"
    
    def fetch_document_content(self, document_url):
        print(f"Fetching document from {document_url}")
        
        try:
            time.sleep(0.1)  # Be respectful to SEC servers
            
            response = requests.get(document_url, headers=self.headers)
            response.raise_for_status()
            
            return response.text
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching document: {e}")
            return None
    
    def save_document(self, content, filename):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Document saved to {filename}")
            return True
        except Exception as e:
            print(f"Error saving document: {e}")
            return False
    
    def fetch_latest_filing(self, ticker, form_type='10-K', save_to_file=True):
        """Fetch the latest filing of a specific form type"""
        print(f"\n{'='*50}")
        print(f"Fetching latest {form_type} for {ticker}")
        print('='*50)
        
        cik, company_name = self.get_company_info(ticker)
        if not cik:
            return None
        
        filings = self.get_filings_list(cik)
        if not filings:
            print("No filings found")
            return None
        
        target_filing = None
        for filing in filings:
            if filing['form_type'] == form_type:
                target_filing = filing
                break
        
        if not target_filing:
            print(f"No {form_type} filing found in recent filings")
            print("Available filings:")
            for filing in filings[:5]:
                print(f"  - {filing['form_type']} filed on {filing['filing_date']}")
            return None
        
        print(f"Found {form_type} filed on {target_filing['filing_date']}")
        
        content = self.fetch_document_content(target_filing['document_url'])
        if not content:
            return None
        
        if save_to_file:
            filename = f"{ticker}_{form_type}_{target_filing['filing_date']}.txt"
            self.save_document(content, filename)
        
        return {
            'ticker': ticker,
            'company_name': company_name,
            'form_type': target_filing['form_type'],
            'filing_date': target_filing['filing_date'],
            'content': content,
            'url': target_filing['document_url']
        }
    
    def fetch_all_latest_filings(self, ticker, form_types=None, save_to_file=True):
        """
        Fetch the most recent filing for each form type
        
        Args:
            ticker: Stock ticker symbol
            form_types: List of form types to fetch (defaults to common forms)
            save_to_file: Whether to save documents to files
            
        Returns:
            dict: Dictionary with form_type as key and filing data as value
        """
        print(f"\n{'='*60}")
        print(f"Fetching all latest filings for {ticker}")
        print('='*60)
        
        cik, company_name = self.get_company_info(ticker)
        if not cik:
            return None
        
        most_recent_filings = self.get_most_recent_by_form_type(cik, form_types)
        
        if not most_recent_filings:
            print("No filings found")
            return None
        
        results = {}
        
        print(f"\nFound {len(most_recent_filings)} different form types:")
        for form_type in sorted(most_recent_filings.keys()):
            filing = most_recent_filings[form_type]
            print(f"  - {form_type}: {filing['filing_date']}")
        
        print(f"\nFetching document content...")
        
        for form_type, filing in most_recent_filings.items():
            print(f"\nProcessing {form_type} from {filing['filing_date']}...")
            
            content = self.fetch_document_content(filing['document_url'])
            if content:
                if save_to_file:
                    filename = f"{ticker}_{form_type.replace('/', '_')}_{filing['filing_date']}.txt"
                    self.save_document(content, filename)
                
                results[form_type] = {
                    'ticker': ticker,
                    'company_name': company_name,
                    'form_type': form_type,
                    'filing_date': filing['filing_date'],
                    'content': content,
                    'url': filing['document_url'],
                    'content_length': len(content)
                }
            else:
                print(f"Failed to fetch content for {form_type}")
        
        return results

def main():
    fetcher = EDGARFetcher()
    
    ticker = input("Enter ticker symbol (e.g., NVDA, MSFT, AAPL): ").strip().upper()
    
    if not ticker:
        print("No ticker provided")
        return
    
    print("\nChoose an option:")
    print("1. Fetch specific form type (e.g., 10-K)")
    print("2. Fetch all latest form types")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        form_type = input("Enter form type (e.g., 10-K, 10-Q, 8-K): ").strip().upper()
        if not form_type:
            form_type = "10-K"
        
        result = fetcher.fetch_latest_filing(ticker, form_type=form_type)
        
        if result:
            print(f"\nSUCCESS!")
            print(f"Company: {result['company_name']}")
            print(f"Document: {result['form_type']} filed {result['filing_date']}")
            print(f"Content length: {len(result['content']):,} characters")
            print(f"Document URL: {result['url']}")
            
            print(f"\nFirst 500 characters of document:")
            print("-" * 50)
            print(result['content'][:500])
            print("-" * 50)
        else:
            print("Failed to fetch document")
    
    elif choice == "2":
        # Option to specify custom form types
        custom_forms = input("Enter specific form types (comma-separated, or press Enter for defaults): ").strip()
        form_types = None
        if custom_forms:
            form_types = [f.strip().upper() for f in custom_forms.split(',')]
        
        results = fetcher.fetch_all_latest_filings(ticker, form_types=form_types)
        
        if results:
            print(f"\n{'='*60}")
            print("SUMMARY OF FETCHED DOCUMENTS")
            print('='*60)
            
            total_chars = 0
            for form_type, result in results.items():
                total_chars += result['content_length']
                print(f"{form_type:12} | {result['filing_date']} | {result['content_length']:,} chars")
            
            print(f"\nTotal documents: {len(results)}")
            print(f"Total content: {total_chars:,} characters")
            
            # Show preview of one document
            if results:
                sample_form = list(results.keys())[0]
                sample_result = results[sample_form]
                print(f"\nPreview of {sample_form} (first 300 characters):")
                print("-" * 50)
                print(sample_result['content'][:300])
                print("-" * 50)
        else:
            print("Failed to fetch documents")
    
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()