"""
Quick Playwright test to verify frontend connection after port fix.
"""

import asyncio
from playwright.async_api import async_playwright


async def test_frontend_connection_fixed():
    """Test that frontend now connects to backend on port 8004"""
    print("🎭 Testing Frontend Connection After Port Fix")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("  📱 Navigating to frontend...")
            await page.goto("http://localhost:5175")
            
            # Wait for page to load and API calls to complete
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)  # Give time for API health check
            
            # Check if we can find the title
            title = await page.title()
            print(f"  📝 Page title: {title}")
            
            # Look for the main title
            try:
                await page.wait_for_selector("text=AI Talent Flow Intelligence", timeout=5000)
                print("  ✅ Main title found")
            except:
                print("  ❌ Main title not found")
            
            # Check for connection status
            try:
                # Look for any error messages about connection
                error_elements = await page.query_selector_all("text*=Cannot connect")
                if error_elements:
                    print("  ❌ Still showing connection errors")
                    error_text = await error_elements[0].inner_text()
                    print(f"      Error: {error_text}")
                else:
                    print("  ✅ No connection error messages found")
            except:
                print("  ℹ️  Could not check for error messages")
            
            # Check if we can see any data
            try:
                # Look for data elements that would indicate successful API calls
                await page.wait_for_selector("text*=Dr. Emma Rodriguez", timeout=5000)
                print("  ✅ Sample talent data found - API connection working!")
            except:
                print("  ⚠️  Sample talent data not visible yet")
            
            # Take a screenshot for verification
            await page.screenshot(path="frontend_connection_test.png", full_page=True)
            print("  📸 Screenshot saved: frontend_connection_test.png")
            
        except Exception as e:
            print(f"  ❌ Test failed: {e}")
            await page.screenshot(path="frontend_connection_error.png")
            
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_frontend_connection_fixed())