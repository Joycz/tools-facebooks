from selenium import webdriver
from typing import Dict, List
import time

class ScrollHelper:
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.scroll_height = 0
        self.scroll_speed = 800
        self.scroll_pause = 2
        
    def scroll_and_extract(self, extractor_func, max_items: int = None) -> List[Dict]:
        items = []
        no_new_items_count = 0
        max_retries = 3
        
        while True:
            previous_height = self.driver.execute_script("return document.documentElement.scrollHeight")
            items_before = len(items)
            
            # Scroll down
            self.driver.execute_script(f"window.scrollTo(0, {self.scroll_height + self.scroll_speed})")
            time.sleep(self.scroll_pause)
            
            # Extract items
            new_items = extractor_func()
            items.extend(new_items)
            
            # Check progress
            if len(items) == items_before:
                no_new_items_count += 1
            else:
                no_new_items_count = 0
                
            # Check stop conditions
            if max_items and len(items) >= max_items:
                return items[:max_items]
                
            if no_new_items_count >= max_retries:
                break
                
            # Update scroll position
            self.scroll_height = self.driver.execute_script("return document.documentElement.scrollHeight")
            if self.scroll_height == previous_height:
                break
                
        return items
        
    def reset(self):
        self.scroll_height = 0
        self.driver.execute_script("window.scrollTo(0, 0)") 