from selenium import webdriver
import undetected_chromedriver as uc
from fake_useragent import UserAgent
import psutil
import signal
import os

class ChromeManager:
    def __init__(self):
        self.driver = None
        self.current_process = None
        
    def setup_driver(self) -> webdriver.Chrome:
        self.kill_chrome_processes()  # Đảm bảo không có process cũ
        options = self._configure_chrome_options()
        self.driver = self._create_driver_with_retry(options)
        self._apply_stealth_settings()
        return self.driver
    
    def _configure_chrome_options(self) -> uc.ChromeOptions:
        options = uc.ChromeOptions()
        ua = UserAgent()
        
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        options.add_argument('--no-sandbox')
        options.add_argument(f'--user-agent={ua.random}')
        options.add_argument('--disable-notifications')
        
        return options
    
    def _create_driver_with_retry(self, options: uc.ChromeOptions, max_retries: int = 3) -> webdriver.Chrome:
        for attempt in range(max_retries):
            try:
                driver = uc.Chrome(options=options)
                # Lưu process ID của Chrome
                for proc in psutil.process_iter(['pid', 'name']):
                    if 'chrome' in proc.info['name'].lower():
                        self.current_process = proc
                        break
                return driver
            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Không thể tạo driver sau {max_retries} lần thử") from e
                self.kill_chrome_processes()
        return None
    
    def _apply_stealth_settings(self):
        if not self.driver:
            return
            
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        
    def kill_chrome_processes(self):
        try:
            # Đóng driver trước
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as e:
                    print(f"Không thể đóng driver: {str(e)}")

            # Kill process hiện tại nếu có
            if self.current_process and self.current_process.is_running():
                try:
                    self.current_process.terminate()  # Dùng terminate thay vì kill
                    self.current_process.wait(timeout=3)  # Đợi process dừng
                except psutil.TimeoutExpired:
                    self.current_process.kill()  # Kill nếu không dừng được
                except Exception as e:
                    print(f"Không thể dừng process hiện tại: {str(e)}")

            # Kill các process Chrome còn lại
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if 'chrome' in proc.info['name'].lower():
                        proc_obj = psutil.Process(proc.info['pid'])
                        proc_obj.terminate()
                        proc_obj.wait(timeout=3)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired) as e:
                    print(f"Không thể dừng process {proc.info['pid']}: {str(e)}")
                except Exception as e:
                    print(f"Lỗi không xác định: {str(e)}")

        except Exception as e:
            print(f"Lỗi khi dừng Chrome: {str(e)}")
        finally:
            self.driver = None
            self.current_process = None
                
    def quit(self):
        self.kill_chrome_processes() 