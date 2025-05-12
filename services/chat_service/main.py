import uuid
import logging
import gradio as gr
import asyncio
import concurrent.futures
import time
from fastapi import FastAPI, Request, HTTPException
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
    """
    Process a message using LangGraph with no timeout.
    This function runs in a separate thread.
    
    Args:
        user_input: User's message text
        thread_id: Thread ID for conversation state
        
    Returns:
        Processed result from LangGraph
    """
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }
    
    state_input = {"messages": [HumanMessage(content=user_input)]}
    
    # Execute the graph
    result = react_graph.invoke(state_input, config)
    return result

async def simple_chatbot_response_with_timeout(user_input: str, thread_id: Optional[str] = None, timeout_seconds: int = 50) -> str:
    """
    Process a user message through the LangGraph with timeout.
    
    Args:
        user_input: User's message text
        thread_id: Optional unique identifier for the conversation thread
        timeout_seconds: Maximum time to wait for a response (default: 50 seconds)
        
    Returns:
        AI response text
    """
    # Generate thread ID if not provided
    if thread_id is None:
        thread_id = str(uuid.uuid4())
    
    logger.info(f"Processing message with timeout of {timeout_seconds}s for thread {thread_id}")
    
    # First attempt
    try:
        # Run the processing in a separate thread with a timeout
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(executor, process_message, user_input, thread_id)
        
        # Wait for completion with timeout
        start_time = time.time()
        result = await asyncio.wait_for(future, timeout=timeout_seconds)
        
        processing_time = time.time() - start_time
        logger.info(f"Message processed in {processing_time:.2f} seconds")
        
        messages = result["messages"]
        
        # Extract only final assistant response
        ai_messages = [m.content for m in messages if isinstance(m, AIMessage)]
        return ai_messages[-1] if ai_messages else "Sorry, I couldn't find a final answer."
    
    except asyncio.TimeoutError:
        logger.warning(f"Request timed out after {timeout_seconds}s. Attempting one more retry...")
        
        # Retry once more
        try:
            # Run the processing again with the same timeout
            future = loop.run_in_executor(executor, process_message, user_input, thread_id)
            result = await asyncio.wait_for(future, timeout=timeout_seconds)
            
            messages = result["messages"]
            ai_messages = [m.content for m in messages if isinstance(m, AIMessage)]
            return ai_messages[-1] if ai_messages else "Sorry, I couldn't find a final answer."
        
        except asyncio.TimeoutError:
            error_msg = f"Request timed out twice after waiting {timeout_seconds*2}s total. Please try a simpler query."
            logger.error(error_msg)
            return f"⏱️ {error_msg}"
        
        except Exception as e:
            logger.error(f"Error in retry attempt: {str(e)}")
            return f"❌ Error during retry: {str(e)}"
    
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return f"❌ Error: {str(e)}"

# Synchronous wrapper for Gradio UI
def simple_chatbot_response(user_input: str, thread_id: Optional[str] = None) -> str:
    """
    Synchronous wrapper for simple_chatbot_response_with_timeout.
    Used by Gradio interface which expects synchronous functions.
    """
    try:
        # Create a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the async function and get result
        result = loop.run_until_complete(
            simple_chatbot_response_with_timeout(user_input, thread_id)
        )
        
        # Close the loop
        loop.close()
        
        return result
    except Exception as e:
        logger.error(f"Error in synchronous wrapper: {str(e)}")
        return f"❌ Error: {str(e)}"

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    API endpoint for chat interaction.
    
    Args:
        request: Chat request with message and optional thread_id
        
    Returns:
        AI response and thread_id
    """
    # Generate thread ID if not provided
    thread_id = request.thread_id or str(uuid.uuid4())
    
    logger.info(f"Processing message for thread {thread_id}...")
    
    # Process the message through LangGraph with timeout
    response = await simple_chatbot_response_with_timeout(
        request.message, 
        thread_id=thread_id
    )
    
    return ChatResponse(message=response, thread_id=thread_id)

# Initialize LangGraph on startup - this creates our singleton instance
@app.on_event("startup")
async def startup_event():
    """Initialize resources on application startup."""
    logger.info("Initializing LangGraph instance...")
    # This initializes the graph singleton
    global react_graph
    react_graph = get_graph_instance()
    logger.info("LangGraph instance initialized successfully")

# Define Gradio interface
def create_gradio_interface():
    """
    Create and configure the Gradio web interface.
    
    Returns:
        Gradio Blocks interface
    """
    with gr.Blocks(title="E-commerce Assistant") as demo:
        gr.Markdown("## 🛍️ E-commerce Chatbot (LangGraph + Cohere)")
        
        # Add example customer ID for testing
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
        
        # Create a fixed thread ID for the entire session
        thread_id = str(uuid.uuid4())
        
        def process_input(input_text, chat_history):
            """Handle user input and update chat history."""
            if not input_text:
                return "", chat_history
                
            # Call the chat processing function with the session's thread_id
            response = simple_chatbot_response(input_text, thread_id=thread_id)
            
            # Update chat history
            chat_history.append((input_text, response))
            
            return "", chat_history
        
        def clear_history():
            """Clear the chat history."""
            return []
        
        # Connect UI components to processing function
        user_input.submit(
            process_input, 
            [user_input, chatbot], 
            [user_input, chatbot]
        )
        
        send_btn.click(
            process_input, 
            [user_input, chatbot], 
            [user_input, chatbot]
        )
        
        clear_btn.click(
            clear_history,
            [],
            [chatbot]
        )
    
    return demo

# Mount Gradio app to FastAPI
gradio_app = create_gradio_interface()
app = gr.mount_gradio_app(app, gradio_app, path="/ui")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)