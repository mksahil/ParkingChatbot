# app_ui.py

import agent_logic # Assuming your project structure allows this import
                                  # e.g. parking_agent_system is a package
                                  # or files are in the same directory.
import json
import milvus_utils # Assuming this is a utility for Milvus DB interactions
import os
os.environ["STREAMLIT_SERVER_ENABLE_FILE_WATCHER"] = "false"
import torch
torch.classes.__path__ = [] 

import streamlit as st


st.set_page_config(page_title="Parking Assistant", layout="wide")

st.title("🚗 Smart Parking Assistant")
st.caption("Your AI-powered helper for finding and booking parking slots.")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you with your parking needs today?"}]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Try to pretty-print JSON if content looks like it
        content = message["content"]
        try:
            # A simple check to see if it might be JSON (starts with { or [)
            if isinstance(content, str) and (content.strip().startswith("{") or content.strip().startswith("[")):
                data = json.loads(content)
                st.json(data) # Streamlit's JSON renderer
            # Check for specific keywords that indicate structured data from tools
            elif "Found parking spots:" in content or "Booking successful! Details:" in content:
                # Extract the JSON part
                try:
                    json_str = content.split(":", 1)[1].strip()
                    data = json.loads(json_str)
                    st.markdown(content.split(":", 1)[0] + ":") # Print the prefix
                    st.json(data)
                except (IndexError, json.JSONDecodeError):
                    st.markdown(content) # Fallback to markdown
            else:
                st.markdown(content)
        except json.JSONDecodeError:
            st.markdown(content) # Fallback if not valid JSON

# User input
if prompt := st.chat_input("What can I do for you? (e.g., 'Find parking for my car downtown')"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        try:
            # Pass the current session's chat history to the agent
            # The agent_logic needs to handle this format or convert it.
            assistant_response = agent_logic.process_user_query(prompt, st.session_state.messages)
            message_placeholder.markdown(assistant_response) # Display final response
        except Exception as e:
            st.error(f"An error occurred: {e}")
            assistant_response = "Sorry, I encountered an internal error. Please try again."
            message_placeholder.markdown(assistant_response)


    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})

# Sidebar for admin actions (optional)
with st.sidebar:
    st.header("Admin Panel")
    if st.button("Reset Parking Availability (Debug)"):
        try:
            import requests
            response = requests.post(f"{agent_logic.FASTAPI_BASE_URL}/admin/reset-availability")
            if response.status_code == 200:
                st.success("Parking availability reset successfully!")
            else:
                st.error(f"Failed to reset: {response.text}")
        except Exception as e:
            st.error(f"Error connecting to API: {e}")

    st.markdown("---")
    st.markdown("Debug Info:")
    st.write(f"Using LLM: {agent_logic.LLM_MODEL}")
    st.write(f"Milvus Collection: {milvus_utils.COLLECTION_NAME}")