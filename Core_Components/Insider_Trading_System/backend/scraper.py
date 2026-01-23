from bs4 import BeautifulSoup
import datetime
import logging
import time
import json
import sys
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException


# -----------------------------------------------------------------------------
# Logging: stderr ONLY (stdout is reserved for JSON output for n8n)
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('capitol_trades.log'),
        logging.StreamHandler(sys.stderr)
    ]
)


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
class Config:
    RECENT_DAYS = 45
    MIN_TRADE_SIZE = 5000
    USE_MAX_RANGE = True

    URL = "https://www.capitoltrades.com/trades"
    TRADES_CHECKED_FILE = "trades_checked.txt"
    DATE_LOG_FILE = "date_log.txt"

    PAGE_LOAD_TIMEOUT = 30
    ELEMENT_WAIT_TIMEOUT = 10
    PAGES_TO_SCRAPE = 7


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
class TradeExtractor:

    @staticmethod
    def parse_trade_size(size_str: Optional[str]) -> Optional[List[int]]:
        if not size_str or size_str == "N/A":
            return None

        try:
            size_str = size_str.strip()

            if '<' in size_str:
                return [0, 1000]

            parts = size_str.replace('–', '-').replace('—', '-').split('-')
            if len(parts) != 2:
                return None

            multipliers = {'K': 1_000, 'M': 1_000_000, 'B': 1_000_000_000}
            result = []

            for part in parts:
                numeric = ''.join(c for c in part if c.isdigit() or c == '.')
                suffix = ''.join(c for c in part if c.isalpha())

                if not numeric or suffix not in multipliers:
                    return None

                result.append(int(float(numeric) * multipliers[suffix]))

            return result

        except Exception:
            return None

    @staticmethod
    def parse_filed_after(filed_str: Optional[str]) -> Optional[int]:
        if not filed_str:
            return None
        digits = ''.join(c for c in filed_str if c.isdigit())
        return int(digits) if digits else None


class TradeChecker:

    def __init__(self, filepath: str):
        self.filepath = filepath
        open(self.filepath, 'a').close()

    def load_checked_ids(self) -> set:
        try:
            with open(self.filepath, 'r') as f:
                return {line.strip() for line in f if line.strip()}
        except Exception:
            return set()

    def mark_as_checked(self, trade_id: str):
        with open(self.filepath, 'a') as f:
            f.write(f"{trade_id}\n")


# -----------------------------------------------------------------------------
# Scraper
# -----------------------------------------------------------------------------
class CapitolTradesScraperSelenium:

    def __init__(self, config: Config):
        self.config = config
        self.extractor = TradeExtractor()
        self.checker = TradeChecker(config.TRADES_CHECKED_FILE)
        self.driver = None
        self.current_page = 1

    def setup_driver(self) -> bool:
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')

            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(self.config.PAGE_LOAD_TIMEOUT)
            return True

        except Exception as e:
            logging.error(f"WebDriver setup failed: {e}")
            return False

    def fetch_page(self, page_num: int):
        try:
            url = self.config.URL if page_num == 1 else f"{self.config.URL}?page={page_num}"
            logging.info(f"Fetching page {page_num}: {url}")

            self.driver.get(url)
            WebDriverWait(self.driver, self.config.ELEMENT_WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )

            time.sleep(2)
            self.current_page = page_num
            return BeautifulSoup(self.driver.page_source, "html.parser")

        except TimeoutException:
            logging.error(f"Timeout loading page {page_num}")
            return None

    def extract_trade_from_row(self, row) -> Optional[Dict]:
        try:
            cells = row.find_all('td')
            if len(cells) < 9:
                return None

            politician_link = cells[0].find('a')
            politician = politician_link.text.strip() if politician_link else None

            issuer_link = cells[1].find('a')
            trade_issue = issuer_link.text.strip() if issuer_link else None

            trade_ticker = "N/A"
            for text in cells[1].stripped_strings:
                if text != trade_issue and text.isupper() and len(text) <= 6:
                    trade_ticker = text
                    break

            filed_after = self.extractor.parse_filed_after(cells[4].text.strip())
            trade_size = self.extractor.parse_trade_size(cells[7].text.strip())

            detail_link = row.find('a', href=lambda x: x and '/trades/' in x)
            if not detail_link:
                return None

            trade_id = ''.join(c for c in detail_link['href'] if c.isdigit())

            return {
                "trade_id": trade_id,
                "politician": politician,
                "trade_issue": trade_issue,
                "trade_ticker": trade_ticker,
                "filed_after": filed_after,
                "trade_size": trade_size,
                "trade_link": f"https://www.capitoltrades.com{detail_link['href']}"
            }

        except Exception:
            return None

    def meets_criteria(self, trade: Dict) -> bool:
        if trade["filed_after"] is None or trade["filed_after"] >= self.config.RECENT_DAYS:
            return False
        if not trade["trade_size"]:
            return False
        if trade["trade_size"][1] < self.config.MIN_TRADE_SIZE:
            return False
        if not trade["trade_ticker"] or trade["trade_ticker"] == "N/A":
            return False
        return True

    def run(self) -> Dict:
        if not self.setup_driver():
            return {"success": False, "error": "WebDriver init failed"}

        checked = self.checker.load_checked_ids()
        results = []

        try:
            for page in range(1, self.config.PAGES_TO_SCRAPE + 1):
                soup = self.fetch_page(page)
                if not soup:
                    break

                rows = soup.find_all('tr')[1:]
                for row in rows:
                    trade = self.extract_trade_from_row(row)
                    if not trade:
                        continue

                    if trade["trade_id"] in checked:
                        continue

                    if self.meets_criteria(trade):
                        results.append(trade)
                        self.checker.mark_as_checked(trade["trade_id"])

            return {
                "success": True,
                "trades": results,
                "metadata": {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "total_trades": len(results)
                }
            }

        finally:
            if self.driver:
                self.driver.quit()


# -----------------------------------------------------------------------------
# Entry point (n8n-safe)
# -----------------------------------------------------------------------------
def main():
    try:
        scraper = CapitolTradesScraperSelenium(Config())
        result = scraper.run()

        print(json.dumps(result))
        sys.exit(0 if result.get("success") else 1)

    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat()
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()
