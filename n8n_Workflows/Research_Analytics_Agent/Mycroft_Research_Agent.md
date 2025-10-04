# Mycroft Research Agent

## Overview

The **Mycroft Research Agent** is an educational n8n workflow that demonstrates AI-powered investment analysis. Named after Sherlock Holmes's analytical elder brother, this system combines financial data analysis with patent intelligence to evaluate AI companies.

## What It Does

- **Analyzes AI companies** using their stock ticker symbols
- **Combines financial metrics** with patent portfolio analysis
- **Generates investment recommendations** with scoring and risk assessment
- **Produces comprehensive reports** in multiple formats
- **Uses live data** from financial APIs and Google Search

## System Architecture

### Core Components

1. **Data Collection Layer**: Gathers financial and patent data
2. **Processing Layer**: Cleans and analyzes collected data
3. **Analysis Engine**: Combines data for investment scoring
4. **Report Generator**: Creates comprehensive investment analysis

## Node-by-Node Breakdown

### 1. Company Input (Set Node)

**Type**: Set Node  
**Purpose**: Entry point for stock ticker symbols

**What It Does**:
- Sets the stock ticker symbol to analyze (e.g., "NVDA", "GOOGL")
- Provides default value for testing
- Acts as the workflow trigger

**Configuration**:
- Variable Name: `ticker`
- Default Value: `NVDA` (NVIDIA)
- Type: String

This is where you specify which company to analyze. Simply change the ticker symbol to analyze different companies.

### 2. Get Financial Overview (HTTP Request)

**Type**: HTTP Request Node  
**Purpose**: Fetch comprehensive company financial data

**What It Does**:
- Connects to Alpha Vantage API
- Downloads company overview data including:
  - Market capitalization
  - Revenue and profit margins
  - P/E ratio and valuation metrics
  - Sector and industry classification
  - Company description

**Configuration**:
- Method: GET
- URL: `https://www.alphavantage.co/query`
- Function: `OVERVIEW`
- Required: Alpha Vantage API key

This node gets basic company information like how big the company is, how profitable it is, and what industry it's in.

### 3. Get Income Statement (HTTP Request)

**Type**: HTTP Request Node  
**Purpose**: Fetch detailed financial statements

**What It Does**:
- Downloads annual financial reports
- Extracts R&D (Research & Development) spending
- Provides revenue breakdowns
- Gets profitability details over time

**Configuration**:
- Method: GET
- URL: `https://www.alphavantage.co/query`
- Function: `INCOME_STATEMENT`
- Required: Alpha Vantage API key

This node gets detailed information about how much money the company makes and spends, especially on research and development (which is crucial for AI companies).

### 4. Process Company Data (Function Node)

**Type**: Function Node  
**Purpose**: Prepare company data for patent search

**What It Does**:
- Extracts clean company name from financial data
- Removes corporate suffixes (Inc, Corp, Ltd, etc.)
- Handles special cases (e.g., Alphabet → Google for better search results)
- Prepares data structure for subsequent nodes

**Code Functionality**:
- String cleaning and normalization
- Data validation
- Search query preparation

This node cleans up the company name so it can be properly searched for patents. For example, it changes "NVIDIA Corporation" to just "NVIDIA" for better search results.

### 5. Google Patent Search (HTTP Request)

**Type**: HTTP Request Node  
**Purpose**: Search for patent-related information using Google

**What It Does**:
- Searches Google for patent information about the company
- Looks for AI-related patents specifically
- Finds recent patent filings (2023-2024)
- Collects patent news and announcements

**Configuration**:
- Method: GET
- URL: `https://www.googleapis.com/customsearch/v1`
- Required: Google Custom Search API key and Search Engine ID
- Query: `[Company] patents AI artificial intelligence machine learning recent 2023 2024`

This node searches the internet for information about the company's patents, especially those related to artificial intelligence. Patents show how innovative a company is.

### 6. Process Patent Data (Function Node)

