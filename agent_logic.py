# agent_logic.py
import json
import requests
from datetime import datetime, timedelta
from typing import Type, Dict, Any, List
from langchain_community.llms import Ollama
from langchain.agents import AgentExecutor, create_openai_tools_agent 
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import BaseTool, tool
from langchain_core.pydantic_v1 import BaseModel, Field 
from langchain.memory import ConversationBufferWindowMemory
from langchain_community.chat_message_histories import ZepChatMessageHistory 
import milvus_utils 
from langchain_openai import AzureChatOpenAI


# --- Configuration ---
LLM_MODEL = "llama3.2" # Ensure this model is pulled in Ollama
FASTAPI_BASE_URL = "http://localhost:8000"
USER_ID_FOR_MEMORY = "test_user_123"
from langchain_community.chat_models import ChatOllama
# --- Initialize LLM ---
llm = ChatOllama(model=LLM_MODEL, temperature=0.1)


# --- Define Pydantic Schemas for Tool Inputs ---
class ParkingSearchInput(BaseModel):
    vehicle_type: str = Field(description="Type of vehicle, e.g., 'car', 'two-wheeler', 'suv'.")
    location: str = Field(description="Desired parking location, e.g., 'downtown', 'airport', 'mall'.")
    slot_type: str = Field(description="Preferred type of parking slot, e.g., 'covered', 'open', 'compact'. Optional.", default=None)
    # date: str = Field(description="Date for parking, e.g., 'today', 'tomorrow', '2024-07-28'. Optional.", default=None)
    # duration: str = Field(description="Parking duration, e.g., '2 hours', 'full day'. Optional.", default=None)

class ParkingBookingInput(BaseModel):
    spot_id: int = Field(description="The ID of the parking spot to book, obtained from search results.")
    vehicle_type: str = Field(description="User's vehicle type for confirmation.")
    # location: str = Field(description="Location of the spot (for confirmation).")
    # slot_type: str = Field(description="Slot type of the spot (for confirmation).")
    start_datetime_str: str = Field(description="Start date and time for parking in 'YYYY-MM-DD HH:MM' format. e.g. '2024-07-28 14:00'")
    end_datetime_str: str = Field(description="End date and time for parking in 'YYYY-MM-DD HH:MM' format. e.g. '2024-07-28 16:00'")


# --- Define Tools for the Agent ---
@tool("search_parking_spots", args_schema=ParkingSearchInput, return_direct=False)
def search_parking_spots_tool(vehicle_type: str, location: str, slot_type: str = None) -> str:
    """
    Searches for available parking spots based on vehicle type, location, and optionally slot type.
    Returns a list of available spots or a message if none are found.
    """
    payload = {
        "vehicle_type": vehicle_type,
        "location": location,
        "slot_type": slot_type,
    }
    try:
        response = requests.post(f"{FASTAPI_BASE_URL}/get-parking-spots", json=payload)
        response.raise_for_status() # Raise an exception for HTTP errors
        spots = response.json()
        if not spots:
            return "No parking spots found matching your criteria. Try different options?"
        return f"Found parking spots: {json.dumps(spots)}"
    except requests.exceptions.RequestException as e:
        return f"API Error during search: {str(e)}. The parking service might be down."
    except json.JSONDecodeError:
        return "API Error: Could not parse response from parking service."

@tool("book_parking_spot", args_schema=ParkingBookingInput, return_direct=False)
def book_parking_spot_tool(spot_id: int, vehicle_type: str, start_datetime_str: str, end_datetime_str: str) -> str:
    """
    Books a specific parking spot ID for a given vehicle type and duration (start and end time).
    Requires spot_id from search results, vehicle type, start time, and end time.
    Start and end time must be in 'YYYY-MM-DD HH:MM' format.
    """
    try:
        # Convert string datetimes to datetime objects
        start_time = datetime.strptime(start_datetime_str, '%Y-%m-%d %H:%M')
        end_time = datetime.strptime(end_datetime_str, '%Y-%m-%d %H:%M')
    except ValueError:
        return "Invalid datetime format. Please use 'YYYY-MM-DD HH:MM'. For example, '2024-07-28 14:00'."

    # The API schema expects `slot_type` and `location` which we don't explicitly ask the user for booking
    # as they are inherent to the `spot_id`.
    # We will need to fetch spot details first or modify the tool/API.
    # For now, we'll assume the API can derive location/slot_type from spot_id or it's passed implicitly.
    # A better approach: The booking request in FastAPI should fetch spot details using spot_id. (DONE in FastAPI part)

    payload = {
        "spot_id": spot_id,
        "vehicle_type": vehicle_type,
        "start_time": start_time.isoformat(), # FastAPI will parse this
        "end_time": end_time.isoformat()
    }
    try:
        print(f"Booking payload: {payload}") # For debugging    
        response = requests.post(f"{FASTAPI_BASE_URL}/book-parking", json=payload)
        print(f"Booking response: {response.text}") # For debugging 
        response.raise_for_status()
        booking_details = response.json()
        return f"Booking successful! Details: {json.dumps(booking_details)}"
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return "Booking Error: Parking spot not found."
        elif e.response.status_code == 400:
            error_detail = e.response.json().get("detail", "Spot not available or invalid request.")
            return f"Booking Error: {error_detail}"
        return f"API Error during booking: {str(e)}"
    except requests.exceptions.RequestException as e:
        return f"API Error during booking: {str(e)}. The parking service might be down."
    except json.JSONDecodeError:
        return "API Error: Could not parse response from parking service."

