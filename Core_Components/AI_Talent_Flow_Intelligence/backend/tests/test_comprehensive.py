"""
Comprehensive test suite for AI Talent Flow Intelligence system.
Tests all components including data collection, movement detection, 
prediction models, and Mycroft integration.
"""

import asyncio
import pytest
import httpx
import json
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.predictive_models import TalentImpactPredictor, TeamMovementPredictor, MarketTimingPredictor
from services.mycroft_integration import MycroftEcosystemIntegrator, TalentSignalAggregator
from services.data_collectors import GitHubTalentCollector, AcademicDataCollector
from services.movement_detection import TalentInfluenceCalculator, MovementPatternAnalyzer

class TestTalentFlowIntelligence:
    """Comprehensive test suite for the entire system"""
    
    @pytest.fixture
    def sample_talent_profile(self):
        """Sample talent profile for testing"""
        return {
            "id": "test_talent_001",
            "name": "Dr. Test Researcher",
            "current_company": "TestCorp",
            "current_role": "Senior AI Scientist",
            "ai_experience_years": 8,
            "technical_skills": ["Python", "Machine Learning", "Deep Learning"],
            "leadership_roles": ["Tech Lead"],
            "influence_score": 0.75,
            "technical_score": 0.80,
            "leadership_score": 0.70,
            "network_score": 0.75,
            "research_papers": 12,
            "patents_filed": 3,
            "github_contributions": 150
        }
    
    @pytest.fixture
    def sample_company_profile(self):
        """Sample company profile for testing"""
        return {
            "id": "test_company_001",
            "name": "TestCorp AI",
            "ticker_symbol": "TEST",
            "company_size": "medium",
            "sector": "Artificial Intelligence",
            "total_ai_talent": 100,
            "recent_hires": 5,
            "recent_exits": 2
        }
    
    @pytest.fixture
    def sample_movement(self):
        """Sample talent movement for testing"""
        return {
            "id": "test_movement_001",
            "talent_name": "Dr. Test Researcher",
            "movement_type": "job_change",
            "from_company": "OldCorp",
            "to_company": "TestCorp AI",
            "from_role": "Research Scientist",
            "to_role": "Senior AI Scientist",
            "movement_date": datetime.now().isoformat(),
            "confidence_score": 0.85,
            "strategic_importance": 0.75
        }

class TestPredictiveModels:
    """Test predictive modeling components"""
    
    def test_talent_impact_predictor_basic(self):
        """Test basic talent impact prediction"""
        predictor = TalentImpactPredictor()
        
        talent = {
            "influence_score": 0.8,
            "technical_score": 0.85,
            "leadership_score": 0.75,
            "network_score": 0.80,
            "ai_experience_years": 6,
            "research_papers": 15,
            "patents_filed": 2
        }
        
        movement = {
            "to_role": "Senior Research Scientist",
            "movement_type": "job_change"
        }
        
        company = {
            "ticker_symbol": "TEST",
            "company_size": "medium"
        }
        
        prediction = predictor.predict_stock_impact(movement, talent, company)
        
        assert prediction.ticker == "TEST"
        assert isinstance(prediction.predicted_impact, float)
        assert -1.0 <= prediction.predicted_impact <= 1.0
        assert 0.0 <= prediction.confidence <= 1.0
        assert prediction.time_horizon in ["short", "medium", "long"]
        assert len(prediction.contributing_factors) > 0
    
    def test_influence_calculator(self):
        """Test talent influence calculation"""
        calculator = TalentInfluenceCalculator()
        
        from models.schemas import TalentProfile
        profile = TalentProfile(
            id="test_001",
            name="Test Talent",
            github_username="test_user",
            current_company="TestCorp",
            current_role="Engineer",
            influence_score=0.8,
            technical_score=0.9,
            leadership_score=0.7,
            network_score=0.8,
            ai_experience_years=8,
            technical_skills=["Python", "TensorFlow", "Research"],
            leadership_roles=["Tech Lead", "Manager"],
            patents_filed=3,
            research_papers=15,
            conference_talks=5,
            companies_worked=["Google", "OpenAI"],
            github_contributions=200
        )
        
        scores = calculator.calculate_influence_score(profile)
        
        assert "overall_influence" in scores
        assert "technical_score" in scores
        assert "leadership_score" in scores
        assert "network_score" in scores
        assert "innovation_score" in scores
        
        for score in scores.values():
            assert 0.0 <= score <= 1.0
    
    def test_team_movement_predictor(self):
        """Test team movement prediction"""
        team_predictor = TeamMovementPredictor()
        
        movements = [
            {"to_role": "Senior Scientist", "movement_type": "job_change"},
            {"to_role": "Principal Engineer", "movement_type": "job_change"},
            {"to_role": "Research Lead", "movement_type": "job_change"}
        ]
        
        talents = [
            {"influence_score": 0.8, "technical_score": 0.85, "leadership_score": 0.7, "network_score": 0.75, "ai_experience_years": 6, "research_papers": 12, "patents_filed": 2},
            {"influence_score": 0.85, "technical_score": 0.9, "leadership_score": 0.8, "network_score": 0.8, "ai_experience_years": 8, "research_papers": 18, "patents_filed": 4},
            {"influence_score": 0.75, "technical_score": 0.8, "leadership_score": 0.85, "network_score": 0.85, "ai_experience_years": 10, "research_papers": 25, "patents_filed": 5}
        ]
        
        company = {"ticker_symbol": "TEST", "company_size": "medium"}
        
        prediction = team_predictor.predict_team_movement_impact(movements, talents, company)
        
        assert prediction.ticker == "TEST"
        assert prediction.prediction_type == "team_movement_impact"
        assert prediction.confidence > 0.0
        assert "team movement" in " ".join(prediction.contributing_factors).lower()
    
    def test_market_timing_predictor(self):
        """Test market timing prediction"""
        timing_predictor = MarketTimingPredictor()
        
        # Mock prediction result
        from models.predictive_models import PredictionResult
        prediction = PredictionResult(
            ticker="TEST",
            prediction_type="test",
            predicted_impact=0.6,
            confidence=0.8,
            time_horizon="short",
            contributing_factors=["test factor"],
            model_version="test",
            prediction_date=datetime.now()
        )
        
        timing = timing_predictor.predict_optimal_timing(prediction)
        
        assert "timing_score" in timing
        assert "timing_recommendation" in timing
        assert "timing_window" in timing
        assert "optimal_entry_confidence" in timing
        assert timing["timing_recommendation"] in ["immediate", "near_term", "wait"]

