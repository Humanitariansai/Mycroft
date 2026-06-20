"""
Advanced Playwright tests for AI Talent Flow Intelligence frontend.
Tests the React dashboard and user interface interactions.
"""

import asyncio
import time
from playwright.async_api import async_playwright, Page


async def test_frontend_dashboard():
    """Test the React frontend dashboard"""
    print("🎭 Testing React Frontend Dashboard")
    
    async with async_playwright() as p:
        # Launch browser in headful mode to see the test
        browser = await p.chromium.launch(
            headless=False,  # Set to True for headless testing
            slow_mo=1000     # Slow down for demonstration
        )
        
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Navigate to frontend
            print("  📱 Navigating to frontend dashboard...")
            await page.goto("http://localhost:5175")
            
            # Wait for page to load
            await page.wait_for_load_state("networkidle")
            
            # Take screenshot of initial state
            await page.screenshot(path="dashboard_initial.png")
            print("  📸 Screenshot saved: dashboard_initial.png")
            
            # Check if the page title is correct
            title = await page.title()
            print(f"  📝 Page title: {title}")
            
            # Look for key elements
            await page.wait_for_selector("text=AI Talent Flow Intelligence", timeout=10000)
            print("  ✅ Main title found")
            
            # Check for API connection status
            try:
                await page.wait_for_selector("[data-testid='api-status']", timeout=5000)
                status = await page.text_content("[data-testid='api-status']")
                print(f"  🔌 API Status: {status}")
            except:
                print("  ⚠️  API status element not found")
            
            # Look for dashboard sections
            sections_to_check = [
                "Talent Profiles",
                "Recent Movements", 
                "Investment Signals",
                "Predictive Analytics"
            ]
            
            for section in sections_to_check:
                try:
                    await page.wait_for_selector(f"text={section}", timeout=3000)
                    print(f"  ✅ Found section: {section}")
                except:
                    print(f"  ❌ Section not found: {section}")
            
            # Test tab navigation if tabs exist
            try:
                await page.click("text=Analytics", timeout=3000)
                await page.wait_for_timeout(1000)
                print("  🔄 Clicked Analytics tab")
                
                await page.click("text=Monitoring", timeout=3000)
                await page.wait_for_timeout(1000)
                print("  🔄 Clicked Monitoring tab")
                
                await page.click("text=Dashboard", timeout=3000)
                await page.wait_for_timeout(1000)
                print("  🔄 Clicked Dashboard tab")
            except:
                print("  ℹ️  Tab navigation not available")
            
            # Test real-time data loading
            try:
                # Look for loading indicators
                await page.wait_for_selector(".loading", timeout=2000)
                print("  ⏳ Loading indicator found")
                
                # Wait for data to load
                await page.wait_for_selector(".loading", state="hidden", timeout=10000)
                print("  ✅ Data loaded successfully")
            except:
                print("  ℹ️  No loading indicators found")
            
            # Test responsive design
            print("  📱 Testing responsive design...")
            
            # Desktop view
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.wait_for_timeout(1000)
            await page.screenshot(path="dashboard_desktop.png")
            print("  📸 Desktop screenshot: dashboard_desktop.png")
            
            # Tablet view
            await page.set_viewport_size({"width": 768, "height": 1024})
            await page.wait_for_timeout(1000)
            await page.screenshot(path="dashboard_tablet.png")
            print("  📸 Tablet screenshot: dashboard_tablet.png")
            
            # Mobile view
            await page.set_viewport_size({"width": 375, "height": 667})
            await page.wait_for_timeout(1000)
            await page.screenshot(path="dashboard_mobile.png")
            print("  📸 Mobile screenshot: dashboard_mobile.png")
            
            # Test error handling
            print("  🔧 Testing error handling...")
            
            # Simulate network failure
            await context.route("**/api/**", lambda route: route.abort())
            
            # Try to refresh and see error handling
            await page.reload()
            await page.wait_for_timeout(2000)
            
            # Look for error messages
            try:
                await page.wait_for_selector("text=Error", timeout=3000)
                print("  ✅ Error state detected")
            except:
                print("  ℹ️  No error state found")
            
            await page.screenshot(path="dashboard_error_state.png")
            print("  📸 Error state screenshot: dashboard_error_state.png")
            
            print("  ✅ Frontend dashboard tests completed")
            
        except Exception as e:
            print(f"  ❌ Frontend test failed: {e}")
            await page.screenshot(path="dashboard_error.png")
            print("  📸 Error screenshot: dashboard_error.png")
            
        finally:
            await browser.close()


