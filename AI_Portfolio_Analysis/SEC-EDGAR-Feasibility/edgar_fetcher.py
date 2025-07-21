#!/usr/bin/env python3
"""
SEC EDGAR Document Fetcher
This script fetches the latest SEC filings for a given company ticker symbol.
It retrieves the company's CIK, lists recent filings, and fetches the content of the latest
10-K filing. The content can be saved to a file."""

import requests
import json
import time
from datetime import datetime

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
    
    def get_filings_list(self, cik):
        print(f"Fetching filings list for CIK {cik}...")
        
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
                    if form in ['10-K', '10-Q', '8-K']:
                        filings.append({
                            'form_type': form,
                            'filing_date': filing_dates[i],
                            'accession_number': accession_numbers[i],
                            'document_url': self._build_document_url(cik, accession_numbers[i])
                        })
                
                filings.sort(key=lambda x: x['filing_date'], reverse=True)
            
            return filings[:10]
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching filings: {e}")
            return []
    
    def _build_document_url(self, cik, accession_number):
        acc_no_dashes = accession_number.replace('-', '')
        return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_no_dashes}/{accession_number}.txt"
    
    def fetch_document_content(self, document_url):
        print(f"Fetching document from {document_url}")
        
        try:
            time.sleep(0.1)
            
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

def main():
    fetcher = EDGARFetcher()
    
    ticker = input("Enter ticker symbol (e.g., NVDA, MSFT, AAPL): ").strip().upper()
    
    if not ticker:
        print("No ticker provided")
        return
    
    result = fetcher.fetch_latest_filing(ticker, form_type='10-K')
    
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

if __name__ == "__main__":
    main()