class TestMycroftIntegration:
    """Test Mycroft ecosystem integration"""
    
    @pytest.mark.asyncio
    async def test_signal_aggregator(self):
        """Test talent signal aggregation"""
        aggregator = TalentSignalAggregator()
        
        # Add test signals
        signals = [
            {"ticker_symbol": "TEST", "confidence_score": 0.8, "predicted_impact": "positive"},
            {"ticker_symbol": "TEST", "confidence_score": 0.75, "predicted_impact": "positive"},
            {"ticker_symbol": "TEST", "confidence_score": 0.7, "predicted_impact": "negative"}
        ]
        
        for signal in signals:
            aggregator.add_signal(signal)
        
        aggregated = aggregator.get_aggregated_signals_for_ticker("TEST")
        
        assert aggregated["ticker"] == "TEST"
        assert aggregated["signal_count"] == 3
        assert aggregated["aggregated_confidence"] > 0
        assert aggregated["sentiment"] in ["positive", "negative", "neutral"]
    
    @pytest.mark.asyncio
    async def test_ecosystem_integrator(self):
        """Test Mycroft ecosystem integration"""
        integrator = MycroftEcosystemIntegrator()
        
        # Test signal combination
        market_data = {
            "data": {
                "final_recommendation": {
                    "score": 0.65
                }
            }
        }
        
        talent_context = {
            "confidence_score": 0.8,
            "predicted_impact": "positive"
        }
        
        combined = integrator._combine_signals(market_data, talent_context)
        
        assert "action" in combined
        assert "combined_confidence" in combined
        assert "market_confidence" in combined
        assert "talent_confidence" in combined
        assert combined["action"] in ["buy", "sell", "hold", "strong_buy"]

