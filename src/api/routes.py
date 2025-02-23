from flask import Blueprint, jsonify, request, Response, render_template
from ..data.storage import Storage
from ..data.queue import LogQueue
from ..facebook.auth import FacebookAuth
from ..facebook.friend import FacebookFriend
from ..facebook.scraper import FacebookScraper
from ..browser.chrome_manager import ChromeManager
import json
import os
from datetime import datetime
from functools import wraps
from flask import current_app
import time

api = Blueprint('api', __name__)
storage = Storage()
log_queue = LogQueue()
chrome_manager = ChromeManager()

@api.route('/')
def index():
    accounts = storage.load_accounts()
    return render_template('index.html', accounts=accounts)

@api.route('/get_json_files')
def get_json_files():
    """Lấy danh sách file JSON trong thư mục profiles"""
    try:
        account_id = request.args.get('account_id')
        if not account_id:
            log_queue.put("Thiếu account_id trong request", True)
            return jsonify([])
            
        account = storage.get_account(int(account_id))
        if not account:
            log_queue.put(f"Không tìm thấy tài khoản ID: {account_id}", True)
            return jsonify([])
            
        # Đảm bảo thư mục profiles tồn tại
        if not os.path.exists('profiles'):
            os.makedirs('profiles')
            log_queue.put("Đã tạo thư mục profiles", False)
            
        # Lấy danh sách file JSON từ thư mục profiles
        files = []
        for f in os.listdir('profiles'):
            if f.endswith('.json') and not f.endswith('_ids.json'):
                files.append(f)
                
        log_queue.put(f"Tìm thấy {len(files)} file JSON trong thư mục profiles", False)
        return jsonify(sorted(files, reverse=True))
        
    except Exception as e:
        log_queue.put(f"Lỗi khi lấy danh sách file: {str(e)}", True)
        return jsonify([])

@api.route('/accounts', methods=['GET'])
def get_accounts():
    accounts = storage.load_accounts()
    return jsonify([acc.to_dict() for acc in accounts])

@api.route('/accounts', methods=['POST'])
def add_account():
    data = request.json
    name = data.get('name')
    cookie = data.get('cookie')
    
    if not name or not cookie:
        return jsonify({'error': 'Missing name or cookie'}), 400
        
    # Verify cookie
    driver = chrome_manager.setup_driver()
    auth = FacebookAuth(driver)
    
    if not auth.login_with_cookies(cookie):
        driver.quit()
        return jsonify({'error': 'Invalid cookie'}), 400
        
    driver.quit()
    
    # Save account
    account = storage.add_account(name, cookie)
    return jsonify(account.to_dict())

def rate_limit(limit=5, per=60):
    def decorator(f):
        last_reset = time.time()
        calls = {}
        
        @wraps(f)
        def wrapped(*args, **kwargs):
            now = time.time()
            if now - last_reset > per:
                calls.clear()
                last_reset = now
                
            client = request.remote_addr
            calls[client] = calls.get(client, 0) + 1
            
            if calls[client] > limit:
                return jsonify({'error': 'Too many requests'}), 429
                
            return f(*args, **kwargs)
        return wrapped
    return decorator

@api.route('/accounts/<int:id>', methods=['PUT'])
@rate_limit(limit=5, per=60)
def update_account(id):
    data = request.json
    name = data.get('name', '').strip()
    cookie = data.get('cookie', '').strip()
    
    # Validation
    if not name or len(name) > 100:
        return jsonify({'error': 'Invalid name length'}), 400
        
    if not cookie or len(cookie) < 10 or len(cookie) > 10000:
        return jsonify({'error': 'Invalid cookie length'}), 400
        
    try:
        account = storage.update_account(id, name, cookie)
        if not account:
            return jsonify({'error': 'Account not found'}), 404
            
        return jsonify(account.to_dict())
    except Exception as e:
        current_app.logger.error(f"Error updating account {id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/accounts/<int:id>', methods=['DELETE'])
def delete_account(id):
    if storage.delete_account(id):
        return '', 204
    return jsonify({'error': 'Account not found'}), 404

@api.route('/scrape', methods=['POST'])
def scrape_members():
    data = request.json
    account_id = data.get('account_id')
    group_url = data.get('group_url')
    max_members = data.get('max_members', 1000)
    
    account = storage.get_account(account_id)
    if not account:
        return jsonify({'error': 'Account not found'}), 404
        
    # Setup browser
    driver = chrome_manager.setup_driver()
    auth = FacebookAuth(driver)
    
    if not auth.login_with_cookies(account.cookie):
        driver.quit()
        return jsonify({'error': 'Login failed'}), 400
        
    # Scrape members
    scraper = FacebookScraper(driver)
    members = scraper.get_group_members(group_url, max_members)
    
    # Tạo tên file dựa trên URL nhóm
    group_id = group_url.split('/')[-1].split('?')[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"profiles/group_{group_id}_{timestamp}.json"
    
    # Save to file
    scraper.save_members_to_file(members, output_file)
    log_queue.put(f"Đã lưu {len(members)} thành viên vào {os.path.basename(output_file)}", False)
    
    driver.quit()
    return jsonify({'success': True, 'members': len(members)})

@api.route('/add-friends', methods=['POST'])
def add_friends():
    try:
        data = request.json
        account_id = data.get('account_id')
        json_file = data.get('json_file')
        max_friends = data.get('max_friends', 20)
        
        account = storage.get_account(account_id)
        if not account:
            return jsonify({'error': 'Không tìm thấy tài khoản'}), 404
            
        json_file_path = f"profiles/{json_file}"
        if not os.path.exists(json_file_path):
            return jsonify({'error': f'File không tồn tại: {json_file}'}), 404
            
        # Setup browser
        driver = chrome_manager.setup_driver()
        auth = FacebookAuth(driver)
        
        try:
            log_queue.put("Đang đăng nhập...", False)
            if not auth.login_with_cookies(account.cookie):
                driver.quit()
                return jsonify({'error': 'Đăng nhập thất bại'}), 400
            
            log_queue.put("Đăng nhập thành công, bắt đầu xử lý...", False)
            
            # Add friends
            friend = FacebookFriend(driver, account.name)
            added_count = friend.add_friends_from_file(json_file_path, max_friends)
            
            return jsonify({
                'success': True,
                'added_friends': added_count,
                'message': f'Đã kết bạn thành công với {added_count} người'
            })
            
        except Exception as e:
            log_queue.put(f"Lỗi: {str(e)}", True)
            return jsonify({'error': str(e)}), 500
        finally:
            driver.quit()
            
    except Exception as e:
        return jsonify({'error': f'Lỗi server: {str(e)}'}), 500

@api.route('/stream')
def stream():
    def generate():
        while True:
            log = log_queue.get()
            if log:
                yield f"data: {json.dumps(log)}\n\n"
            else:
                yield "data: {}\n\n"
                
    return Response(generate(), mimetype='text/event-stream')

@api.route('/stop_task', methods=['POST'])
def stop_task():
    try:
        # Dừng Chrome trước
        chrome_manager.kill_chrome_processes()
        
        # Gửi thông báo tới client
        log_queue.put("Đã dừng tất cả tiến trình", False)
        
        return jsonify({
            'success': True,
            'message': 'Đã dừng thành công'
        })
    except Exception as e:
        log_queue.put(f"Lỗi khi dừng: {str(e)}", True)
        return jsonify({
            'error': str(e),
            'message': 'Không thể dừng tiến trình'
        }), 500 