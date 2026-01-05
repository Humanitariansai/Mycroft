import time
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import re

WATCHLIST = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'TSLA', 'META', 'AMZN', 'EME', 'AEP', 'SMID']
ALERT_CODES = ['P', 'A', 'S']
stocks_sent = []

def parse_html_form4(html_content):
    """Parse Form 4 HTML tables"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # BETTER ticker extraction - look for the specific pattern in Form 4s
        ticker = None
        
        # Strategy 1: Find "Issuer Trading Symbol" label and get the NEXT cell's value
        for row in soup.find_all('tr'):
            cells = row.find_all('td')
            for i, cell in enumerate(cells):
                text = cell.get_text(strip=True).lower()
                if 'issuer trading symbol' in text or 'trading symbol' in text:
                    # Get next cell
                    if i + 1 < len(cells):
                        ticker_text = cells[i + 1].get_text(strip=True)
                        # Extract only uppercase letters, 1-5 chars
                        ticker_match = re.search(r'^([A-Z]{1,5})$', ticker_text)
                        if ticker_match:
                            ticker = ticker_match.group(1)
                            break
            if ticker:
                break
        
        # Strategy 2: Look for class="FormData" cells near "trading symbol"
        if not ticker:
            found_label = False
            for elem in soup.find_all(['td', 'span']):
                text = elem.get_text(strip=True).lower()
                if 'trading symbol' in text:
                    found_label = True
                    continue
                
                if found_label:
                    # This should be the ticker
                    potential = elem.get_text(strip=True)
                    if potential and len(potential) <= 5 and potential.isupper() and potential.isalpha():
                        # Validate it's not a common false positive
                        if potential not in ['CORP', 'INC', 'LLC', 'LTD', 'CO', 'LP', 'TRUST', 'GROUP', 'THE']:
                            ticker = potential
                            break
        
        # Strategy 3: Look in first table for ticker pattern
        if not ticker:
            first_table = soup.find('table')
            if first_table:
                for cell in first_table.find_all('td', class_='FormData'):
                    text = cell.get_text(strip=True)
                    # Ticker is usually 1-5 uppercase letters, NOT ending in common suffixes
                    if text and 1 <= len(text) <= 5 and text.isupper() and text.isalpha():
                        if text not in ['CORP', 'INC', 'LLC', 'LTD', 'CO', 'LP', 'GROUP', 'THE', 'TRUST', 'FORM', 'TABLE']:
                            ticker = text
                            break
        
        if not ticker:
            print("    ❌ No ticker found")
            # Debug: show first table
            first_table = soup.find('table')
            if first_table:
                print("    DEBUG: First table content:")
                rows = first_table.find_all('tr')[:5]
                for row in rows:
                    cells = row.find_all('td')
                    print(f"      {[c.get_text(strip=True) for c in cells]}")
            return []
        
        print(f"    ✅ Ticker: {ticker}")
        
        is_officer = 'officer' in soup.get_text().lower()
        results = []
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                cell_texts = [c.get_text(strip=True) for c in cells]
                
                if len(cell_texts) < 5:
                    continue
                
                # Find transaction code
                code = None
                for text in cell_texts:
                    if text in ['P', 'S', 'A', 'D', 'M', 'G', 'F']:
                        code = text
                        break
                
                if not code:
                    continue
                
                # Extract numbers
                numbers = []
                for text in cell_texts:
                    clean = text.replace(',', '').replace('$', '')
                    clean = re.sub(r'\([0-9]+\)', '', clean).strip()
                    
                    if clean:
                        try:
                            num = float(clean)
                            if num >= 0:
                                numbers.append(num)
                        except:
                            pass
                
                direct = 'D' in cell_texts
                
                if len(numbers) >= 1:
                    # Get shares (usually largest whole number)
                    whole_nums = [n for n in numbers if n == int(n) and n > 0]
                    decimal_nums = [n for n in numbers if n != int(n) and n > 0]
                    
                    if whole_nums:
                        shares = max(whole_nums)
                    else:
                        shares = max(numbers)
                    
                    # Get price (usually a decimal, smaller than shares)
                    price = None
                    if decimal_nums:
                        # Take the decimal that's NOT shares
                        for num in decimal_nums:
                            if num != shares and num < shares:
                                price = num
                                break
                        if not price:
                            price = decimal_nums[0]
                    
                    if not price or price == 0:
                        price = 0.01
                    
                    # Sanity check: price shouldn't be way larger than shares
                    if price > shares and shares > 100:
                        # Probably swapped
                        price, shares = shares, price
                    
                    if shares > 0 and shares < 1000000000:  # Reasonable share count
                        results.append({
                            'ticker': ticker,
                            'is_officer': is_officer,
                            'code': code,
                            'shares': shares,
                            'price': price,
                            'value': shares * price,
                            'direct': direct
                        })
        
        if results:
            print(f"    📊 Extracted {len(results)} transactions")
        return results
        
    except Exception as e:
        print(f"    💥 Parse error: {e}")
        return []

def scrape_form4(filing_url):
    """Fetch and parse Form 4"""
    headers = {"User-Agent": "InsiderTracker/1.0 your.email@example.com"}
    
    try:
        res = requests.get(filing_url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        form4_link = None
        for row in soup.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 4 and cells[3].text.strip() == '4':
                link_tag = cells[2].find('a')
                if link_tag:
                    href = link_tag['href']
                    if 'form4' in href.lower() or href.endswith('.xml'):
                        form4_link = 'https://www.sec.gov' + href
                        break
        
        if not form4_link:
            return []
        
        time.sleep(0.4)
        form4_res = requests.get(form4_link, headers=headers, timeout=15)
        
        return parse_html_form4(form4_res.text)
    
    except Exception as e:
        print(f"    💥 Error: {str(e)[:100]}")
        return []

def monitor_feed():
    url = 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&company=&dateb=&owner=include&start=0&count=100&output=atom'
    
    headers = {"User-Agent": "InsiderTracker/1.0 your.email@example.com"}
    
    print(f"🔍 Fetching SEC Form 4 filings... {datetime.now().strftime('%H:%M:%S')}\n")
    
    response = requests.get(url, headers=headers, timeout=10)
    
    import xml.etree.ElementTree as ET
    root = ET.fromstring(response.content)
    
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    entries = root.findall('atom:entry', ns)
    print(f"Found {len(entries)} filings\n")
    
    processed = 0
    for i, entry in enumerate(entries[:20]):  # Check first 20
        try:
            title = entry.find('atom:title', ns).text
            
            if not title.startswith('4 -'):
                continue
                
            filing_url = entry.find('atom:link', ns).get('href')
            
            if not filing_url.startswith('http'):
                filing_url = 'https://www.sec.gov' + filing_url
            
            if filing_url in stocks_sent:
                continue
            
            processed += 1
            print(f"[{processed}] {title[:65]}")
            
            transactions = scrape_form4(filing_url)
            
            if transactions:
                for txn in transactions:
                    print(f"    📊 {txn['ticker']}: {txn['code']} | {txn['shares']:,.0f} @ ${txn['price']:.2f} = ${txn['value']:,.0f}")
                    
                    if txn['ticker'] in WATCHLIST and txn['code'] in ALERT_CODES:
                        print(f"\n    {'='*60}")
                        print(f"    🚨 WATCHLIST ALERT: {txn['ticker']} 🚨")
                        print(f"    {'='*60}")
                        print(f"    Type: {txn['code']} ({'Purchase' if txn['code']=='P' else 'Award' if txn['code']=='A' else 'Sale'})")
                        print(f"    Shares: {txn['shares']:,.0f}")
                        print(f"    Price: ${txn['price']:.2f}")
                        print(f"    Value: ${txn['value']:,.0f}")
                        print(f"    Officer: {txn['is_officer']} | Direct: {txn['direct']}")
                        print(f"    Link: {filing_url}")
                        print(f"    {'='*60}\n")
            
            stocks_sent.append(filing_url)
            print()
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"    Error: {e}\n")
    
    print(f"{'='*70}")
    print(f"Processed {processed} filings")

if __name__ == "__main__":
    monitor_feed()