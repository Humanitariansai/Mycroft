from edgar import *

# Set your identity (required by SEC)
set_identity("your.email@example.com")

# Get company filings
company = Company("AAPL")
filings = company.get_filings(form="10-K")

# Get latest 10-K
filing = filings[0]

# Extract text content (this likely includes narrative sections)
text = filing.text()

print(text[0:1000]) # Print first 1000 characters of the text