package com.mycroft.triangulation.service;

import com.mycroft.triangulation.domain.Signal;
import com.mycroft.triangulation.domain.TriangulationResult;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class TriangulationEngineTest {

    private TriangulationEngine engine;

    @BeforeEach
    void setUp() {
        engine = new TriangulationEngine();
    }

    @Test
    void testTriangulate_UnanimousAgreement() {
        // Arrange: All 3 agents agree with high confidence
        List<Signal> signals = new ArrayList<>();
        signals.add(createSignal("OpenAI", "Talent Agent", "Hired senior researchers", 85));
        signals.add(createSignal("OpenAI", "Patent Agent", "Filed patents", 80));
        signals.add(createSignal("OpenAI", "News Agent", "Raised funding", 90));

        // Act
        TriangulationResult result = engine.triangulate(signals);

        // Assert
        assertEquals("OpenAI", result.getCompanyName());
        assertEquals(3, result.getAgentsAgreeing());
        assertEquals(3, result.getTotalAgentsReporting());
        assertTrue(result.getTriangulatedConfidence() > result.getAverageConfidence());
        assertEquals("UNANIMOUS", result.getConsensusLevel());
        assertEquals("TRUST_SIGNAL", result.getRecommendation());
        assertEquals("LOW", result.getRiskLevel());
    }

    @Test
    void testTriangulate_MajorityAgreement() {
        // Arrange: 2/3 agents agree
        List<Signal> signals = new ArrayList<>();
        signals.add(createSignal("Anthropic", "Talent Agent", "Strong team", 85));
        signals.add(createSignal("Anthropic", "Patent Agent", "Strong patents", 80));
        signals.add(createSignal("Anthropic", "News Agent", "Regulatory risk", 30));

        // Act
        TriangulationResult result = engine.triangulate(signals);

        // Assert
        assertEquals(2, result.getAgentsAgreeing());
        assertEquals(3, result.getTotalAgentsReporting());
        assertEquals("HIGH", result.getConsensusLevel());
    }

    @Test
    void testTriangulate_ConflictingSignals() {
        // Arrange: 1/3 agents agree on positive, 2/3 on negative
        List<Signal> signals = new ArrayList<>();
        signals.add(createSignal("xAI", "Talent Agent", "Losing people", 25));
        signals.add(createSignal("xAI", "Patent Agent", "Patent filed", 35));
        signals.add(createSignal("xAI", "News Agent", "Major win", 85));

        // Act
        TriangulationResult result = engine.triangulate(signals);

        // Assert
        assertEquals("CONFLICTING", result.getConsensusLevel());
        assertEquals("INVESTIGATE", result.getRecommendation());
        assertEquals("HIGH", result.getRiskLevel());
    }

    @Test
    void testTriangulate_SingleSignal() {
        // Arrange: Only 1 agent reporting
        List<Signal> signals = new ArrayList<>();
        signals.add(createSignal("Meta", "News Agent", "AI investment", 75));

        // Act
        TriangulationResult result = engine.triangulate(signals);

        // Assert
        assertEquals(1, result.getTotalAgentsReporting());
        assertEquals("WEAK", result.getConsensusLevel());
        assertEquals("INSUFFICIENT_DATA", result.getRecommendation());
    }

    @Test
    void testTriangulate_NoSignals() {
        // Arrange: Empty signal list
        List<Signal> signals = new ArrayList<>();

        // Act
        TriangulationResult result = engine.triangulate(signals);

        // Assert
        assertEquals("NO_DATA", result.getConsensusLevel());
        assertEquals("HIGH", result.getRiskLevel());
    }

    @Test
    void testTriangulationConfidenceBoost() {
        // Arrange: Signals with mid-range confidence
        List<Signal> signals = new ArrayList<>();
        signals.add(createSignal("Company", "Agent1", "Signal1", 65));
        signals.add(createSignal("Company", "Agent2", "Signal2", 65));
        signals.add(createSignal("Company", "Agent3", "Signal3", 65));

        // Act
        TriangulationResult result = engine.triangulate(signals);

        // Assert: Triangulated confidence should be higher than average
        int average = result.getAverageConfidence();
        int triangulated = result.getTriangulatedConfidence();
        assertTrue(triangulated > average,
            String.format("Triangulated (%d) should be > average (%d)", triangulated, average));
    }

    // Helper method to create test signals
    private Signal createSignal(String company, String agent, String text, Integer confidence) {
        return Signal.builder()
            .companyName(company)
            .agentName(agent)
            .signalText(text)
            .confidence(confidence)
            .signalType(inferType(agent))
            .createdAt(LocalDateTime.now())
            .build();
    }

    private String inferType(String agentName) {
        if (agentName.contains("Talent")) return "talent";
        if (agentName.contains("Patent")) return "patent";
        if (agentName.contains("News")) return "news";
        return "other";
    }
}
