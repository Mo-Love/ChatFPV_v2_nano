import argparse
import os
import sys
import time
import requests
from pathlib import Path
from typing import List, Dict, Any

# Add the project root to the path so we can import nanochat
sys.path.insert(0, str(Path(__file__).parent.parent))

from nanochat.chat import Chat
from nanochat.models import ModelManager
from nanochat.utils import load_config, save_config

def main():
    parser = argparse.ArgumentParser(description="NanoChat Web Interface")
    parser.add_argument("--model", type=str, default="gpt2", help="Model to use (e.g., gpt2, gpt2-medium)")
    parser.add_argument("--device", type=str, default="cpu", help="Device to run on (cpu or cuda)")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the web server on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind the web server to")
    parser.add_argument("--config", type=str, default="config.json", help="Path to config file")
    parser.add_argument("--no-stream", action="store_true", help="Disable streaming responses")
    parser.add_argument("--temperature", type=float, default=0.7, help="Sampling temperature")
    parser.add_argument("--top_p", type=float, default=0.9, help="Top-p sampling")
    parser.add_argument("--max_length", type=int, default=512, help="Maximum response length")
    parser.add_argument("--system_prompt", type=str, default="You are a helpful AI assistant.", help="System prompt")
    parser.add_argument("--chat_file", type=str, default="chat_history.json", help="File to save chat history")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Initialize model manager
    model_manager = ModelManager()
    model = model_manager.load_model(args.model, device=args.device)
    
    # Initialize chat
    chat = Chat(
        model=model,
        system_prompt=args.system_prompt,
        temperature=args.temperature,
        top_p=args.top_p,
        max_length=args.max_length,
        chat_file=args.chat_file
    )
    
    # Start web server
    from flask import Flask, render_template, request, jsonify
    import threading
    
    app = Flask(__name__)
    
    @app.route("/")
    def index():
        return render_template("index.html")
    
    @app.route("/chat", methods=["POST"])
    def chat_endpoint():
        user_input = request.json.get("message", "")
        if not user_input.strip():
            return jsonify({"error": "Empty message"}), 400
        
        try:
            response = chat.generate_response(user_input, stream=not args.no_stream)
            return jsonify({"response": response})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    def run_server():
        app.run(host=args.host, port=args.port, threaded=True)
    
    # Start the server in a separate thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    print(f"Web server running at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        chat.save_chat()
        sys.exit(0)

if __name__ == "__main__":
    main()
