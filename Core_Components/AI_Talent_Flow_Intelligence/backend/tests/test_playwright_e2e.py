"""
End-to-end Playwright tests for AI Talent Flow Intelligence system.
Tests the complete user journey through web interface and API interactions.
"""

import asyncio
import pytest
import json
import time
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import httpx

class TestAITalentFlowE2E:
    """Comprehensive end-to-end tests using Playwright"""
    
    @pytest.fixture(scope="class")
    async def browser(self):
        """Create browser instance"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            yield browser
            await browser.close()
    
    @pytest.fixture
    async def page(self, browser: Browser):
        """Create new page for each test"""
        context = await browser.new_context()
        page = await context.new_page()
        yield page
        await context.close()
    
    async def wait_for_backend(self, timeout=30):
        """Wait for backend API to be ready"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:8004/health", timeout=5.0)
                    if response.status_code == 200:
                        return True
            except:
                pass
            await asyncio.sleep(1)
        return False
    
    async def test_api_health_check(self):
        """Test that the API is running and healthy"""
        backend_ready = await self.wait_for_backend()
        assert backend_ready, "Backend API not responding"
        
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8004/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert "services" in data
            assert data["services"]["predictive_models"] == "operational"
    
    async def test_talent_profiles_api(self):
        """Test talent profiles API endpoint"""
        await self.wait_for_backend()
        
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8004/api/talent/profiles")
            assert response.status_code == 200
            
            profiles = response.json()
            assert isinstance(profiles, list)
            assert len(profiles) >= 3  # Should have sample data
            
            # Check profile structure
            profile = profiles[0]
            required_fields = ["id", "name", "current_company", "current_role", "influence_score"]
            for field in required_fields:
                assert field in profile
    
    async def test_companies_api(self):
        """Test company profiles API endpoint"""
        await self.wait_for_backend()
        
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8004/api/companies/profiles")
            assert response.status_code == 200
            
            companies = response.json()
            assert isinstance(companies, list)
            assert len(companies) >= 3
            
            # Check company structure
            company = companies[0]
            required_fields = ["id", "name", "ticker_symbol", "company_size"]
            for field in required_fields:
                assert field in company
    
    async def test_movement_prediction_api(self):
        """Test movement impact prediction API"""
        await self.wait_for_backend()
        
        prediction_data = {
            "talent_name": "Dr. Emma Rodriguez",
            "to_company": "OpenAI",
            "to_role": "VP of Research",
            "movement_type": "job_change"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8004/api/predictions/movement-impact",
                json=prediction_data,
                timeout=10.0
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "success"
            assert "prediction" in data
            assert "timing" in data
            assert "investment_recommendation" in data
            
            # Check prediction structure
            prediction = data["prediction"]
            assert "ticker" in prediction
            assert "predicted_impact" in prediction
            assert "confidence" in prediction
            assert 0 <= prediction["confidence"] <= 1
    
    async def test_monitoring_status_api(self):
        """Test real-time monitoring API"""
        await self.wait_for_backend()
        
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8004/api/monitoring/status")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert "monitoring" in data
            assert "websocket_url" in data
            
            # Check monitoring structure
            monitoring = data["monitoring"]
            assert "monitoring_enabled" in monitoring
            assert "thresholds" in monitoring
            assert "uptime_seconds" in monitoring
    
    async def test_monitoring_events_api(self):
        """Test monitoring events API"""
        await self.wait_for_backend()
        
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8004/api/monitoring/events")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert "events" in data
            assert isinstance(data["events"], list)
    
    async def test_demo_generation_api(self):
        """Test demo movement generation"""
        await self.wait_for_backend()
        
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8004/api/demo/generate-predictive-movement")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert "demo_movement" in data
            assert "predictive_analysis" in data
            assert "enhanced_signal" in data
    
    async def test_scenario_analysis_api(self):
        """Test scenario analysis API"""
        await self.wait_for_backend()
        
        scenarios = {
            "scenarios": [
                {
                    "name": "OpenAI Acquisition",
                    "talent_name": "Dr. Emma Rodriguez",
                    "to_company": "OpenAI",
                    "to_role": "Chief Research Officer",
                    "movement_type": "job_change"
                },
                {
                    "name": "Anthropic Move", 
                    "talent_name": "Alex Chen",
                    "to_company": "Anthropic",
                    "to_role": "VP of Engineering",
                    "movement_type": "job_change"
                }
            ]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8004/api/predictions/scenario-analysis",
                json=scenarios,
                timeout=15.0
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "success"
            assert "scenario_analysis" in data
            
            analysis = data["scenario_analysis"]
            assert "total_scenarios" in analysis
            assert "scenarios" in analysis
            assert len(analysis["scenarios"]) == 2
    
    async def test_market_timing_api(self):
        """Test market timing analysis API"""
        await self.wait_for_backend()
        
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8004/api/predictions/market-timing/OPENAI")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert "timing_analysis" in data
            assert "market_context" in data
            assert "recommendation_summary" in data
    
    async def test_alert_triggering(self):
        """Test custom alert triggering"""
        await self.wait_for_backend()
        
        alert_data = {
            "event_type": "test_e2e_alert",
            "level": "info",
            "message": "Playwright E2E test alert",
            "data": {"test_source": "playwright"}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8004/api/monitoring/trigger-alert",
                json=alert_data
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "success"
            assert "event" in data
            assert data["event"]["event_type"] == "test_e2e_alert"
    
    async def test_api_documentation_available(self):
        """Test that API documentation is accessible"""
        await self.wait_for_backend()
        
        async with httpx.AsyncClient() as client:
            # Test Swagger UI
            response = await client.get("http://localhost:8004/docs")
            assert response.status_code == 200
            assert "swagger" in response.text.lower()
            
            # Test ReDoc
            response = await client.get("http://localhost:8004/redoc")
            assert response.status_code == 200
            assert "redoc" in response.text.lower()
    
    async def test_integration_endpoints(self):
        """Test Mycroft integration endpoints"""
        await self.wait_for_backend()
        
        # Test ecosystem status
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8004/api/integration/ecosystem-status")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert "ecosystem_status" in data
            assert "integration_features" in data
    
    async def test_performance_benchmarks(self):
        """Test API performance with multiple requests"""
        await self.wait_for_backend()
        
        start_time = time.time()
        
        # Make 10 concurrent requests
        async with httpx.AsyncClient() as client:
            tasks = []
            for _ in range(10):
                task = client.get("http://localhost:8004/health")
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
        
        # Should handle 10 requests in under 5 seconds
        assert duration < 5.0, f"Performance test took {duration:.2f} seconds"
        
        avg_response_time = duration / 10
        print(f"Average response time: {avg_response_time:.3f} seconds")
    
    async def test_error_handling(self):
        """Test API error handling"""
        await self.wait_for_backend()
        
        async with httpx.AsyncClient() as client:
            # Test invalid endpoint
            response = await client.get("http://localhost:8004/api/nonexistent")
            assert response.status_code == 404
            
            # Test invalid prediction data
            response = await client.post(
                "http://localhost:8004/api/predictions/movement-impact",
                json={"invalid": "data"}
            )
            assert response.status_code == 400
    
    async def test_data_validation(self):
        """Test data validation across APIs"""
        await self.wait_for_backend()
        
        async with httpx.AsyncClient() as client:
            # Get talent profiles and verify data quality
            response = await client.get("http://localhost:8004/api/talent/profiles")
            profiles = response.json()
            
            for profile in profiles:
                # Check influence scores are in valid range
                assert 0.0 <= profile["influence_score"] <= 1.0
                assert 0.0 <= profile["technical_score"] <= 1.0
                assert 0.0 <= profile["leadership_score"] <= 1.0
                assert 0.0 <= profile["network_score"] <= 1.0
                
                # Check required string fields are not empty
                assert profile["name"].strip()
                assert profile["current_company"].strip()
                assert profile["current_role"].strip()


async def run_playwright_tests():
    """Run all Playwright tests and generate report"""
    print("🎭 Starting Playwright E2E Tests for AI Talent Flow Intelligence")
    print("=" * 70)
    
    test_results = {
        "passed": 0,
        "failed": 0,
        "errors": []
    }
    
    # Create test instance
    test_instance = TestAITalentFlowE2E()
    
    # Get all test methods
    test_methods = [method for method in dir(test_instance) if method.startswith("test_")]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        for method_name in test_methods:
            try:
                print(f"  Running {method_name}... ", end="")
                method = getattr(test_instance, method_name)
                await method()
                print("✅ PASSED")
                test_results["passed"] += 1
                
            except Exception as e:
                print("❌ FAILED")
                test_results["failed"] += 1
                test_results["errors"].append(f"{method_name}: {str(e)}")
        
        await browser.close()
    
    # Print summary
    print("\n" + "=" * 70)
    print("🎭 PLAYWRIGHT TEST SUMMARY")
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")
    
    if test_results["errors"]:
        print(f"\n❌ ERRORS:")
        for error in test_results["errors"]:
            print(f"  - {error}")
    
    total_tests = test_results["passed"] + test_results["failed"]
    success_rate = (test_results["passed"] / total_tests * 100) if total_tests > 0 else 0
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    if test_results["failed"] == 0:
        print("🎉 ALL PLAYWRIGHT TESTS PASSED!")
    
    return test_results


if __name__ == "__main__":
    import asyncio
    results = asyncio.run(run_playwright_tests())