tools = [search_parking_spots_tool, book_parking_spot_tool]

def get_agent_prompt_template(retrieved_memory_str: str = ""):
    memory_guidance = ""
    if retrieved_memory_str:
        memory_guidance = (
            f"Here's some relevant information from past conversations with this user:\n"
            f"{retrieved_memory_str}\n"
            f"Use this to pre-fill information or confirm preferences if appropriate. "
            f"Don't assume, always confirm if you are using past info.\n"
        )

    system_prompt = f"""
    You are a helpful AI parking assistant. Your goal is to help users find and book parking spots.
    Be friendly and conversational.

    Follow these steps:
    1. Greet the user and ask how you can help.
    2. Determine if the user wants to SEARCH for parking or BOOK a parking spot.
    3. **For SEARCHING:**
       - You NEED `vehicle_type`, `location`. `slot_type` is optional.
       - If any of these are missing from the user's query, ask for them one by one.
       - Example: "Sure, I can help you find a parking spot. What type of vehicle do you have?" or "And where are you looking to park?"
       - Once you have `vehicle_type` and `location`, use the `search_parking_spots_tool`.
    4. **For BOOKING:**
       - The user usually wants to book after a search. They will mention a `spot_id` from the search results.
       - You NEED `spot_id`, `vehicle_type` (confirm from user or search context), `start_datetime_str`, and `end_datetime_str`.
       - Ask for the date and time for parking. "When would you like to park? Please provide the start and end date and time (e.g., 'Today from 2 PM to 4 PM' or '2024-07-28 14:00 to 2024-07-28 16:00')."
       - Convert natural language times (like "today at 2 PM") to 'YYYY-MM-DD HH:MM' format before calling the tool. Assume 'today' if only time is given.
       - Once you have all booking details, use the `book_parking_spot_tool`.
    5. **Input Validation:**
       - Before calling any tool, double-check if you have ALL required parameters for that tool.
       - The LLM (you) must be responsible for extracting and validating the *presence* of information. The tools will validate the *values*.
       - If information is insufficient, ask the user for what's missing.
    6. **Memory Usage:**
       {memory_guidance}
    7. **Tool Usage:**
       - Only use tools when you have confirmed all necessary information for the action.
       - Provide the tool's output back to the user clearly.
    8. **Clarification:** If the user's request is ambiguous, ask for clarification.

    Current date and time is: {datetime.now().strftime('%Y-%m-%d %H:%M')}

    Remember your available tools:
    - `search_parking_spots_tool`: for finding spots.
    - `book_parking_spot_tool`: for making a booking.

    Always respond in a friendly, conversational manner.
    If a search returns no spots, inform the user and maybe suggest trying different criteria.
    If a booking fails, explain why based on the tool's message.
    """
    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

# --- Agent and Memory ---
# `ConversationBufferWindowMemory` is for the agent's short-term context.
chat_history_for_agent = []

# Main function to process user input
def process_user_query(user_query: str, current_chat_history: List[Dict[str,str]]) -> str:
    """
    Processes a user query using the agent.
    `current_chat_history` is for the UI, format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    """
    global chat_history_for_agent

    # 1. Store user query to Milvus
    milvus_utils.store_conversation_turn(
        user_query,
        {"user_id": USER_ID_FOR_MEMORY, "role": "user", "timestamp": datetime.utcnow().isoformat()}
    )

    # 2. Retrieve relevant history from Milvus
    relevant_milvus_history = milvus_utils.retrieve_relevant_history(user_query, USER_ID_FOR_MEMORY, top_k=3)
    retrieved_memory_str = "\n".join([f"- {item['text']} (from a past conversation)" for item in relevant_milvus_history])


    # 3. Create/Update Agent
    prompt = get_agent_prompt_template(retrieved_memory_str)
    agent = create_openai_tools_agent(llm, tools, prompt) 
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    from langchain_core.messages import HumanMessage, AIMessage
    langchain_formatted_history = []
    for msg in current_chat_history: 
        if msg["role"] == "user":
            langchain_formatted_history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            langchain_formatted_history.append(AIMessage(content=msg["content"]))


    # 4. Invoke Agent
    response = agent_executor.invoke({
        "input": user_query,
        "chat_history": langchain_formatted_history
    })
    assistant_response = response.get("output", "Sorry, I encountered an issue.")

    # 5. Store assistant response to Milvus
    milvus_utils.store_conversation_turn(
        assistant_response,
        {"user_id": USER_ID_FOR_MEMORY, "role": "assistant", "timestamp": datetime.utcnow().isoformat()}
    )

    return assistant_response

# Initialize Milvus collection on startup
milvus_utils.create_milvus_collection_if_not_exists()