Funding Round Verifier
A tool to verify the authenticity of funding rounds for companies or projects by analyzing news sources.

Goal
Verify the validity of reported funding rounds by analyzing reliable sources.

Features
Automated verification of funding round information
Source validation through news content analysis
Fallback to web search when direct sources aren't provided
Implementation Plan
Data Collection

Accept input data containing funding round details
Extract company name, funding amount, date, and news source links
Source Validation

If news link is provided:
Scrape the webpage content
Extract relevant information about the funding round
If no news link is provided:
Use web search capabilities to find reliable sources
Prioritize established financial/tech news outlets
Content Analysis

Process the news content using LLM
Extract key details (company, amount, investors, date)
Compare extracted details with provided information
Verification Logic

Establish confidence score based on source reliability
Flag discrepancies between reported and verified information
Generate detailed verification report
Output Generation

Provide verification status (Verified/Unverified/Inconclusive)
Include supporting evidence and confidence level
Document any discrepancies found
Tech Stack
Python: Core programming language
OpenAI API: For content analysis and verification
Pydantic: For data validation and modeling
BeautifulSoup/Scrapy: For web scraping
Getting Started
run the script : make sure you are in /workspaces/rounds-verifier

python3 src/main.py



