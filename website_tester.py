"""
Website testing module for browser-based functionality testing.

This module extends browser automation for testing purposes.
"""

from typing import Dict, List, Any, Optional
from browser_automation import BrowserAutomation


class WebsiteTester:
    """Tests website functionality and quality."""
    
    def __init__(self, browser: Optional[BrowserAutomation] = None,
                 headless: bool = True):
        """
        Initialize website tester.
        
        Args:
            browser: Existing browser instance (optional)
            headless: Run browser in headless mode
        """
        self.browser = browser
        self.headless = headless
        self.own_browser = browser is None
    
    def test_website(self, url: str, test_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run basic website tests.
        
        Args:
            url: Website URL to test
            test_config: Test configuration
        
        Returns:
            Dictionary with test results
        """
        if not self.browser:
            self.browser = BrowserAutomation(headless=self.headless)
        
        results = {
            'url': url,
            'tests_passed': 0,
            'tests_failed': 0,
            'test_results': []
        }
        
        try:
            # Navigate to page
            if not self.browser.navigate(url):
                results['tests_failed'] += 1
                results['test_results'].append({
                    'test': 'navigation',
                    'status': 'failed',
                    'message': 'Could not navigate to URL'
                })
                return results
            
            # Test 1: Page loads
            title = self.browser.get_page_title()
            if title:
                results['tests_passed'] += 1
                results['test_results'].append({
                    'test': 'page_load',
                    'status': 'passed',
                    'message': f'Page loaded: {title}'
                })
            else:
                results['tests_failed'] += 1
                results['test_results'].append({
                    'test': 'page_load',
                    'status': 'failed',
                    'message': 'Page title not found'
                })
            
            # Test 2: Links exist (basic check)
            try:
                from selenium.webdriver.common.by import By
                links = self.browser.driver.find_elements(By.TAG_NAME, 'a')
                if links:
                    results['tests_passed'] += 1
                    results['test_results'].append({
                        'test': 'links_exist',
                        'status': 'passed',
                        'message': f'Found {len(links)} links'
                    })
                else:
                    results['tests_failed'] += 1
                    results['test_results'].append({
                        'test': 'links_exist',
                        'status': 'failed',
                        'message': 'No links found on page'
                    })
            except Exception as e:
                results['test_results'].append({
                    'test': 'links_exist',
                    'status': 'error',
                    'message': str(e)
                })
            
            # Test 3: Images load (basic check)
            try:
                from selenium.webdriver.common.by import By
                images = self.browser.driver.find_elements(By.TAG_NAME, 'img')
                broken_images = 0
                for img in images[:5]:  # Check first 5 images
                    if not img.get_attribute('src'):
                        broken_images += 1
                
                if broken_images == 0 and images:
                    results['tests_passed'] += 1
                    results['test_results'].append({
                        'test': 'images_load',
                        'status': 'passed',
                        'message': f'Found {len(images)} images'
                    })
                elif broken_images > 0:
                    results['tests_failed'] += 1
                    results['test_results'].append({
                        'test': 'images_load',
                        'status': 'failed',
                        'message': f'{broken_images} images may be broken'
                    })
            except Exception as e:
                results['test_results'].append({
                    'test': 'images_load',
                    'status': 'error',
                    'message': str(e)
                })
            
            # Test 4: Responsive check (basic)
            try:
                viewport_size = self.browser.driver.get_window_size()
                results['tests_passed'] += 1
                results['test_results'].append({
                    'test': 'viewport',
                    'status': 'passed',
                    'message': f'Viewport: {viewport_size["width"]}x{viewport_size["height"]}'
                })
            except Exception as e:
                results['test_results'].append({
                    'test': 'viewport',
                    'status': 'error',
                    'message': str(e)
                })
        
        except Exception as e:
            results['tests_failed'] += 1
            results['test_results'].append({
                'test': 'general',
                'status': 'error',
                'message': f'Test error: {str(e)}'
            })
        
        return results
    
    def test_local_file(self, file_path: str) -> Dict[str, Any]:
        """
        Test a local HTML file.
        
        Args:
            file_path: Path to HTML file
        
        Returns:
            Test results
        """
        import os
        from pathlib import Path
        
        full_path = os.path.abspath(file_path)
        # Convert to file:// URL
        url = f"file://{full_path}"
        
        return self.test_website(url)
    
    def close(self):
        """Close browser if we own it."""
        if self.own_browser and self.browser:
            self.browser.close()
            self.browser = None

