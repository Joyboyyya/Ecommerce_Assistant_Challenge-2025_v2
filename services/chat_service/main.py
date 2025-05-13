import uuid
import logging
import gradio as gr
import asyncio
import concurrent.futures
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage

from graph import get_graph_instance

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="E-commerce Chatbot Service",
    description="Chat interface for e-commerce customer support",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define API models
class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    thread_id: str

# Get the LangGraph instance
react_graph = get_graph_instance()

# ThreadPoolExecutor for running tasks with timeouts
executor = concurrent.futures.ThreadPoolExecutor()

@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "E-commerce Chatbot Service API", "status": "running"}

def process_message(user_input: str, thread_id: str):
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }
    state_input = {"messages": [HumanMessage(content=user_input)]}
    result = react_graph.invoke(state_input, config)
    return result

async def simple_chatbot_response_with_timeout_parallel(user_input: str, thread_id: Optional[str] = None, timeout_seconds: int = 50) -> str:
    """
    Run 3 parallel LangGraph invocations and return the result of the first to complete.

    Args:
        user_input: The user's message
        thread_id: Optional conversation thread ID
        timeout_seconds: Maximum wait time for each individual task

    Returns:
        The first successful AI response
    """
    if thread_id is None:
        thread_id = str(uuid.uuid4())

    logger.info(f"Starting 3 parallel tasks for thread {thread_id}")

    async def wrapped_in_executor(task_id: int):
        loop = asyncio.get_event_loop()
        try:
            result = await asyncio.wait_for(loop.run_in_executor(executor, process_message, user_input, thread_id), timeout=timeout_seconds)
            messages = result["messages"]
            ai_messages = [m.content for m in messages if isinstance(m, AIMessage)]
            response = ai_messages[-1] if ai_messages else "No final answer found."
            logger.info(f"✅ Task {task_id} completed successfully.")
            return response
        except Exception as e:
            logger.warning(f"❌ Task {task_id} failed: {e}")
            return None

    # Wrap coroutines in tasks
    tasks = [asyncio.create_task(wrapped_in_executor(i)) for i in range(2)]
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    for task in pending:
        task.cancel()

    for task in done:
        result = task.result()
        if result:
            return result

    return "⚠️ All attempts failed or timed out. Please try again later."


def simple_chatbot_response(user_input: str, thread_id: Optional[str] = None) -> str:
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            simple_chatbot_response_with_timeout_parallel(user_input, thread_id)
        )
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Error in synchronous wrapper: {str(e)}")
        return f"❌ Error: {str(e)}"

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    thread_id = request.thread_id or str(uuid.uuid4())
    logger.info(f"Processing message for thread {thread_id}...")
    response = await simple_chatbot_response_with_timeout_parallel(
        request.message,
        thread_id=thread_id
    )
    return ChatResponse(message=response, thread_id=thread_id)

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing LangGraph instance...")
    global react_graph
    react_graph = get_graph_instance()
    logger.info("LangGraph instance initialized successfully")

def create_gradio_interface():
    with gr.Blocks(title="E-commerce Assistant") as demo:
        gr.Markdown("## 🛍️ E-commerce Chatbot (LangGraph + Cohere)")
        gr.Markdown("""
        ℹ️ **Try these examples:**
        - "What are the top-rated guitar products?"
        - "Show me guitar strings with good ratings"
        - "What was my last order?" (Customer ID: 37077)
        - "Do I have any orders for car products?" (Customer ID: 37077)
        """)
        chatbot = gr.Chatbot()
        user_input = gr.Textbox(placeholder="Ask something like 'What's my last order?'")
        send_btn = gr.Button("Send")
        clear_btn = gr.Button("Clear")
        thread_id = str(uuid.uuid4())

        def process_input(input_text, chat_history):
            if not input_text:
                return "", chat_history
            response = simple_chatbot_response(input_text, thread_id=thread_id)
            chat_history.append((input_text, response))
            return "", chat_history

        def clear_history():
            return []

        user_input.submit(process_input, [user_input, chatbot], [user_input, chatbot])
        send_btn.click(process_input, [user_input, chatbot], [user_input, chatbot])
        clear_btn.click(clear_history, [], [chatbot])

    return demo

gradio_app = create_gradio_interface()
app = gr.mount_gradio_app(app, gradio_app, path="/ui")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
