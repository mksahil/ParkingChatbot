# AI-Powered Parking Slot Search and Booking System

This project implements an agentic AI system for searching and booking parking slots. Users can interact with the system via a conversational interface to find parking based on vehicle type, location, slot type, and duration. The system uses a Large Language Model (LLM) for natural language understanding and task execution, a vector database (Milvus) for conversational memory, and a FastAPI backend with SQLite for parking data management.

## SnapShots
![image](https://github.com/user-attachments/assets/3600311f-dab6-47e2-8f79-b13da1048247)

![image](https://github.com/user-attachments/assets/07a65d19-029a-4cee-9b7b-ff6cb0086a3b)


## Features

*   **Conversational AI:** Interact with an AI agent to find and book parking.
*   **Parking Search:** Search for available spots based on:
    *   Vehicle Type (e.g., car, two-wheeler, SUV)
    *   Location (e.g., downtown, airport, mall)
    *   Slot Type (e.g., covered, open)
*   **Automated Booking:** Book available parking spots directly through the agent.
*   **Input Validation:** LLM-assisted validation of user inputs.
*   **Conversational Memory:** Uses Milvus to remember past interactions and preferences, reducing repetitive questions.
*   **UI Interface:** Streamlit-based chat interface to display conversation history, search results, and booking confirmations.
*   **Backend Services:** FastAPI backend for managing parking spots and bookings, with data stored in SQLite.

## Technology Stack

*   **Orchestration:** LangChain
*   **LLM:** Llama 3 (or other Ollama-supported models) via Ollama
*   **Backend API:** FastAPI
*   **Relational Database:** SQLite
*   **Vector Database (Memory):** Milvus
*   **UI Framework:** Streamlit
*   **Embeddings:** Sentence-Transformers (`all-MiniLM-L6-v2`)


## Prerequisites

Before you begin, ensure you have the following installed:

1.  **Python:** Version 3.9 or higher.
2.  **Pip:** Python package installer.
3.  **Docker and Docker Compose:** For running Milvus.
4.  **Ollama:** For running the Llama LLM locally.
    *   Download from [ollama.com](https://ollama.com/).
    *   After installation, pull the Llama 3.2 model (or your preferred model):
        ```bash
        ollama pull llama3.2 
        ```

## Setup Instructions

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/mksahil/-Parking-Slot-Search-and-Booking.git
    cd parking_agent_system
    ```

2.  **Set up Python Virtual Environment:**
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

3.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Milvus: The easiest way is using Docker:**
   ```bash
wget https://github.com/milvus-io/milvus/releases/download/v2.3.1/milvus-standalone-docker-compose.yml -O docker-compose.yml
```
Navigate to the project root directory (where `docker-compose.yml` is located) and run:
```bash
    docker-compose up -d
```
This will start a standalone Milvus instance. Wait a minute or two for Milvus to be fully operational. You can check logs using `docker-compose logs -f milvus-standalone`.

6.  **Ensure Ollama is Running:**
    Start the Ollama application if it's not already running. It typically runs a server on `http://localhost:11434`.

7.  **Environment Variables (Optional but Recommended):**
    You can create a `.env` file in the project root directory to configure Milvus connection details if they differ from the defaults:
    ```env
    # .env file
    MILVUS_HOST=localhost
    MILVUS_PORT=19530
    ```
    The application will use these if set, otherwise defaults to localhost:19530.

## Running the Application

The system consists of two main components that need to be run: the FastAPI backend and the Streamlit UI.

1.  **Start the FastAPI Backend:**
    Open a new terminal, activate the virtual environment, and run:
    ```bash
    python -m parking_agent_system.main_api
    ```
    The backend API will be available at `http://localhost:8000`. You can access the API documentation (Swagger UI) at `http://localhost:8000/docs`.
    On the first run, it will create `parking_data.db` and populate it with some initial parking spots.

2.  **Start the Streamlit UI:**
    Open another new terminal, activate the virtual environment, and run:
    ```bash
    streamlit run app_ui.py
    ```
    The UI will be accessible in your web browser, typically at `http://localhost:8501`.

## How to Use

1.  Open the Streamlit UI in your browser (`http://localhost:8501`).
2.  The AI agent will greet you.
3.  Type your parking requests into the chat input, for example:
    *   "Hello, I need parking."
    *   "Find a parking spot for my car downtown."
    *   "I want to park my two-wheeler near the mall."
    *   (After search results) "Book spot ID 1 for today from 2 PM to 4 PM."
4.  The agent will ask for any missing information and use its tools to search for spots or make bookings.
5.  Conversation history, search results, and booking confirmations will be displayed in the UI.

## Development Notes

*   **LLM Model:** The `agent_logic.py` file is configured to use `llama3` by default. If you wish to use a different Ollama model, change the `LLM_MODEL` variable in that file and ensure the model is pulled via `ollama pull <model_name>`.
*   **SQLite Database:** The `parking_data.db` file stores parking spots and bookings. You can use a SQLite browser to inspect its contents.
*   **Milvus Data:** Conversation history is stored in Milvus. Data will persist as long as the Milvus Docker volume is not deleted.
*   **Resetting Parking Availability:** The Streamlit UI has an "Admin Panel" in the sidebar with a button to reset all parking spot availability and clear bookings. This is useful for testing.

---
