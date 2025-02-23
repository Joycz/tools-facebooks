from flask import Flask
from src.api.routes import api
import os
import signal
import sys
from src.browser.chrome_manager import ChromeManager

app = Flask(__name__, 
           static_folder='templates',
           static_url_path='/static')
           
app.secret_key = 'your-secret-key-here'
app.register_blueprint(api)

chrome_manager = ChromeManager()

def signal_handler(sig, frame):
    print("\nShutting down...")
    chrome_manager.kill_chrome_processes()
    sys.exit(0)
    
signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    # Create required directories
    os.makedirs("profiles", exist_ok=True)
    
    print("\n=== Facebook Tools ===")
    print("✓ Server running at http://127.0.0.1:5000")
    print("✓ Press Ctrl+C to stop")
    print("="*22 + "\n")
    
    app.run(debug=True) 