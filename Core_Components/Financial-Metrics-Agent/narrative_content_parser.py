from sec_api import ExtractorApi

extractorApi = ExtractorApi("YOUR_API_KEY")

# 10-K example - Tesla filing
filing_url = "https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231.htm"

# Get Risk Factors as clean text
risk_factors = extractorApi.get_section(filing_url, "1A", "text")

# Get MD&A as HTML
mda = extractorApi.get_section(filing_url, "7", "html")

# 10-Q example
filing_url_10q = "https://www.sec.gov/Archives/edgar/data/1318605/000095017022006034/tsla-20220331.htm"
risk_factors_10q = extractorApi.get_section(filing_url_10q, "part2item1a", "text")