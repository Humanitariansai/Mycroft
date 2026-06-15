"""
Quick test to verify frontend CORS connectivity
"""
import asyncio
from playwright.async_api import async_playwright

async def test_frontend_api_connection():
    """Test that frontend can now connect to API after CORS fix"""
    print("🔧 Testing Frontend API Connection After CORS Fix")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Navigate to frontend
            print("  📱 Loading frontend...")
            await page.goto("http://localhost:5175")
            await page.wait_for_load_state("networkidle")
            
            # Wait a bit for API calls to complete
            await asyncio.sleep(5)
            
            # Test API call from browser console
            print("  🔌 Testing API call from browser...")
            api_result = await page.evaluate("""
                fetch('http://localhost:8004/health')
                .then(response => response.json())
                .then(data => ({success: true, status: data.status}))
                .catch(error => ({success: false, error: error.message}))
            """)
            
            if api_result['success']:
                print(f"  ✅ API call successful: {api_result['status']}")
                
                # Test talent profiles call
                talent_result = await page.evaluate("""
                    fetch('http://localhost:8004/api/talent/profiles')
                    .then(response => response.json())
                    .then(data => ({success: true, count: data.length}))
                    .catch(error => ({success: false, error: error.message}))
                """)
                
                if talent_result['success']:
                    print(f"  ✅ Talent API call successful: {talent_result['count']} profiles")
                else:
                    print(f"  ❌ Talent API failed: {talent_result['error']}")
            else:
                print(f"  ❌ API call failed: {api_result['error']}")
            
            # Check for error messages on page
            try:
                error_elements = await page.query_selector_all("text*=Connection Error")
                if error_elements:
                    print("  ⚠️  Still showing connection error on page")
                else:
                    print("  ✅ No connection errors visible on page")
            except:
                print("  ℹ️  Could not check page for errors")
            
            # Take screenshot
            await page.screenshot(path="frontend_after_cors_fix.png")
            print("  📸 Screenshot saved: frontend_after_cors_fix.png")
            
        except Exception as e:
            print(f"  ❌ Test failed: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_frontend_api_connection())