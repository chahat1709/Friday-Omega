from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time

class WebResearcher:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None

    def _init_driver(self):
        if self.driver:
            return
            
        print("[WebResearcher] Initializing Chrome Driver...")
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new") 
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print("[WebResearcher] Driver initialized.")
        except Exception as e:
            print(f"[WebResearcher] Init failed: {e}")

    def research(self, topic):
        self._init_driver()
        if not self.driver:
            return "Error: Could not start browser."

        print(f"[WebResearcher] Searching for: {topic}")
        results = ""
        try:
            # 1. Search Google/DuckDuckGo
            search_url = f"https://html.duckduckgo.com/html/?q={topic}"
            self.driver.get(search_url)
            
            # 2. Extract first few results
            # Wait for results
            time.sleep(2) 
            
            links = self.driver.find_elements(By.CSS_SELECTOR, ".result__a")
            summaries = []
            
            # Get top 3
            # Use a more generic selector for DDG snippets if possible, or just extract text block from result
            for i, link in enumerate(links[:3]):
                title = link.text
                url = link.get_attribute('href')
                
                # Try to get snippet (usually next sibling or child of parent)
                snippet = "No details."
                try:
                    # DDG structure: .result__body > .result__snippet
                    # link is .result__a inside .result__body
                    # We need to find the parent div and then get the snippet
                    parent = link.find_element(By.XPATH, "./../..")
                    snippet_el = parent.find_element(By.CLASS_NAME, "result__snippet")
                    snippet = snippet_el.text
                except:
                    pass
                
                summaries.append(f"Source {i+1}: {title}\nDesc: {snippet}\nURL: {url}")
            
            results = "\n\n".join(summaries)
            
            # Simple content extraction from first result (optional)
            if links:
                first_url = links[0].get_attribute('href')
                print(f"[WebResearcher] Reading first source: {first_url}")
                self.driver.get(first_url)
                time.sleep(2)
                body = self.driver.find_element(By.TAG_NAME, "body").text
                # Truncate
                snippet = body[:1000].replace('\n', ' ')
                results += f"\n\n--- Content Snippet ---\n{snippet}..."

        except Exception as e:
            results = f"Search Error: {e}"
            
        return results

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
