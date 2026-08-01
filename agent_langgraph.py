from tools import get_price_history, get_stock_price, search_news,check_watchlist
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langchain_chroma import Chroma
import os, json, uuid
from dotenv import load_dotenv

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

TOOLS = [get_price_history, get_stock_price, search_news]
llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0.3)
llm_with_tools = llm.bind_tools(TOOLS)

SYSTEM_INSTRUCTION = (
    "You are a financial monitoring assistant. You have tools to check stock "
    "prices, price history, and news. Answer user queries based on the tools available. Be concise and "
    "cite what you found."
)

EXTRACT_INFORMATION_TEMPLATE = """
Below is one turn of a conversation with a stock \
monitoring assistant. Decide if it reveals any DURABLE fact about the user \
worth remembering for future conversations. This could include: their interests, preferences, or any other information that could help the assistant provide better answers in the future.

Do NOT extract: one-off questions, routine price checks, or anything that's 
only relevant to this single turn.

USER SAID : {user_prompt}
ASSISTANT ANSWERED : {model_response}

Extracted information should be returned only in JSON format with the following structure:
{{memories: [list of relevant information strings]}}
Return an empty list if there is no relevant information to store.
"""

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

memory_store = Chroma(
    collection_name="stock_agent_memory",
    embedding_function=embeddings,
    persist_directory="./stock_agent_memory_store"
)

def retrieve_memory(query: str, top_k: int = 3, user_id: str = "test2") -> list[str]:
    """
    Retrieve relevant memory entries based on a query.

    Args:
        query: The query string to search for in memory.
        top_k: The number of top relevant entries to return.
        user_id: The ID of the user whose memory entries to retrieve.

    Returns:
        A list of relevant memory entries.
    """
    results = memory_store.similarity_search(query, k=top_k, filter={"user_id": user_id})
    if results:
        return [result.page_content for result in results]

    return []


def memory_similarity(new_memory: str, user_id: str = "test2", threshold: float = 0.3) -> bool:
    """
    Check if a new memory entry is similar to any existing memory entries for a user.

    Args:
        new_memory: The new memory entry to check.
        user_id: The ID of the user whose memory entries to compare against.
        threshold: The similarity threshold below which two entries are considered similar.
    """
    results = memory_store.similarity_search_with_score(new_memory, k=1, filter={"user_id": user_id})
    if not results:
        return False
    matched_dod, distance = results[0]
    print(f"Similarity check: new memory '{new_memory}' vs existing memory '{matched_dod.page_content}' with distance {distance}")
    return distance < threshold


def extract_and_store_memory(user_prompt: str, model_response: str, user_id: str = "test2"):
    """
    Extracts relevant information from the model's response and stores it in memory.

    Args:
        user_id: The ID of the user for whom to store the memory.
        user_prompt: The user's prompt that led to the model's response.
        model_response: The model's response to the user's prompt.
    """
    prompt = EXTRACT_INFORMATION_TEMPLATE.format(user_prompt=user_prompt, model_response=model_response)
    response = llm.invoke(prompt)
    #print("response from memory extraction:-", response)
    raw_text = response.content[0]["text"]
    #print("Raw text from memory extraction:-", raw_text)
    raw_text = raw_text.strip("`").strip("json").strip()
    parsed_text = json.loads(raw_text)
    memories = parsed_text.get("memories", [])
    if memories:
        new_memories = [new_memory for new_memory in memories if not memory_similarity(new_memory, user_id)]
        
        if new_memories:
            memory_store.add_texts(
                texts = new_memories,
                metadatas = [{"user_id": user_id} for _ in new_memories],
                ids = [str(uuid.uuid4()) for _ in new_memories]
            )
            
            for memory in new_memories:
                print(f"Stored memory for user {user_id}: {memory}")
        else:
            print(f"No new relevant memories to store for user {user_id}.")
    else:
        print(f"No relevant memories extracted for user {user_id}.")
        

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
    

def run_agent(user_prompt:str, thread_id:str = "default_thread", user_id:str = "test2"):
    
    config = {
        "configurable": {"thread_id": thread_id}
    }
    
    existing_state =agent_graph.get_state(config)
    new_conversation = not existing_state.values.get("messages")
    
    retrieved_memory = retrieve_memory(user_prompt, user_id=user_id)
    messages = []
    
    if retrieved_memory:
        memory_context = "Relevant context remembered about this user from past conversations:\n"    
        memory_context += "\n".join(
            f"- {memory}" for memory in retrieved_memory
        )
        print("Memory context retrieved for user:", memory_context)
    else:
        memory_context = ""
        print("No relevant memory context found for user.")
        
    if new_conversation:
        messages.append(SystemMessage(content=SYSTEM_INSTRUCTION))
    messages.append(HumanMessage(content=user_prompt + memory_context))

    result = agent_graph.invoke({"messages": messages}, config=config)
    print("Final Result from agent_graph:-", result["messages"][-1].content)
    
    extract_and_store_memory(user_prompt, result["messages"][-1].content, user_id)
    
    return result

USER_PROMPT = "I've also started keeping an eye on IT sector stocks recently, in addition to my usual picks."

run_agent(USER_PROMPT, user_id="test5")
    