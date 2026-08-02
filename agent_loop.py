import os
from tools import get_price_history, get_stock_price, search_news
from google import genai
from google.genai import types
from tool_declaration import TOOL_DECLARATIONS, TOOL_FUNCTIONS 
from dotenv import load_dotenv

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

client = genai.Client()
model = "gemini-3.1-flash-lite"

SYSTEM_INSTRUCTION = (
    "You are a financial monitoring assistant. You have tools to check stock "
    "prices, price history, and news. Answer user queries based on the tools available. Be concise and "
    "cite what you found."
)

tools = types.Tool(function_declarations=TOOL_DECLARATIONS)

def run_agent(prompt):
    
    
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        tools = [tools]
    )
    
    contents = [types.Content(role="user", parts=[types.Part(text=prompt)])]
    trace_calls = []
    trace_results = []
    for i in range(3):
        #query = input(prompt)
        response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
        #print("Agent Response:", response)
        print("Tokens used: ", response.usage_metadata.total_token_count)
        parts = response.candidates[0].content.parts
        
        function_calls = [part for part in parts if part.function_call is not None]
        text_parts = [part for part in parts if part.text is not None]
        
        
        
        if text_parts:
            for text_part in text_parts:
                print("Text Parts:", text_part.text)
        else:
            print("No text parts found in the response.")
            
        if len(function_calls) == 0:
            print("No function calls found in the response.")
            return {
                "text" : "\n".join([text_part.text for text_part in text_parts]),
                "result": trace_results,
                "trace_calls": trace_calls
            }
        
        contents.append(response.candidates[0].content)
        resonse_parts = []
        for function_call in function_calls:
            tool_name = function_call.function_call.name
            tool_args = function_call.function_call.args
            trace_calls.append({"tool_name": tool_name, "tool_args": tool_args})
            
            print("Function Call Name:", tool_name)
            print("Function Call Arguments:", tool_args)
            if tool_name in TOOL_FUNCTIONS:
                try:
                    result = TOOL_FUNCTIONS[tool_name](**tool_args)
                    print("Function Result:", result)
                except Exception as e:
                    result = {"error": f"Error occurred while executing tool '{tool_name}': {str(e)}"}
            else:
                result = {"error": f"Tool '{tool_name}' not found."}
            
            trace_results.append(result)
            resonse_parts.append(
                types.Part.from_function_response(
                    name=tool_name,
                    response={"result": result}
                )
            )
            
            print("-"*50)
        print("trace_calls:", trace_calls)
        contents.append(types.Content(role="user", parts=resonse_parts))
        
    return {
        "text": "Maximum iteration reached before getting a final answer.",
        "result": trace_results,
        "trace_calls": trace_calls
    }
      
if __name__ == "__main__":  
    prompt = (
            #f"Has Hindustan Copper been trending up or down over the last 1 week?"
            #f"Analyze the price history for Hindustan Copper over the last 7 days and determine if it has been trending up or down."
            f"Check reliance stock price and if it moved more than 0.2%"
            "in the last week, investigate why using news, and summarize each."
        )
    run_agent(prompt)