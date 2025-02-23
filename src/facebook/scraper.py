from selenium import webdriver
from selenium.webdriver.common.by import By
from typing import List, Dict, Optional
import json
import time
from datetime import datetime
from ..browser.scroll_helper import ScrollHelper

class FacebookScraper:
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.scroll_helper = ScrollHelper(driver)
        
    def get_group_members(self, group_url: str, max_members: Optional[int] = None) -> List[Dict]:
        try:
            self.driver.get(f"{group_url}/members")
            time.sleep(3)
            
            return self.scroll_helper.scroll_and_extract(
                extractor_func=self._extract_members,
                max_items=max_members
            )
            
        except Exception as e:
            print(f"Failed to get group members: {str(e)}")
            return []
            
    def _extract_members(self) -> List[Dict]:
        members = []
        member_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div[role="listitem"]')
        
        for element in member_elements:
            try:
                member = self._extract_member_info(element)
                if member:
                    members.append(member)
            except:
                continue
                
        return members
        
    def _extract_member_info(self, element) -> Optional[Dict]:
        try:
            link = element.find_element(By.CSS_SELECTOR, 'a[href*="/user/"], a[href*="profile.php"]')
            url = link.get_attribute('href')
            
            # Extract user ID
            user_id = None
            if 'profile.php' in url:
                user_id = url.split('id=')[-1].split('&')[0]
            else:
                user_id = url.split('/user/')[-1].split('?')[0]
                
            if not user_id:
                return None
                
            # Extract other info
            name = link.get_attribute('aria-label') or link.text.strip()
            avatar = element.find_element(By.CSS_SELECTOR, 'image, img')
            avatar_url = avatar.get_attribute('xlink:href') or avatar.get_attribute('src') or ''
            
            return {
                'id': user_id,
                'name': name,
                'profile_url': url,
                'avatar_url': avatar_url,
                'scraped_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except:
            return None
            
    def save_members_to_file(self, members: List[Dict], output_file: str):
        data = {
            'members': members,
            'total_members': len(members),
            'scraped_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2) 