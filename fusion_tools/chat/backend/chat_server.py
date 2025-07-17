#!/usr/bin/env python3
"""
Chat Server Backend
FastAPI server for chat interface with hybrid fusion models
"""

import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import json
import asyncio

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from utils.api_client import FusionAPIClient
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    """Chat message data structure"""
    id: str
    user_message: str
    bot_response: str
    model_used: str
    timestamp: str
    response_time: float

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    model: Optional[str] = None
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    model_used: str
    conversation_id: str
    timestamp: str
    response_time: float

class ChatHistory(BaseModel):
    """Chat history model"""
    conversation_id: str
    messages: List[Dict]
    created_at: str
    last_updated: str

class ChatServer:
    """Chat server with fusion model integration"""
    
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.get_fusion_config()
        self.chat_config = self.config.chat
        
        self.api_client = FusionAPIClient(
            host=self.config.host,
            port=self.config.port,
            timeout=self.config.timeout
        )
        
        self.conversations: Dict[str, ChatHistory] = {}
        self.active_websockets: List[WebSocket] = []
        
        # Setup FastAPI app
        self.app = FastAPI(
            title="Fusion Chat Server",
            description="Chat interface for hybrid fusion models",
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Mount static files (for frontend)
        frontend_path = os.path.join(os.path.dirname(__file__), "../frontend")
        if os.path.exists(frontend_path):
            self.app.mount("/static", StaticFiles(directory=frontend_path), name="static")
        
        self.setup_routes()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/")
        async def root():
            """Serve main chat interface"""
            frontend_path = os.path.join(os.path.dirname(__file__), "../frontend/index.html")
            if os.path.exists(frontend_path):
                return FileResponse(frontend_path)
            return {"message": "Chat Server", "status": "running"}
        
        @self.app.post("/chat", response_model=ChatResponse)
        async def chat(request: ChatRequest):
            """Main chat endpoint"""
            try:
                start_time = datetime.now()
                
                # Validate message length
                max_length = self.chat_config.get('max_message_length', 4096)
                if len(request.message) > max_length:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Message too long. Max length: {max_length}"
                    )
                
                # Determine model to use
                model_name = request.model or self.chat_config.get('default_model', 'hybrid-fusion-v1')
                
                # Get response from fusion server
                response = self.api_client.chat_with_model(model_name, request.message)
                
                if response is None:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to get response from fusion server"
                    )
                
                # Calculate response time
                response_time = (datetime.now() - start_time).total_seconds()
                
                # Create conversation ID if not provided
                conversation_id = request.conversation_id or f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Store in conversation history
                if self.chat_config.get('enable_history', True):
                    self.store_message(conversation_id, request.message, response, model_name, response_time)
                
                # Broadcast to websockets
                await self.broadcast_message({
                    "type": "chat_response",
                    "conversation_id": conversation_id,
                    "user_message": request.message,
                    "bot_response": response,
                    "model_used": model_name,
                    "response_time": response_time
                })
                
                return ChatResponse(
                    response=response,
                    model_used=model_name,
                    conversation_id=conversation_id,
                    timestamp=datetime.now().isoformat(),
                    response_time=response_time
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Chat error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/models")
        async def get_available_models():
            """Get available models"""
            try:
                models = self.api_client.get_available_models()
                hybrids = self.api_client.get_hybrid_models()
                
                hybrid_names = [h.get('name', 'unknown') for h in hybrids]
                
                return {
                    "standard_models": models,
                    "hybrid_models": hybrid_names,
                    "default_model": self.chat_config.get('default_model', 'hybrid-fusion-v1')
                }
            except Exception as e:
                logger.error(f"Failed to get models: {e}")
                return {"standard_models": [], "hybrid_models": [], "default_model": "hybrid-fusion-v1"}
        
        @self.app.get("/conversations")
        async def get_conversations():
            """Get conversation list"""
            return {
                "conversations": [
                    {
                        "id": conv_id,
                        "message_count": len(history.messages),
                        "created_at": history.created_at,
                        "last_updated": history.last_updated
                    }
                    for conv_id, history in self.conversations.items()
                ]
            }
        
        @self.app.get("/conversations/{conversation_id}")
        async def get_conversation(conversation_id: str):
            """Get specific conversation"""
            if conversation_id not in self.conversations:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            return self.conversations[conversation_id]
        
        @self.app.delete("/conversations/{conversation_id}")
        async def delete_conversation(conversation_id: str):
            """Delete conversation"""
            if conversation_id not in self.conversations:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            del self.conversations[conversation_id]
            return {"message": "Conversation deleted"}
        
        @self.app.get("/status")
        async def get_chat_status():
            """Get chat server status"""
            fusion_status = self.api_client.get_fusion_status()
            server_health = self.api_client.get_server_health()
            
            return {
                "chat_server_status": "running",
                "fusion_server_connected": fusion_status is not None,
                "fusion_server_health": server_health.get('status', 'unknown'),
                "active_conversations": len(self.conversations),
                "active_websockets": len(self.active_websockets),
                "default_model": self.chat_config.get('default_model', 'hybrid-fusion-v1'),
                "config": {
                    "max_message_length": self.chat_config.get('max_message_length', 4096),
                    "response_timeout": self.chat_config.get('response_timeout', 60),
                    "history_enabled": self.chat_config.get('enable_history', True)
                }
            }
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time chat"""
            await websocket.accept()
            self.active_websockets.append(websocket)
            
            try:
                while True:
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    # Handle different message types
                    if message_data.get("type") == "chat":
                        # Process chat message
                        try:
                            request = ChatRequest(
                                message=message_data.get("message", ""),
                                model=message_data.get("model"),
                                conversation_id=message_data.get("conversation_id")
                            )
                            
                            # Get response (reuse logic from chat endpoint)
                            start_time = datetime.now()
                            model_name = request.model or self.chat_config.get('default_model', 'hybrid-fusion-v1')
                            
                            response = self.api_client.chat_with_model(model_name, request.message)
                            response_time = (datetime.now() - start_time).total_seconds()
                            
                            # Send response back
                            await websocket.send_text(json.dumps({
                                "type": "chat_response",
                                "response": response,
                                "model_used": model_name,
                                "response_time": response_time,
                                "timestamp": datetime.now().isoformat()
                            }))
                            
                        except Exception as e:
                            await websocket.send_text(json.dumps({
                                "type": "error",
                                "message": str(e)
                            }))
                    
            except WebSocketDisconnect:
                self.active_websockets.remove(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if websocket in self.active_websockets:
                    self.active_websockets.remove(websocket)
    
    def store_message(self, conversation_id: str, user_message: str, bot_response: str, 
                     model_used: str, response_time: float):
        """Store message in conversation history"""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = ChatHistory(
                conversation_id=conversation_id,
                messages=[],
                created_at=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat()
            )
        
        # Add message to history
        message = {
            "id": f"msg_{len(self.conversations[conversation_id].messages) + 1}",
            "user_message": user_message,
            "bot_response": bot_response,
            "model_used": model_used,
            "timestamp": datetime.now().isoformat(),
            "response_time": response_time
        }
        
        self.conversations[conversation_id].messages.append(message)
        self.conversations[conversation_id].last_updated = datetime.now().isoformat()
        
        # Limit history size
        max_history = self.chat_config.get('max_history_size', 100)
        if len(self.conversations[conversation_id].messages) > max_history:
            self.conversations[conversation_id].messages = self.conversations[conversation_id].messages[-max_history:]
    
    async def broadcast_message(self, message: Dict):
        """Broadcast message to all connected websockets"""
        if self.active_websockets:
            message_str = json.dumps(message)
            for websocket in self.active_websockets[:]:  # Copy list to avoid modification during iteration
                try:
                    await websocket.send_text(message_str)
                except Exception as e:
                    logger.error(f"Failed to send websocket message: {e}")
                    if websocket in self.active_websockets:
                        self.active_websockets.remove(websocket)
    
    def run(self, host: str = "0.0.0.0", port: int = 8001):
        """Run the chat server"""
        logger.info(f"🚀 Starting chat server on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fusion Chat Server")
    parser.add_argument('--host', default='0.0.0.0', help='Host address')
    parser.add_argument('--port', type=int, default=8001, help='Port number')
    
    args = parser.parse_args()
    
    server = ChatServer()
    server.run(host=args.host, port=args.port)

if __name__ == "__main__":
    main() 