Agentic Stock Analysis Assistant

An AI-powered stock analysis assistant built using Google Gemini Function Calling that autonomously invokes external tools to answer stock market queries. Instead of relying solely on the LLM's internal knowledge, the agent dynamically decides which tools to use, retrieves live financial data, and combines the results to generate context-aware responses.

Features
- Retrieve real-time stock prices for NSE-listed companies.
- Fetch historical OHLC price data for user-specified time periods.
- Search recent company and market news using Google News RSS.
- Autonomous tool selection through Gemini Function Calling.
- Modular architecture for easily integrating additional financial analysis tools.

Tech Stack
- Python
- Google Gemini API
- Function Calling
- yFinance
- Google News RSS
- Python Tool Orchestration

Example Queries
- What is the current price of BEL.NS?
- Show me the last 30 days of price history for HINDALCO.NS.
- Why is Suzlon Energy moving today?
- Give me the latest news for Tata Motors.
- Compare today's price with the last week's trend for Infosys.
