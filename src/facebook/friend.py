from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from typing import Optional
import json
import os
import shutil
import msvcrt
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class SafeFileHandler:
    def __init__(self, filename):
        self.filename = filename
        self.lock_file = f"{filename}.lock"
        self.file_handle = None
        
    def __enter__(self):
        start_time = time.time()
        while time.time() - start_time < 10:
            try:
                self.file_handle = open(self.lock_file, 'wb+')
                msvcrt.locking(self.file_handle.fileno(), msvcrt.LK_NBLCK, 1)
                return self
            except IOError:
                time.sleep(0.1)
        raise IOError("Không thể acquire lock sau 10 giây")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file_handle:
            try:
                msvcrt.locking(self.file_handle.fileno(), msvcrt.LK_UNLCK, 1)
            except:
                pass
            self.file_handle.close()
            try:
                os.remove(self.lock_file)
            except:
                pass

    def read(self):
        try:
            if not os.path.exists(self.filename):
                return None
                
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            backup_file = f"{self.filename}.bak"
            if os.path.exists(backup_file):
                shutil.copy2(backup_file, self.filename)
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
            
    def write(self, data):
        if os.path.exists(self.filename):
            shutil.copy2(self.filename, f"{self.filename}.bak")
            
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

class FacebookFriend:
    def __init__(self, driver: webdriver.Chrome, account_name: str):
        self.driver = driver
        self.account_name = account_name
        self.account_data_dir = f"data/{account_name}"
        self.processed_ids_file = f"{self.account_data_dir}/processed_ids.json"
        self.unavailable_ids_file = f"{self.account_data_dir}/unavailable_ids.json"
        self._ensure_account_dir()
        
        # Load processed và unavailable IDs từ cả thư mục data/account_name và data chung
        self.processed_ids = self._load_all_processed_ids()
        self.unavailable_ids = self._load_all_unavailable_ids()
        print(f"Đã load {len(self.processed_ids)} processed IDs và {len(self.unavailable_ids)} unavailable IDs")

    def _ensure_account_dir(self):
        """Tạo thư mục data và thư mục con cho tài khoản"""
        os.makedirs(self.account_data_dir, exist_ok=True)
        
    def _load_all_processed_ids(self) -> set:
        all_ids = set()
        
        # Load từ thư mục account cụ thể
        account_ids = self._load_ids_from_file(self.processed_ids_file)
        all_ids.update(account_ids)
        
        # Load từ thư mục data chung
        common_file = "data/processed_ids.json"
        if os.path.exists(common_file):
            common_ids = self._load_ids_from_file(common_file)
            all_ids.update(common_ids)
            
        return all_ids

    def _load_all_unavailable_ids(self) -> set:
        all_ids = set()
        
        # Load từ thư mục account cụ thể
        account_ids = self._load_ids_from_file(self.unavailable_ids_file)
        all_ids.update(account_ids)
        
        # Load từ thư mục data chung
        common_file = "data/unavailable_ids.json"
        if os.path.exists(common_file):
            common_ids = self._load_ids_from_file(common_file)
            all_ids.update(common_ids)
            
        return all_ids

    def _load_ids_from_file(self, filename: str) -> set:
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    return set(json.load(f))
            return set()
        except Exception as e:
            print(f"Lỗi khi đọc file {filename}: {str(e)}")
            return set()
            
    def _save_ids_to_file(self, ids: set, filename: str):
        try:
            with open(filename, 'w') as f:
                json.dump(list(ids), f)
        except Exception as e:
            print(f"Lỗi khi lưu file {filename}: {str(e)}")

    def _save_processed_ids(self):
        self._save_ids_to_file(self.processed_ids, self.processed_ids_file)
        
    def _save_unavailable_ids(self):
        self._save_ids_to_file(self.unavailable_ids, self.unavailable_ids_file)

    def send_friend_request(self, profile_id: str) -> bool:
        if not self._can_send_request(profile_id):
            return False
            
        if not self._access_profile(profile_id):
            self.unavailable_ids.add(profile_id)
            self._save_unavailable_ids()
            return False
            
        if self._click_add_friend_button():
            self.processed_ids.add(profile_id)
            self._save_processed_ids()
            return True
            
        self.unavailable_ids.add(profile_id)
        self._save_unavailable_ids()
        return False
        
    def _can_send_request(self, profile_id: str) -> bool:
        return profile_id and profile_id not in self.processed_ids and profile_id not in self.unavailable_ids
        
    def _access_profile(self, profile_id: str) -> bool:
        try:
            self.driver.get(f"https://www.facebook.com/{profile_id}")
            time.sleep(2)
            return True
        except:
            return False
            
    def _click_add_friend_button(self) -> bool:
        try:
            # Find add friend button
            selectors = ['div[aria-label="Thêm bạn bè"]', 'div[aria-label="Add friend"]']
            for selector in selectors:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        button.click()
                        time.sleep(2)
                        return True
            return False
        except:
            return False
            
    def add_friends_from_file(self, json_file: str, max_friends: int = 20) -> int:
        try:
            # Đọc và parse file JSON
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, dict) or 'members' not in data:
                print(f"File {json_file} không đúng định dạng")
                return 0
            
            members = data['members']
            if not members or not isinstance(members, list):
                print("Không có thành viên nào trong file")
                return 0
            
            successful_adds = 0
            skipped = 0
            processed = 0
            
            print(f"\nBắt đầu xử lý {len(members)} thành viên...")
            
            # Lọc danh sách members trước khi xử lý
            valid_members = []
            for member in members:
                user_id = member.get('id')
                name = member.get('name', 'Unknown')
                
                if not user_id:
                    print(f"Bỏ qua: {name} (không có ID)")
                    continue
                    
                # Kiểm tra ID đã xử lý trước
                if user_id in self.processed_ids:
                    print(f"Bỏ qua: {name} (ID: {user_id}) - đã gửi kết bạn trước đó")
                    skipped += 1
                    continue
                    
                if user_id in self.unavailable_ids:
                    print(f"Bỏ qua: {name} (ID: {user_id}) - profile không khả dụng")
                    skipped += 1
                    continue
                    
                valid_members.append(member)
            
            print(f"\nSau khi lọc:")
            print(f"- Tổng số thành viên: {len(members)}")
            print(f"- Đã xử lý trước đó: {skipped}")
            print(f"- Cần xử lý: {len(valid_members)}")
            
            # Xử lý các thành viên hợp lệ
            for member in valid_members:
                if successful_adds >= max_friends:
                    print(f"\nĐã đạt số lượng kết bạn tối đa ({max_friends})")
                    break
                
                user_id = member['id']
                name = member.get('name', 'Unknown')
                
                print(f"\nĐang xử lý: {name} (ID: {user_id})")
                
                try:
                    # Truy cập profile và gửi kết bạn
                    if self._access_profile(user_id) and self._click_add_friend_button():
                        successful_adds += 1
                        self.processed_ids.add(user_id)
                        self._save_processed_ids()
                        print(f"✓ Đã gửi kết bạn thành công ({successful_adds}/{max_friends})")
                        time.sleep(3)
                    else:
                        print(f"✗ Không thể gửi kết bạn")
                        self.unavailable_ids.add(user_id)
                        self._save_unavailable_ids()
                        time.sleep(1)
                    
                except Exception as e:
                    print(f"Lỗi: {str(e)}")
                    self.unavailable_ids.add(user_id)
                    self._save_unavailable_ids()
                    time.sleep(1)
                
                processed += 1
            
            print(f"\nKết quả cuối cùng:")
            print(f"- Tổng số thành viên: {len(members)}")
            print(f"- Đã xử lý trước đó: {skipped}")
            print(f"- Đã xử lý trong lần này: {processed}")
            print(f"- Kết bạn thành công: {successful_adds}")
            
            return successful_adds
            
        except Exception as e:
            print(f"Lỗi khi đọc file {json_file}: {str(e)}")
            return 0

    def _access_profile(self, user_id: str) -> bool:
        max_retries = 3
        base_url = "https://www.facebook.com/"
        
        # Xác định đúng URL dựa trên định dạng ID
        if user_id.isdigit():
            profile_url = f"{base_url}profile.php?id={user_id}"
        else:
            profile_url = f"{base_url}{user_id}"
        
        print(f"Truy cập: {profile_url}")
        
        for attempt in range(max_retries):
            try:
                self.driver.get(profile_url)
                
                # Đợi cho body element xuất hiện
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Kiểm tra xem có bị chuyển hướng đến trang lỗi không
                current_url = self.driver.current_url
                if "login" in current_url or "checkpoint" in current_url:
                    print("Đã bị chuyển hướng đến trang đăng nhập/checkpoint")
                    return False
                
                if "profile unavailable" in self.driver.page_source.lower():
                    print("Profile không khả dụng")
                    return False
                
                # Đợi thêm 1 giây để trang load hoàn toàn
                time.sleep(1)
                return True
                
            except TimeoutException:
                print(f"Timeout khi truy cập profile (lần {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    return False
                time.sleep(2)
                
            except Exception as e:
                print(f"Lỗi khi truy cập profile: {str(e)}")
                return False
        
        return False 