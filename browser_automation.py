"""
Selenium browser automation wrapper for Brave browser.

This module handles:
- Browser initialization (Brave-specific)
- Tab switching, clicking, navigation
- Element interaction helpers
- Screenshot capture for debugging
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from typing import Optional, List, Dict, Any
import time
import os


class BrowserAutomation:
    """Selenium wrapper for Brave browser automation."""
    
    def __init__(self, brave_path: Optional[str] = None, headless: bool = False):
        """
        Initialize Brave browser instance.
        
        Args:
            brave_path: Path to Brave browser executable (macOS default: /Applications/Brave Browser.app/Contents/MacOS/Brave Browser)
            headless: Run browser in headless mode
        """
        self.driver = None
        self.brave_path = brave_path or self._find_brave_path()
        self.headless = headless
        self._initialize_driver()
    
    def _find_brave_path(self) -> Optional[str]:
        """Find Brave browser path on macOS."""
        default_paths = [
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            "/usr/bin/brave-browser",
            "/usr/local/bin/brave-browser"
        ]
        
        for path in default_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _initialize_driver(self):
        """Initialize Selenium WebDriver with Brave options.
        
        Uses Selenium 4's built-in driver management to automatically handle ChromeDriver,
        avoiding manual installation and Gatekeeper warnings.
        """
        chrome_options = Options()
        
        if self.brave_path:
            chrome_options.binary_location = self.brave_path
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Additional options for stability
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Try to initialize driver with Selenium 4's automatic driver management
        try:
            # Selenium 4.6+ automatically downloads and manages ChromeDriver
            # No manual installation needed!
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
        except Exception as e:
            raise Exception(f"Failed to initialize Brave browser: {str(e)}\n"
                          f"Selenium will automatically download ChromeDriver on first run.\n"
                          f"If issues persist, check your internet connection.")
    
    def navigate(self, url: str) -> bool:
        """
        Navigate to a URL.
        
        Args:
            url: URL to navigate to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.driver.get(url)
            return True
        except Exception as e:
            print(f"Navigation error: {str(e)}")
            return False
    
    def click_element(self, selector: str, by: By = By.CSS_SELECTOR, 
                     timeout: int = 10) -> bool:
        """
        Click an element on the page.
        
        Args:
            selector: CSS selector, XPath, or other selector
            by: Selenium By strategy (default: CSS_SELECTOR)
            timeout: Maximum wait time in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, selector))
            )
            element.click()
            return True
        except TimeoutException:
            print(f"Element not found or not clickable: {selector}")
            return False
        except Exception as e:
            print(f"Click error: {str(e)}")
            return False
    
    def type_text(self, selector: str, text: str, by: By = By.CSS_SELECTOR,
                  timeout: int = 10) -> bool:
        """
        Type text into an input field.
        
        Args:
            selector: Element selector
            text: Text to type
            by: Selenium By strategy
            timeout: Maximum wait time
            
        Returns:
            True if successful, False otherwise
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            element.clear()
            element.send_keys(text)
            return True
        except TimeoutException:
            print(f"Input element not found: {selector}")
            return False
        except Exception as e:
            print(f"Type text error: {str(e)}")
            return False
    
    def get_text(self, selector: str, by: By = By.CSS_SELECTOR,
                timeout: int = 10) -> Optional[str]:
        """
        Get text content from an element.
        
        Args:
            selector: Element selector
            by: Selenium By strategy
            timeout: Maximum wait time
            
        Returns:
            Text content or None if not found
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return element.text
        except TimeoutException:
            print(f"Element not found: {selector}")
            return None
        except Exception as e:
            print(f"Get text error: {str(e)}")
            return None
    
    def switch_tab(self, index: int) -> bool:
        """
        Switch to a different browser tab.
        
        Args:
            index: Tab index (0-based)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            tabs = self.driver.window_handles
            if 0 <= index < len(tabs):
                self.driver.switch_to.window(tabs[index])
                return True
            return False
        except Exception as e:
            print(f"Switch tab error: {str(e)}")
            return False
    
    def get_current_url(self) -> Optional[str]:
        """Get current page URL."""
        try:
            return self.driver.current_url
        except Exception:
            return None
    
    def get_page_title(self) -> Optional[str]:
        """Get current page title."""
        try:
            return self.driver.title
        except Exception:
            return None
    
    def wait_for_element(self, selector: str, by: By = By.CSS_SELECTOR,
                        timeout: int = 10) -> bool:
        """
        Wait for an element to appear on the page.
        
        Args:
            selector: Element selector
            by: Selenium By strategy
            timeout: Maximum wait time
            
        Returns:
            True if element appears, False otherwise
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return True
        except TimeoutException:
            return False
    
    def take_screenshot(self, filepath: str) -> bool:
        """
        Take a screenshot of the current page.
        
        Args:
            filepath: Path to save screenshot
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.driver.save_screenshot(filepath)
            return True
        except Exception as e:
            print(f"Screenshot error: {str(e)}")
            return False
    
    def execute_script(self, script: str) -> Any:
        """
        Execute JavaScript in the browser.
        
        Args:
            script: JavaScript code to execute
            
        Returns:
            Result of script execution
        """
        try:
            return self.driver.execute_script(script)
        except Exception as e:
            print(f"Script execution error: {str(e)}")
            return None
    
    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

