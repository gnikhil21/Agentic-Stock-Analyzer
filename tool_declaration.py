from tools import get_price_history, get_stock_price, search_news

TOOL_FUNCTIONS = {
    "get_stock_price": lambda **kwargs: get_stock_price(kwargs["ticker"]),
    "search_news": lambda **kwargs: search_news(
        kwargs["query"], kwargs.get("max_results", 5)
    ),
    "get_price_history": lambda **kwargs: get_price_history(
        kwargs["ticker"], kwargs.get("days", 30)
    ),
}

TOOL_DECLARATIONS = [
    {
        "name": "get_stock_price",
        "description": (
            "Get the current price and today's % change for a single stock "
            "ticker. Use this first to check if a stock has moved significantly."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "NSE ticker with .NS suffix, e.g. 'HINDALCO.NS'",
                }
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "search_news",
        "description": (
            "Search recent news headlines for a company or topic. Use this "
            "when a stock has moved significantly and you need to explain why."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term, e.g. company name like 'Hindalco Industries'",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of headlines to fetch (default 5)",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_price_history",
        "description": (
            "Get OHLC price history for a ticker over the past N days. Use this "
            "to check if a move is part of a larger trend or an isolated spike."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "NSE ticker with .NS suffix"},
                "days": {"type": "integer", "description": "Number of days to look back"},
            },
            "required": ["ticker"],
        },
    },
]