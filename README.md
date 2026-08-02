AI Financial Research Agent

An intelligent financial research assistant built using LangGraph and Google Gemini that answers stock market queries through autonomous tool execution and persistent semantic memory.
The agent combines tool calling, conversational reasoning, and long-term vector memory to provide personalized responses based on both live financial data and previously learned user preferences.

Features
- AI-powered conversational stock analysis.
- Real-time stock prices using Yahoo Finance.
- Historical OHLC price history for custom time periods.
- Latest company and market news via Google News RSS.
- Autonomous tool selection using Gemini Function Calling.
- Long-term semantic memory using ChromaDB and Gemini Embeddings.
- Automatic extraction and storage of durable user preferences.
- Memory deduplication through embedding similarity search.
- Modular LangGraph workflow designed for future extension with additional financial analysis tools.

Tech Stack
- Python
- LangGraph
- Google Gemini 3.1 Flash Lite
- Gemini Embeddings
- LangChain
- ChromaDB
- yFinance
- Google News RSS
- Function Calling

Example Queries
- What is the current price of BEL.NS?
- Show me the last 60 days of Tata Motors.
- Why is Reliance moving today?
- Based on my previous investment preferences, suggest some Indian semiconductor stocks.
- What stocks have I shown interest in before?
- Give me the latest news for Hindalco.