**Type**: Function Node  
**Purpose**: Analyze search results to extract patent intelligence

**What It Does**:
- Counts patent mentions in search results
- Identifies AI-related content
- Estimates total patent portfolio size
- Calculates AI patent ratio
- Generates realistic patent examples
- Assigns patent quality scores

**Key Calculations**:
- **Patent Count Estimation**: Based on search mentions + company type
- **AI Patent Ratio**: Percentage of patents related to AI
- **Patent Quality Score**: 0-100 scale based on portfolio strength
- **Competitive Moat Assessment**: Very Strong/Strong/Moderate/Developing/Weak

This node analyzes the search results to understand how many patents the company has and how many are related to AI. More AI patents usually means the company is more innovative.

### 7. Process Financial Data (Function Node)

**Type**: Function Node  
**Purpose**: Calculate comprehensive financial health metrics

**What It Does**:
- Parses all financial values safely (handles missing data)
- Calculates R&D intensity (R&D spending as % of revenue)
- Computes financial ratios and margins
- Estimates missing R&D data based on company type
- Categorizes market capitalization (Mega Cap, Large Cap, etc.)

**Key Metrics Calculated**:
- **R&D Intensity**: How much the company invests in research
- **Profit Margins**: How profitable the company is
- **Return on Equity**: How efficiently the company uses investor money
- **Market Cap Category**: Company size classification

This node crunches all the financial numbers to understand how healthy and profitable the company is, and how much they invest in research and development.

### 8. Generate Analysis (Function Node)

**Type**: Function Node  
**Purpose**: Core scoring and recommendation engine

**What It Does**:
- **Innovation Scoring (0-100)**: Combines R&D intensity + Patent portfolio + AI focus
- **Financial Scoring (0-100)**: Evaluates profitability + valuation + scale + efficiency
- **Overall Score**: Weighted combination (65% innovation + 35% financial)
- **Risk Assessment**: LOW/MEDIUM/HIGH risk levels
- **Confidence Rating**: HIGH/MODERATE/LOW based on data quality
- **Investment Recommendation**: STRONG BUY/BUY/HOLD/SELL

**Scoring Methodology**:

**Innovation Score (65% weight)**:
- R&D Intensity: 30 points max
- Patent Portfolio: 40 points max
- AI Patent Focus: 30 points max

**Financial Score (35% weight)**:
- Profitability: 25 points max
- Valuation: 20 points max
- Scale: 20 points max
- Efficiency: 15 points max

This is the "brain" of the system. It combines all the financial and patent information to give the company a score and make an investment recommendation (like "BUY" or "SELL").

### 9. Generate Final Report (Function Node)

**Type**: Function Node  
**Purpose**: Create comprehensive investment analysis report

**What It Does**:
- Formats all analysis into professional report
- Generates letter grades (A+ to F) for each category
- Creates investment thesis based on strengths
- Identifies risk factors and opportunities
- Assembles technical metadata and methodology notes
- Produces JSON output with complete analysis

**Report Sections**:
- **Executive Summary**: Key recommendation and scores
- **Financial Analysis**: Complete financial breakdown
- **Innovation Analysis**: Patent and R&D assessment
- **Investment Thesis**: Why to invest or not
- **Risk Factors**: What could go wrong
- **Opportunity Factors**: Growth potential
- **Technical Notes**: Data quality and methodology

This node takes all the analysis and creates a professional-looking report that explains whether you should invest in the company and why.

### 10. Report Download (Python Code Node)

**Type**: Code Node (Python)  
**Purpose**: Format report for browser download

**What It Does**:
- Creates detailed text report with professional formatting
- Generates CSV data for spreadsheet analysis
- Adds comprehensive company analysis
- Includes patent portfolio breakdown
- Provides download instructions
- Outputs both text and spreadsheet formats

**Output Formats**:
- **Text Report**: Complete analysis with emojis and formatting
- **CSV Data**: Structured data for Excel/Google Sheets
- **Console Instructions**: Step-by-step download guide