import json
import os
import shutil
import msvcrt
import time
from typing import List, Optional
from .account import Account

class SafeFileHandler:
    def __init__(self, filename):
        self.filename = filename
        self.lock_file = f"{filename}.lock"
        self.file_handle = None
        
    def __enter__(self):
        # Thử acquire lock trong 10 giây
        start_time = time.time()
        while time.time() - start_time < 10:
            try:
                # Mở file với chế độ exclusive
                self.file_handle = open(self.lock_file, 'wb+')
                msvcrt.locking(self.file_handle.fileno(), msvcrt.LK_NBLCK, 1)
                return self
            except IOError:
                time.sleep(0.1)
        raise IOError("Không thể acquire lock sau 10 giây")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file_handle:
            try:
                # Unlock và đóng file
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
            # Thử khôi phục từ backup
            backup_file = f"{self.filename}.bak"
            if os.path.exists(backup_file):
                shutil.copy2(backup_file, self.filename)
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
            
    def write(self, data):
        # Tạo backup của file hiện tại
        if os.path.exists(self.filename):
            shutil.copy2(self.filename, f"{self.filename}.bak")
            
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

class Storage:
    def __init__(self, accounts_file: str = 'accounts.json'):
        self.accounts_file = accounts_file
        self._ensure_file_exists()
        
    def _ensure_file_exists(self):
        if not os.path.exists(self.accounts_file):
            with SafeFileHandler(self.accounts_file) as handler:
                handler.write([])
                
    def load_accounts(self) -> List[Account]:
        with SafeFileHandler(self.accounts_file) as handler:
            data = handler.read()
            if data is None:
                return []
            return [Account.from_dict(acc) for acc in data]
            
    def save_accounts(self, accounts: List[Account]):
        with SafeFileHandler(self.accounts_file) as handler:
            handler.write([acc.to_dict() for acc in accounts])
            
    def add_account(self, name: str, cookie: str) -> Account:
        with SafeFileHandler(self.accounts_file) as handler:
            data = handler.read()
            if data is None:
                data = []
            
            new_id = len(data) + 1
            account = Account.create(new_id, name, cookie)
            data.append(account.to_dict())
            handler.write(data)
            return account
            
    def update_account(self, id: int, name: str, cookie: str) -> Optional[Account]:
        with SafeFileHandler(self.accounts_file) as handler:
            data = handler.read()
            if data is None:
                return None
                
            for acc in data:
                if acc['id'] == id:
                    account = Account.from_dict(acc)
                    account.update(name, cookie)
                    acc.update(account.to_dict())
                    handler.write(data)
                    return account
                    
            return None
            
    def delete_account(self, id: int) -> bool:
        with SafeFileHandler(self.accounts_file) as handler:
            data = handler.read()
            if data is None:
                return False
                
            filtered = [acc for acc in data if acc['id'] != id]
            if len(filtered) < len(data):
                handler.write(filtered)
                return True
                
            return False
            
    def get_account(self, id: int) -> Optional[Account]:
        with SafeFileHandler(self.accounts_file) as handler:
            data = handler.read()
            if data is None:
                return None
                
            for acc in data:
                if acc['id'] == id:
                    return Account.from_dict(acc)
                    
            return None 