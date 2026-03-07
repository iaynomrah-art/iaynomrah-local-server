import sys
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

def main():
    username = sys.argv[1] if len(sys.argv) > 1 else "DemoUser"  # Replace with actual user if known
    
    # Path to the persistent profile
    base_dir = Path("c:/Users/Admin/Documents/code/iaynomrah-local-server")
    profile_dir = base_dir / "ctrader_profile" / username
    
    if not profile_dir.exists():
        print(f"Profile directory {profile_dir} not found!")
        return
        
    print(f"Connecting to persistent context at {profile_dir}...")
    
    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(profile_dir),
                channel="chrome",
                headless=True
            )
            
            # Find the active cTrader page
            target_page = None
            for page in context.pages:
                if "ctrader.com" in page.url:
                    target_page = page
                    break
                    
            if not target_page:
                print("No cTrader page found. Creating one...")
                target_page = context.new_page()
                target_page.goto("https://app.ctrader.com/")
                target_page.wait_for_load_state("networkidle")
                
            print(f"Analyzing page: {target_page.url}")
            
            # The user's screenshot highlights this specific hierarchy
            # Let's grab the HTML of the footer bar to see its exact structure
            
            print("\n--- Strategy 1: Find by text 'Balance:' ---")
            elements = target_page.locator("*:has-text('Balance:')").all()
            for i, el in enumerate(elements[-3:]): # Get the last few matches
                try:
                    html = el.evaluate("el => el.outerHTML")
                    print(f"Match {i} HTML:\n{html[:300]}...\n")
                except Exception as e:
                    pass
                    
            print("\n--- Strategy 2: Find the specific data test IDs ---")
            # We can also execute some raw JS to find the balance element
            footer_html = target_page.evaluate("""() => {
                // Find any span containing 'Balance'
                const spans = Array.from(document.querySelectorAll('span'));
                const balanceSpan = spans.find(s => s.textContent.includes('Balance:'));
                if (balanceSpan) {
                    // Go up a few levels to get the container
                    return balanceSpan.parentElement.parentElement.outerHTML;
                }
                return "Not found";
            }""")
            print(f"Footer HTML:\n{footer_html}\n")
            
            context.close()
            
        except Exception as e:
            print(f"Error connecting: {e}")

if __name__ == "__main__":
    main()
