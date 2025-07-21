# SEC EDGAR Document Fetcher

## What the Current Code Does

The script successfully downloads raw SEC filing documents for any stock ticker using the free SEC EDGAR API. It converts ticker symbols to SEC identification numbers, finds recent filings, and downloads the complete document content to local files.

**Current Capabilities:**
- Retrieves company information from ticker symbols
- Downloads latest 10-K, 10-Q, or 8-K filings
- Saves complete document content locally
- Provides basic filing metadata and preview

## Current Limitations

- **Raw format**: Downloads unprocessed SGML/HTML with SEC headers and formatting
- **No parsing**: Cannot extract specific sections or clean text
- **No financial extraction**: Cannot access structured financial data
- **Single filing focus**: Only gets latest filing, no historical analysis
- **Basic error handling**: Limited troubleshooting and retry capabilities