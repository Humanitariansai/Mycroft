package com.mycroft.triangulation.client;

import com.mycroft.triangulation.domain.Signal;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

class MockSignalProviderTest {

    private MockSignalProvider provider;

    @BeforeEach
    void setUp() {
        provider = new MockSignalProvider();
    }

    @Test
    void testGetSignalsForCompany_OpenAI() {
        List<Signal> signals = provider.getSignalsForCompany("OpenAI");

        assertNotNull(signals);
        assertEquals(4, signals.size());
        assertTrue(signals.stream().allMatch(s -> s.getCompanyName().equals("OpenAI")));
    }

    @Test
    void testGetSignalsForCompany_Anthropic() {
        List<Signal> signals = provider.getSignalsForCompany("Anthropic");

        assertNotNull(signals);
        assertEquals(4, signals.size());
        assertTrue(signals.stream().anyMatch(s -> s.getSignalType().equals("talent")));
        assertTrue(signals.stream().anyMatch(s -> s.getSignalType().equals("patent")));
    }

    @Test
    void testGetSignalsForCompany_NonExistent() {
        List<Signal> signals = provider.getSignalsForCompany("NonExistentCompany");

        assertNotNull(signals);
        assertTrue(signals.isEmpty());
    }

    @Test
    void testGetAllCompanies() {
        List<String> companies = provider.getAllCompanies();

        assertNotNull(companies);
        assertEquals(5, companies.size());
        assertTrue(companies.contains("OpenAI"));
        assertTrue(companies.contains("Anthropic"));
        assertTrue(companies.contains("Google"));
        assertTrue(companies.contains("Meta"));
        assertTrue(companies.contains("Microsoft"));
    }

    @Test
    void testAddSignal() {
        Signal newSignal = Signal.builder()
            .companyName("NewCompany")
            .agentName("Test Agent")
            .signalText("Test signal")
            .confidence(70)
            .signalType("news")
            .build();

        provider.addSignal(newSignal);

        List<Signal> signals = provider.getSignalsForCompany("NewCompany");
        assertEquals(1, signals.size());
        assertEquals("Test signal", signals.get(0).getSignalText());
    }

    @Test
    void testGetSignalsByType() {
        List<Signal> talentSignals = provider.getSignalsByType("OpenAI", "talent");

        assertEquals(1, talentSignals.size());
        assertEquals("talent", talentSignals.get(0).getSignalType());
    }

    @Test
    void testGetSignalsByType_MultipleOfType() {
        List<Signal> patentSignals = provider.getSignalsByType("Microsoft", "patent");

        assertEquals(1, patentSignals.size());
        assertTrue(patentSignals.stream().allMatch(s -> s.getSignalType().equals("patent")));
    }

    @Test
    void testGetSignalsAboveConfidence() {
        List<Signal> signals = provider.getSignalsAboveConfidence("OpenAI", 80);

        assertTrue(signals.size() >= 1);
        assertTrue(signals.stream().allMatch(s -> s.getConfidence() >= 80));
    }

    @Test
    void testGetSignalsAboveConfidence_HighThreshold() {
        List<Signal> signals = provider.getSignalsAboveConfidence("Meta", 50);

        assertTrue(signals.size() > 0);
        assertTrue(signals.stream().allMatch(s -> s.getConfidence() >= 50));
    }

    @Test
    void testClearAll() {
        provider.clearAll();

        List<String> companies = provider.getAllCompanies();
        assertTrue(companies.isEmpty());
    }

    @Test
    void testReset() {
        provider.clearAll();
        assertTrue(provider.getAllCompanies().isEmpty());

        provider.reset();

        List<String> companies = provider.getAllCompanies();
        assertEquals(5, companies.size());
    }

    @Test
    void testGetSignalsForCompanies() {
        List<String> companies = List.of("OpenAI", "Google", "Meta");
        Map<String, List<Signal>> results = provider.getSignalsForCompanies(companies);

        assertEquals(3, results.size());
        assertTrue(results.containsKey("OpenAI"));
        assertTrue(results.containsKey("Google"));
        assertTrue(results.containsKey("Meta"));
        assertEquals(4, results.get("OpenAI").size());
    }

    @Test
    void testGetStatistics() {
        Map<String, Object> stats = provider.getStatistics();

        assertNotNull(stats);
        assertEquals(5, stats.get("totalCompanies"));
        int totalSignals = (int) stats.get("totalSignals");
        assertTrue(totalSignals >= 20, "Expected at least 20 signals, got " + totalSignals);
        assertTrue(stats.containsKey("companies"));
    }

    @Test
    void testConfidenceScores_Meta_Negative() {
        List<Signal> signals = provider.getSignalsForCompany("Meta");

        // Meta should have mixed signals with some low confidence
        assertTrue(signals.stream().anyMatch(s -> s.getConfidence() <= 40));
    }

    @Test
    void testConfidenceScores_Microsoft_Positive() {
        List<Signal> signals = provider.getSignalsForCompany("Microsoft");

        // Microsoft should have mostly high confidence signals
        assertTrue(signals.stream().anyMatch(s -> s.getConfidence() >= 85));
    }
}