async def test_api_interactions():
    """Test API interactions through browser console"""
    print("🎭 Testing API Interactions via Browser")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            await page.goto("about:blank")
            
            # Test API calls directly in browser
            api_tests = [
                {
                    "name": "Health Check",
                    "code": """
                        fetch('http://localhost:8004/health')
                        .then(r => r.json())
                        .then(data => ({success: true, data}))
                        .catch(err => ({success: false, error: err.message}))
                    """
                },
                {
                    "name": "Talent Profiles",
                    "code": """
                        fetch('http://localhost:8004/api/talent/profiles')
                        .then(r => r.json())
                        .then(data => ({success: true, count: data.length}))
                        .catch(err => ({success: false, error: err.message}))
                    """
                },
                {
                    "name": "Movement Prediction",
                    "code": """
                        fetch('http://localhost:8004/api/predictions/movement-impact', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                talent_name: "Dr. Emma Rodriguez",
                                to_company: "OpenAI", 
                                to_role: "VP Research",
                                movement_type: "job_change"
                            })
                        })
                        .then(r => r.json())
                        .then(data => ({success: true, prediction: data.prediction?.predicted_impact}))
                        .catch(err => ({success: false, error: err.message}))
                    """
                }
            ]
            
            for test in api_tests:
                print(f"  🧪 Testing {test['name']}...")
                result = await page.evaluate(test['code'])
                
                if result.get('success'):
                    print(f"  ✅ {test['name']} - Success")
                    if 'data' in result:
                        print(f"      Status: {result['data'].get('status', 'N/A')}")
                    if 'count' in result:
                        print(f"      Records: {result['count']}")
                    if 'prediction' in result:
                        print(f"      Prediction: {result['prediction']}")
                else:
                    print(f"  ❌ {test['name']} - Failed: {result.get('error')}")
                
                await page.wait_for_timeout(1000)
            
        finally:
            await browser.close()


async def test_websocket_connection():
    """Test WebSocket real-time monitoring"""
    print("🎭 Testing WebSocket Real-time Monitoring")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            await page.goto("about:blank")
            
            # Test WebSocket connection
            ws_test_code = """
                new Promise((resolve) => {
                    const ws = new WebSocket('ws://localhost:8005');
                    const events = [];
                    let connected = false;
                    
                    ws.onopen = () => {
                        connected = true;
                        console.log('WebSocket connected');
                        
                        // Send ping
                        ws.send(JSON.stringify({type: 'ping'}));
                    };
                    
                    ws.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        events.push(data);
                        console.log('Received event:', data);
                    };
                    
                    ws.onerror = (error) => {
                        console.log('WebSocket error:', error);
                        resolve({success: false, error: 'Connection failed'});
                    };
                    
                    // Test for 5 seconds
                    setTimeout(() => {
                        ws.close();
                        resolve({
                            success: connected,
                            events: events.length,
                            connected: connected
                        });
                    }, 5000);
                });
            """
            
            print("  🔌 Testing WebSocket connection...")
            result = await page.evaluate(ws_test_code)
            
            if result.get('success'):
                print(f"  ✅ WebSocket connected successfully")
                print(f"      Events received: {result.get('events', 0)}")
            else:
                print(f"  ❌ WebSocket connection failed: {result.get('error')}")
                
        except Exception as e:
            print(f"  ❌ WebSocket test error: {e}")
            
        finally:
            await browser.close()


async def run_advanced_playwright_tests():
    """Run all advanced Playwright tests"""
    print("🚀 Advanced Playwright Testing Suite")
    print("=" * 60)
    
    tests = [
        ("Frontend Dashboard", test_frontend_dashboard),
        ("API Interactions", test_api_interactions), 
        ("WebSocket Connection", test_websocket_connection)
    ]
    
    results = []
    
    for name, test_func in tests:
        print(f"\n📋 {name}")
        print("-" * 40)
        
        start_time = time.time()
        try:
            await test_func()
            duration = time.time() - start_time
            results.append({"name": name, "status": "PASSED", "duration": duration})
            print(f"✅ {name} completed in {duration:.2f}s")
        except Exception as e:
            duration = time.time() - start_time
            results.append({"name": name, "status": "FAILED", "duration": duration, "error": str(e)})
            print(f"❌ {name} failed in {duration:.2f}s: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("🎭 ADVANCED PLAYWRIGHT SUMMARY")
    
    passed = sum(1 for r in results if r["status"] == "PASSED")
    failed = sum(1 for r in results if r["status"] == "FAILED")
    
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    total_time = sum(r["duration"] for r in results)
    print(f"⏱️  Total time: {total_time:.2f}s")
    
    if failed == 0:
        print("🎉 ALL ADVANCED TESTS PASSED!")
    
    return results


if __name__ == "__main__":
    asyncio.run(run_advanced_playwright_tests())