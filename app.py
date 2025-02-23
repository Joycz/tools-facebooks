from flask import Flask
from src.api.routes import api
import os
import signal
import sys
from src.browser.chrome_manager import ChromeManager

app = Flask(__name__, 
           static_folder='static',
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
    # Tạo cấu trúc thư mục cần thiết
    required_dirs = [
        "data",           # Lưu dữ liệu tài khoản
        "static/css",     # CSS files
        "static/js",      # JavaScript files
        "profiles",       # Lưu file JSON từ việc scrape group
    ]
    
    for dir_path in required_dirs:
        os.makedirs(dir_path, exist_ok=True)
        
    # Di chuyển dữ liệu từ profiles sang data nếu cần
    if os.path.exists('profiles'):
        print("✓ Di chuyển dữ liệu từ profiles sang data...")
    
    print("\n=== Facebook Tools ===")
    print("✓ Server running at http://127.0.0.1:5000")
    print("✓ Press Ctrl+C to stop")
    print("="*22 + "\n")
    
    app.run(debug=True) 