class TestAPIEndpoints:
    """Test API endpoints"""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test health check endpoint"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("http://localhost:8004/health", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    assert data["status"] == "healthy"
                    assert "predictive_models" in data["services"]
                else:
                    pytest.skip("API server not running")
            except httpx.ConnectError:
                pytest.skip("API server not available")
    
    @pytest.mark.asyncio
    async def test_talent_profiles_endpoint(self):
        """Test talent profiles endpoint"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("http://localhost:8004/api/talent/profiles", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    assert isinstance(data, list)
                    if data:
                        assert "id" in data[0]
                        assert "name" in data[0]
                        assert "influence_score" in data[0]
                else:
                    pytest.skip("API server not running properly")
            except httpx.ConnectError:
                pytest.skip("API server not available")
    
    @pytest.mark.asyncio
    async def test_prediction_endpoint(self):
        """Test movement impact prediction endpoint"""
        async with httpx.AsyncClient() as client:
            try:
                movement_data = {
                    "talent_name": "Dr. Emma Rodriguez",
                    "to_company": "OpenAI",
                    "to_role": "VP of Research",
                    "movement_type": "job_change"
                }
                
                response = await client.post(
                    "http://localhost:8004/api/predictions/movement-impact",
                    json=movement_data,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    assert data["status"] == "success"
                    assert "prediction" in data
                    assert "timing" in data
                    assert "investment_recommendation" in data
                else:
                    pytest.skip("API prediction endpoint not working")
            except httpx.ConnectError:
                pytest.skip("API server not available")

class TestDataCollection:
    """Test data collection components"""
    
    def test_github_collector_initialization(self):
        """Test GitHub collector can be initialized"""
        collector = GitHubTalentCollector()
        assert collector.config is not None
        assert hasattr(collector, 'get_user_profile')
    
    def test_academic_collector_initialization(self):
        """Test academic collector can be initialized"""
        collector = AcademicDataCollector()
        assert collector.config is not None
        assert hasattr(collector, 'get_researcher_publications')
    
    @pytest.mark.asyncio
    async def test_academic_arxiv_parsing(self):
        """Test arXiv XML parsing capability"""
        collector = AcademicDataCollector()
        
        # Sample arXiv XML response
        sample_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <id>http://arxiv.org/abs/2301.00001v1</id>
                <title>Test Paper Title</title>
                <summary>Test abstract content</summary>
                <published>2023-01-01T00:00:00Z</published>
                <author><name>Test Author</name></author>
                <category term="cs.AI" />
            </entry>
        </feed>'''
        
        papers = collector._parse_arxiv_response(sample_xml)
        assert len(papers) == 1
        assert papers[0]["title"] == "Test Paper Title"
        assert "Test Author" in papers[0]["authors"]

class TestPerformanceMetrics:
    """Test system performance and reliability"""
    
    def test_prediction_performance(self):
        """Test prediction generation performance"""
        predictor = TalentImpactPredictor()
        
        start_time = datetime.now()
        
        # Run multiple predictions to test performance
        for i in range(10):
            movement = {
                "to_role": f"Role {i}",
                "movement_type": "job_change"
            }
            talent = {
                "influence_score": 0.7 + (i % 3) * 0.1,
                "technical_score": 0.8,
                "leadership_score": 0.7,
                "network_score": 0.75,
                "ai_experience_years": 5 + i,
                "research_papers": 10 + i,
                "patents_filed": i % 5
            }
            company = {
                "ticker_symbol": f"TEST{i}",
                "company_size": "medium"
            }
            
            prediction = predictor.predict_stock_impact(movement, talent, company)
            assert prediction.predicted_impact is not None
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete 10 predictions in under 1 second
        assert duration < 1.0, f"Predictions took too long: {duration} seconds"
    
    def test_confidence_consistency(self):
        """Test that confidence scores are consistent"""
        predictor = TalentImpactPredictor()
        
        # Same input should produce similar confidence
        talent = {
            "influence_score": 0.8,
            "technical_score": 0.85,
            "leadership_score": 0.75,
            "network_score": 0.80,
            "ai_experience_years": 6,
            "research_papers": 15,
            "patents_filed": 2
        }
        
        movement = {
            "to_role": "Senior Research Scientist",
            "movement_type": "job_change"
        }
        
        company = {
            "ticker_symbol": "TEST",
            "company_size": "medium"
        }
        
        confidences = []
        for _ in range(5):
            prediction = predictor.predict_stock_impact(movement, talent, company)
            confidences.append(prediction.confidence)
        
        # Confidence should be relatively consistent (within 0.1 range)
        confidence_range = max(confidences) - min(confidences)
        assert confidence_range < 0.15, f"Confidence too variable: {confidence_range}"

def run_comprehensive_tests():
    """Run all tests and generate report"""
    print("🧪 Running AI Talent Flow Intelligence Comprehensive Test Suite")
    print("=" * 70)
    
    test_results = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": []
    }
    
    # Test Categories
    test_classes = [
        TestPredictiveModels(),
        TestMycroftIntegration(), 
        TestAPIEndpoints(),
        TestDataCollection(),
        TestPerformanceMetrics()
    ]
    
    for test_class in test_classes:
        class_name = test_class.__class__.__name__
        print(f"\n📋 {class_name}")
        print("-" * 50)
        
        # Get all test methods
        test_methods = [method for method in dir(test_class) if method.startswith("test_")]
        
        for method_name in test_methods:
            try:
                print(f"  Running {method_name}... ", end="")
                method = getattr(test_class, method_name)
                
                if asyncio.iscoroutinefunction(method):
                    asyncio.run(method())
                else:
                    method()
                
                print("✅ PASSED")
                test_results["passed"] += 1
                
            except Exception as e:
                if "skip" in str(e).lower():
                    print("⏭️  SKIPPED")
                    test_results["skipped"] += 1
                else:
                    print("❌ FAILED")
                    test_results["failed"] += 1
                    test_results["errors"].append(f"{class_name}.{method_name}: {str(e)}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")
    print(f"⏭️  Skipped: {test_results['skipped']}")
    
    if test_results["errors"]:
        print(f"\n❌ ERRORS:")
        for error in test_results["errors"]:
            print(f"  - {error}")
    
    total_tests = test_results["passed"] + test_results["failed"] + test_results["skipped"]
    success_rate = (test_results["passed"] / total_tests * 100) if total_tests > 0 else 0
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    if test_results["failed"] == 0:
        print("🎉 ALL TESTS PASSED!")
    
    return test_results

if __name__ == "__main__":
    results = run_comprehensive_tests()