from selenium import webdriver
import pickle
import os
import time
from typing import Dict, List
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class FacebookAuth:
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.cookies_file = "fb_cookies.pkl"
        self.max_retries = 3
        self.timeout = 10
        
    def login_with_cookies(self, cookie_string: str) -> bool:
        if not cookie_string or len(cookie_string.strip()) < 10:
            return False
            
        for attempt in range(self.max_retries):
            try:
                self.driver.get("https://www.facebook.com")
                # Đợi cho đến khi trang load xong
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                cookies = self._parse_cookie_string(cookie_string)
                if not cookies:
                    return False
                    
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
                    
                self.driver.get("https://www.facebook.com")
                return self._verify_login()
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    print(f"Login failed after {self.max_retries} attempts: {str(e)}")
                    return False
                time.sleep(2)
            
    def _parse_cookie_string(self, cookie_string: str) -> List[Dict]:
        cookies = []
        cookie_pairs = [x.strip() for x in cookie_string.split(";")]
        
        for pair in cookie_pairs:
            if "=" not in pair:
                continue
            name, value = pair.split("=", 1)
            cookies.append({
                "name": name.strip(),
                "value": value.strip(),
                "domain": ".facebook.com"
            })
            
        return cookies
        
    def _verify_login(self) -> bool:
        current_url = self.driver.current_url
        return not ("login" in current_url or "checkpoint" in current_url)
        
    def save_cookies(self):
        if self.driver:
            pickle.dump(self.driver.get_cookies(), open(self.cookies_file, "wb"))
            
    def load_cookies(self) -> bool:
        if os.path.exists(self.cookies_file):
            cookies = pickle.load(open(self.cookies_file, "rb"))
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            return True
        return False 