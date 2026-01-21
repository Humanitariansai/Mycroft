import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class StockPriceAnalyzer:
    """Analyzes stock price trends around congressional trade dates."""
    
    def __init__(self, days_before: int = 30, days_after: int = 30):
        self.days_before = days_before
        self.days_after = days_after
        self.cache_dir = Path("stock_data_cache")
        self.cache_dir.mkdir(exist_ok=True)
    
    def parse_trade_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats from Capitol Trades."""
        if not date_str:
            return None
        
        date_str = date_str.strip()
        
        # Handle formats like "9 Dec2025" -> "9 Dec 2025"
        import re
        date_str = re.sub(r'([A-Za-z])(\d{4})', r'\1 \2', date_str)
        
        date_formats = [
            "%d %b %Y",      # 9 Dec 2025
            "%d %B %Y",      # 9 December 2025
            "%m/%d/%Y",      # 12/09/2025
            "%Y-%m-%d",      # 2025-12-09
            "%m/%d/%y",      # 12/09/25
            "%B %d, %Y",     # December 9, 2025
            "%b %d, %Y",     # Dec 9, 2025
            "%d-%b-%Y",      # 9-Dec-2025
            "%d-%B-%Y",      # 9-December-2025
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        logging.warning(f"Could not parse date: {date_str}")
        return None
    
    def normalize_ticker(self, ticker: str) -> List[str]:
        """Generate possible ticker variations for lookup."""
        ticker = ticker.strip().upper()
        
        # Remove common exchange suffixes
        ticker_base = ticker.split(':')[0].split('.')[0]
        
        variations = [ticker_base]
        
        # Add common variations
        if ticker_base != ticker:
            variations.append(ticker)
        
        # For ADRs or foreign stocks, try common suffixes
        if len(ticker_base) > 4:  # Likely ADR
            variations.extend([
                ticker_base,
                f"{ticker_base[:-1]}",  # Remove last character
            ])
        
        return variations
    
    def get_stock_data(self, ticker: str, start_date: datetime, 
                       end_date: datetime) -> Optional[pd.DataFrame]:
        """Fetch stock data using yfinance (free Yahoo Finance API)."""
        ticker_variations = self.normalize_ticker(ticker)
        
        for attempt_ticker in ticker_variations:
            try:
                # Check cache first
                cache_file = self.cache_dir / f"{attempt_ticker}_{start_date.date()}_{end_date.date()}.json"
                
                if cache_file.exists():
                    logging.info(f"Loading cached data for {attempt_ticker}")
                    df = pd.read_json(cache_file)
                    df.index = pd.to_datetime(df.index)
                    return df
                
                logging.info(f"Fetching data for {attempt_ticker} from {start_date.date()} to {end_date.date()}")
                stock = yf.Ticker(attempt_ticker)
                df = stock.history(start=start_date, end=end_date)
                
                if not df.empty:
                    df.to_json(cache_file)
                    if attempt_ticker != ticker:
                        logging.info(f"✓ Found data using normalized ticker: {attempt_ticker} (original: {ticker})")
                    return df
            
            except Exception as e:
                logging.debug(f"Failed to fetch {attempt_ticker}: {e}")
                continue
        
        logging.warning(f"No data found for {ticker} (tried: {', '.join(ticker_variations)})")
        return None
    
    def calculate_metrics(self, df: pd.DataFrame, trade_date: datetime) -> Dict:
        """Calculate key metrics around the trade date."""
        try:
            # Convert trade_date to timezone-aware if df has timezone
            if df.index.tz is not None:
                trade_date_normalized = pd.Timestamp(trade_date).tz_localize(df.index.tz).normalize()
            else:
                trade_date_normalized = pd.Timestamp(trade_date).normalize()
            
            # Find closest trading day to trade date
            closest_idx = df.index.get_indexer([trade_date_normalized], method='nearest')[0]
            if closest_idx == -1:
                return {}
            
            trade_price = df.iloc[closest_idx]['Close']
            actual_trade_date = df.index[closest_idx]
            
            # Split data into before and after
            before_df = df[df.index < actual_trade_date]
            after_df = df[df.index >= actual_trade_date]
            
            metrics = {
                'trade_price': round(trade_price, 2),
                'actual_trade_date': actual_trade_date.strftime('%Y-%m-%d')
            }
            
            # Calculate price changes
            if len(before_df) > 0:
                start_price = before_df.iloc[0]['Close']
                metrics['price_before_start'] = round(start_price, 2)
                metrics['change_to_trade'] = round(((trade_price - start_price) / start_price) * 100, 2)
            
            if len(after_df) > 1:
                end_price = after_df.iloc[-1]['Close']
                metrics['price_after_end'] = round(end_price, 2)
                metrics['change_after_trade'] = round(((end_price - trade_price) / trade_price) * 100, 2)
            
            # Volume analysis
            if 'Volume' in df.columns:
                avg_volume_before = before_df['Volume'].mean() if len(before_df) > 0 else 0
                trade_volume = df.iloc[closest_idx]['Volume']
                metrics['avg_volume_before'] = int(avg_volume_before)
                metrics['trade_day_volume'] = int(trade_volume)
                if avg_volume_before > 0:
                    metrics['volume_ratio'] = round(trade_volume / avg_volume_before, 2)
            
            # Volatility (using std of returns)
            if len(df) > 1:
                returns = df['Close'].pct_change()
                metrics['volatility'] = round(returns.std() * 100, 2)
            
            return metrics
        
        except Exception as e:
            logging.error(f"Error calculating metrics: {e}")
            return {}
    
    def plot_trend(self, df: pd.DataFrame, trade_date: datetime, 
                   ticker: str, politician: str, transaction_type: str,
                   save_path: Optional[str] = None) -> str:
        """Create a visualization of the stock trend."""
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), 
                                           gridspec_kw={'height_ratios': [3, 1]})
            
            # Price chart
            ax1.plot(df.index, df['Close'], linewidth=2, label='Close Price', color='#2E86AB')
            
            # Mark trade date - handle timezone
            if df.index.tz is not None:
                trade_date_normalized = pd.Timestamp(trade_date).tz_localize(df.index.tz).normalize()
            else:
                trade_date_normalized = pd.Timestamp(trade_date).normalize()
            
            closest_idx = df.index.get_indexer([trade_date_normalized], method='nearest')[0]
            actual_trade_date = df.index[closest_idx]
            trade_price = df.iloc[closest_idx]['Close']
            
            ax1.axvline(x=actual_trade_date, color='red', linestyle='--', 
                       linewidth=2, label='Trade Date', alpha=0.7)
            ax1.scatter([actual_trade_date], [trade_price], color='red', 
                       s=200, zorder=5, marker='o', edgecolors='darkred', linewidth=2)
            
            # Shading
            ax1.axvspan(df.index[0], actual_trade_date, alpha=0.1, color='blue', 
                       label='Before Trade')
            ax1.axvspan(actual_trade_date, df.index[-1], alpha=0.1, color='green', 
                       label='After Trade')
            
            ax1.set_xlabel('Date', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Price ($)', fontsize=12, fontweight='bold')
            ax1.set_title(f'{ticker} - {politician} ({transaction_type})\n'
                         f'Trade Date: {actual_trade_date.strftime("%Y-%m-%d")} | '
                         f'Price: ${trade_price:.2f}',
                         fontsize=14, fontweight='bold', pad=20)
            ax1.legend(loc='best', fontsize=10)
            ax1.grid(True, alpha=0.3)
            
            # Volume chart
            colors = ['green' if df['Close'].iloc[i] >= df['Open'].iloc[i] 
                     else 'red' for i in range(len(df))]
            ax2.bar(df.index, df['Volume'], color=colors, alpha=0.6, width=0.8)
            ax2.axvline(x=actual_trade_date, color='red', linestyle='--', 
                       linewidth=2, alpha=0.7)
            ax2.set_xlabel('Date', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Volume', fontsize=12, fontweight='bold')
            ax2.set_title('Trading Volume', fontsize=12, fontweight='bold')
            ax2.grid(True, alpha=0.3, axis='y')
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logging.info(f"Chart saved to {save_path}")
                return save_path
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"charts/{ticker}_{politician.replace(' ', '_')}_{timestamp}.png"
                Path("charts").mkdir(exist_ok=True)
                plt.savefig(filename, dpi=300, bbox_inches='tight')
                logging.info(f"Chart saved to {filename}")
                return filename
        
        except Exception as e:
            logging.error(f"Error creating plot: {e}")
            return ""
        finally:
            plt.close()
    
    def analyze_trade(self, trade_data: Dict) -> Dict:
        """Analyze a single trade with stock price data."""
        try:
            ticker = trade_data.get('trade_ticker')
            traded_date_str = trade_data.get('traded_date')
            
            if not ticker or ticker == "N/A" or not traded_date_str:
                return {'error': 'Missing ticker or trade date'}
            
            trade_date = self.parse_trade_date(traded_date_str)
            if not trade_date:
                return {'error': f'Could not parse date: {traded_date_str}'}
            
            start_date = trade_date - timedelta(days=self.days_before)
            end_date = trade_date + timedelta(days=self.days_after)
            
            df = self.get_stock_data(ticker, start_date, end_date)
            if df is None or df.empty:
                return {'error': f'No stock data available for {ticker}'}
            
            metrics = self.calculate_metrics(df, trade_date)
            
            chart_path = self.plot_trend(
                df, trade_date, ticker,
                trade_data.get('politician', 'Unknown'),
                trade_data.get('transaction_type', 'Unknown')
            )
            
            result = {
                'ticker': ticker,
                'politician': trade_data.get('politician'),
                'party': trade_data.get('party'),
                'transaction_type': trade_data.get('transaction_type'),
                'trade_date': traded_date_str,
                'filed_after': trade_data.get('filed_after'),
                'trade_size_range': trade_data.get('trade_size'),
                'metrics': metrics,
                'chart_path': chart_path,
                'trade_link': trade_data.get('trade_link')
            }
            
            return result
        
        except Exception as e:
            logging.error(f"Error analyzing trade: {e}")
            return {'error': str(e)}
    
    def analyze_all_trades(self, trades: List[Dict]) -> List[Dict]:
        """Analyze all trades from scraper."""
        results = []
        success_count = 0
        error_count = 0
        
        for i, trade in enumerate(trades, 1):
            logging.info(f"\n{'='*60}")
            logging.info(f"Analyzing trade {i}/{len(trades)}")
            logging.info(f"Ticker: {trade.get('trade_ticker', 'N/A')} | Politician: {trade.get('politician', 'N/A')}")
            logging.info(f"{'='*60}")
            
            result = self.analyze_trade(trade)
            
            if 'error' in result:
                error_count += 1
                logging.warning(f"✗ Analysis failed: {result['error']}")
            else:
                success_count += 1
                logging.info(f"✓ Analysis complete")
            
            results.append(result)
        
        logging.info(f"\n{'='*80}")
        logging.info(f"ANALYSIS SUMMARY")
        logging.info(f"{'='*80}")
        logging.info(f"Total trades: {len(trades)}")
        logging.info(f"Successful: {success_count}")
        logging.info(f"Failed: {error_count}")
        logging.info(f"Success rate: {(success_count/len(trades)*100):.1f}%")
        logging.info(f"{'='*80}")
        
        return results
    
    def generate_report(self, results: List[Dict], output_file: str = None):
        """Generate a comprehensive report."""
        if not results:
            print("No results to report")
            return
        
        report = []
        report.append("\n" + "="*100)
        report.append(f"CONGRESSIONAL TRADING ANALYSIS REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Trades Analyzed: {len(results)}")
        report.append("="*100 + "\n")
        
        successful = [r for r in results if 'error' not in r]
        failed = [r for r in results if 'error' in r]
        
        for i, result in enumerate(successful, 1):
            report.append(f"\nTRADE #{i}")
            report.append("-"*80)
            report.append(f"Politician: {result['politician']} ({result['party']})")
            report.append(f"Transaction: {result['transaction_type']}")
            report.append(f"Ticker: {result['ticker']}")
            report.append(f"Trade Date: {result['trade_date']}")
            report.append(f"Filed After: {result['filed_after']} days")
            
            if result['trade_size_range']:
                report.append(f"Trade Size: ${result['trade_size_range'][0]:,} - ${result['trade_size_range'][1]:,}")
            
            metrics = result.get('metrics', {})
            if metrics:
                report.append(f"\nPRICE ANALYSIS:")
                report.append(f"  Trade Price: ${metrics.get('trade_price', 'N/A')}")
                
                if 'change_to_trade' in metrics:
                    change = metrics['change_to_trade']
                    report.append(f"  Price Change (30 days before): {change:+.2f}%")
                
                if 'change_after_trade' in metrics:
                    change = metrics['change_after_trade']
                    report.append(f"  Price Change (30 days after): {change:+.2f}%")
                
                if 'volatility' in metrics:
                    report.append(f"  Volatility: {metrics['volatility']:.2f}%")
                
                if 'volume_ratio' in metrics:
                    report.append(f"  Volume Ratio (vs avg): {metrics['volume_ratio']:.2f}x")
            
            if result.get('chart_path'):
                report.append(f"\nChart: {result['chart_path']}")
            
            report.append(f"Details: {result['trade_link']}")
            report.append("")
        
        if failed:
            report.append(f"\n{'='*80}")
            report.append(f"FAILED ANALYSES: {len(failed)}")
            report.append(f"{'='*80}")
            for fail in failed:
                report.append(f"Error: {fail.get('error', 'Unknown error')}")
        
        report_text = "\n".join(report)
        print(report_text)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
            logging.info(f"Report saved to {output_file}")
        
        # Save JSON for programmatic access
        json_file = output_file.replace('.txt', '.json') if output_file else 'analysis_results.json'
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logging.info(f"JSON data saved to {json_file}")


def load_trades_from_file(filename: str = None) -> List[Dict]:
    """Load trades from the most recent filtered_trades file."""
    try:
        if filename:
            filepath = Path(filename)
        else:
            # Find most recent filtered_trades file
            trade_files = list(Path('.').glob('filtered_trades_*.txt'))
            if not trade_files:
                logging.error("No filtered_trades files found")
                return []
            filepath = max(trade_files, key=lambda p: p.stat().st_mtime)
        
        logging.info(f"Loading trades from: {filepath}")
        
        trades = []
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Parse the text file format
        trade_blocks = content.split('Trade #')[1:]  # Skip header
        
        for block in trade_blocks:
            lines = block.strip().split('\n')
            trade = {}
            
            for line in lines:
                if ':' not in line:
                    continue
                
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if key == 'Politician':
                    # Extract party from "(Republican)" or "(Democrat)"
                    if '(' in value:
                        name, party = value.rsplit('(', 1)
                        trade['politician'] = name.strip()
                        trade['party'] = party.rstrip(')')
                    else:
                        trade['politician'] = value
                        trade['party'] = 'Unknown'
                
                elif key == 'Transaction':
                    trade['transaction_type'] = value
                
                elif key == 'Company':
                    # Extract ticker from "Company Name (TICKER)"
                    if '(' in value:
                        company, ticker = value.rsplit('(', 1)
                        trade['trade_issue'] = company.strip()
                        trade['trade_ticker'] = ticker.rstrip(')')
                    else:
                        trade['trade_issue'] = value
                        trade['trade_ticker'] = 'N/A'
                
                elif key == 'Size':
                    # Parse "$1,000 - $15,000" format
                    size_parts = value.replace(',', '').split('-')
                    if len(size_parts) == 2:
                        try:
                            trade['trade_size'] = [int(size_parts[0].strip()), 
                                                  int(size_parts[1].strip())]
                        except ValueError:
                            trade['trade_size'] = None
                
                elif key == 'Filed After':
                    try:
                        trade['filed_after'] = int(value.split()[0])
                    except (ValueError, IndexError):
                        trade['filed_after'] = None
                
                elif key == 'Traded':
                    trade['traded_date'] = value
                
                elif key == 'Published':
                    trade['published'] = value
                
                elif key == 'Price':
                    trade['price'] = value
                
                elif key == 'Link':
                    trade['trade_link'] = value
                    # Extract trade_id from link
                    import re
                    match = re.search(r'/trades/(\d+)', value)
                    if match:
                        trade['trade_id'] = match.group(1)
            
            if trade.get('trade_ticker') and trade.get('traded_date'):
                trades.append(trade)
        
        logging.info(f"Loaded {len(trades)} trades from file")
        return trades
    
    except Exception as e:
        logging.error(f"Error loading trades from file: {e}")
        return []


def main(filename: str = None, run_scraper: bool = False):
    """
    Main function with options to load from file or run scraper.
    
    Args:
        filename: Specific filtered_trades file to analyze (optional)
        run_scraper: If True, run scraper first to get fresh data
    """
    if run_scraper:
        from scraper import main as scraper_main
        print("Running Capitol Trades scraper...")
        trades = scraper_main()
    else:
        trades = load_trades_from_file(filename)
    
    if not trades:
        print("No trades found to analyze")
        return
    
    # Analyze trades
    print(f"\nAnalyzing {len(trades)} trades...")
    analyzer = StockPriceAnalyzer(days_before=30, days_after=30)
    results = analyzer.analyze_all_trades(trades)
    
    # Generate report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"analysis_report_{timestamp}.txt"
    analyzer.generate_report(results, report_file)
    
    return results


if __name__ == "__main__":
    main()