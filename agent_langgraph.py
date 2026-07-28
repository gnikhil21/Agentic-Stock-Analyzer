from tools import get_price_history, get_stock_price, search_news,check_watchlist
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
import os
from dotenv import load_dotenv

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

TOOLS = [get_price_history, get_stock_price, search_news, check_watchlist]
llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0.3)
llm_with_tools = llm.bind_tools(TOOLS)

SYSTEM_INSTRUCTION = (
    "You are a financial monitoring assistant. You have tools to check stock "
    "prices, price history, and news. Answer user queries based on the tools available. Be concise and "
    "cite what you found."
)

def model(state: MessagesState):
    
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    #print("response from llm:-", response)
    if response.tool_calls:
        print("Tool calls made by the model:-", response.tool_calls)
    else:
        print("No tool calls made by the model.")
    return {"messages": [response]}


graph = StateGraph(MessagesState)
graph.add_node("agent", model)
graph.add_node("tools", ToolNode(TOOLS))

graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", tools_condition)

graph.add_edge("tools", "agent")
checkpointer = InMemorySaver()
agent_graph = graph.compile(checkpointer=checkpointer)
    

def run_agent(user_prompt:str, thread_id:str = "default_thread"):
    
    config = {
        "configurable": {"thread_id": thread_id}
    }
    
    existing_state =agent_graph.get_state(config)
    new_conversation = not existing_state.values.get("messages")
    
    messages = []
    if new_conversation:
        messages.append(SystemMessage(content=SYSTEM_INSTRUCTION))
    messages.append(HumanMessage(content=user_prompt))

    result = agent_graph.invoke({"messages": messages}, config=config)
    print("Final Result from agent_graph:-", result["messages"][-1].content)
    
    return result

USER_PROMPT = "what about tata motors?"

run_agent(USER_PROMPT, "new_conversation1")
    
    