from dataclasses import dataclass
import json
from agent_loop import run_agent, model
from google import genai
from google.genai import types

@dataclass
class EvalCase:
    id: str
    prompt: str
    expected_tools: set[str]
    notes: str = ""
 
 
EVAL_SET: list[EvalCase] = [
    # EvalCase(
    #     id="price_only_1",
    #     prompt="What's the current price of HINDALCO.NS?",
    #     expected_tools={"get_stock_price"},
    #     notes="Simple price question — should NOT trigger news search.",
    # ),
    # EvalCase(
    #     id="price_only_2",
    #     prompt="How much is Suzlon Energy trading at right now?",
    #     expected_tools={"get_stock_price"},
    #     notes="Same intent, phrased naturally instead of using the ticker directly.",
    # ),
    # EvalCase(
    #     id="news_only_1",
    #     prompt="What's the latest news on Amara Raja Energy & Mobility?",
    #     expected_tools={"search_news"},
    #     notes="Pure news question — should NOT need a price check.",
    # ),
    # EvalCase(
    #     id="trend_check_1",
    #     prompt="Has Hindustan Copper been trending up or down over the last month?",
    #     expected_tools={"get_price_history"},
    #     notes="Trend question — should use history, not just a single price point.",
    # ),
    EvalCase(
        id="watchlist_digest_1",
        prompt=(
            "Check reliance, data patterns stocks. For any that moved more than 0.1% "
            "today, investigate why using news, and summarize each."
        ),
        expected_tools={"get_stock_price", "search_news"},
        notes=(
            "Digest case — get_stock_price for both is required. search_news "
            "is conditionally required only if a mover is found; we treat it "
            "as expected here but flag (not fail) if skipped — see scoring note."
        ),
    ),
]

client = genai.Client()

answer_faithfullness_template = """
    You are an expert evaluator of AI-generated answers. 
    Below is AI assistans answer and the raw tool data it used to generate that answer.
    
    Your job:- Determine if the answer cantains any claim not supported by the tool data (hallucination),
        or any number not present in the tool data.
    
    TOOL DATA:
    {tool_data}
    
    answer:
    {answer}
    
    Respond only with a json object in the format:-
    {{"faithful": true or false, "issues": ["short description of each unsupported claim, empty list if faithful"]}}
"""

def score_tool_selection(actual_calls: list[dict], expected_tools: list[str]):
    """
    Scores the tool selection for a given evaluation case.
    """
    
    actual_tools = {call["tool_name"] for call in actual_calls}
    
    missing_tools = expected_tools - actual_tools
    extra_tools = actual_tools - expected_tools

    precision = len(actual_tools & expected_tools) / len(actual_tools) if actual_tools else 1.0
    recall = len(actual_tools & expected_tools) / len(expected_tools) if expected_tools else 1.0
    
    return {
        "precision": precision,
        "recall": recall,
        "missing_tools": missing_tools,
        "extra_tools": extra_tools
    }
    
def answer_faithfullness(response_text:str, response):
    
    tool_data = json.dumps(response, indent=2)
    answer_faithfullness_prompt = answer_faithfullness_template.format(tool_data=tool_data, answer=response_text)
    
    response = client.models.generate_content(
            model=model,
            contents=answer_faithfullness_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
    
    return {
        "faithful": response.text.get("faithful", False),
        "issues": response.text.get("issues", [])
    }

def run_eval():
    """
    Runs the evaluation set and prints results.
    """
    for case in EVAL_SET:
        
        # Here you would call your agent with the prompt and capture the actual tool calls
        # For demonstration, let's assume we have a function `run_agent` that returns the trace_calls
        print(f"Prompt: {case.prompt}")
        agent_response = run_agent(case.prompt) 
        trace_calls = agent_response.get("trace_calls", []) # This should return a list of dicts with tool_name and tool_args
        result = agent_response.get("result", []) # This should return the raw tool data used by the agent
        text = agent_response.get("text", "") # This should return the text response from the agent
        
        if not trace_calls:
            print("No tool calls were made by the agent. Check the agent's response and ensure it is functioning correctly.")
            return
        
        score = score_tool_selection(trace_calls, case.expected_tools)
        faithfulness = answer_faithfullness(text, result)

        print(f"Actual Tool Calls: {[call['tool_name'] for call in trace_calls]}")
        print(f"Score: Precision={score['precision']:.2f}, Recall={score['recall']:.2f}")
        if score['missing_tools']:
            print(f"Missing Tools: {score['missing_tools']}")
        if score['extra_tools']:
            print(f"Extra Tools: {score['extra_tools']}")
        print(f"Answer Faithfulness: {faithfulness['faithful']}")
        if faithfulness['issues']:
            print(f"Issues: {faithfulness['issues']}")
        print("="*100)
        print("="*100)
       
if __name__ == "__main__": 
    run_eval()