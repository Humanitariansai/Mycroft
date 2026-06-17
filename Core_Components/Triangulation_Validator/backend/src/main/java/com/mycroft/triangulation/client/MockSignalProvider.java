package com.mycroft.triangulation.client;

import com.mycroft.triangulation.domain.Signal;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;

/**
 * Mock signal provider for testing without actual agent APIs
 */
@Slf4j
@Service
public class MockSignalProvider {

    private final Map<String, List<Signal>> mockSignalsDb = new HashMap<>();

    public MockSignalProvider() {
        initializeMockData();
    }

    /**
     * Initialize mock signal database with test companies
     */
    private void initializeMockData() {
        // OpenAI mock signals
        mockSignalsDb.put("OpenAI", Arrays.asList(
            createMockSignal("OpenAI", "Talent Agent", "Hired 50 senior researchers", 85, "talent"),
            createMockSignal("OpenAI", "Patent Agent", "Filed 15 new patents", 80, "patent"),
            createMockSignal("OpenAI", "News Agent", "Closed Series C funding", 90, "news"),
            createMockSignal("OpenAI", "Market Agent", "Stock price up 25%", 75, "market")
        ));

        // Anthropic mock signals
        mockSignalsDb.put("Anthropic", Arrays.asList(
            createMockSignal("Anthropic", "Talent Agent", "Strong hiring momentum", 85, "talent"),
            createMockSignal("Anthropic", "Patent Agent", "AI model patent filed", 80, "patent"),
            createMockSignal("Anthropic", "News Agent", "Partnership with AWS", 88, "news"),
            createMockSignal("Anthropic", "Regulatory Agent", "Compliance review passed", 70, "regulatory")
        ));

        // Google mock signals
        mockSignalsDb.put("Google", Arrays.asList(
            createMockSignal("Google", "Patent Agent", "Quantum computing patent", 75, "patent"),
            createMockSignal("Google", "News Agent", "Cloud division growth", 80, "news"),
            createMockSignal("Google", "Market Agent", "Revenue up 15% YoY", 85, "market"),
            createMockSignal("Google", "Regulatory Agent", "Antitrust review ongoing", 65, "regulatory")
        ));

        // Meta mock signals
        mockSignalsDb.put("Meta", Arrays.asList(
            createMockSignal("Meta", "Talent Agent", "Layoffs and restructuring", 35, "talent"),
            createMockSignal("Meta", "Patent Agent", "VR/AR patents filed", 70, "patent"),
            createMockSignal("Meta", "News Agent", "Metaverse investment questioned", 40, "news"),
            createMockSignal("Meta", "Market Agent", "Stock volatility high", 55, "market")
        ));

        // Microsoft mock signals
        mockSignalsDb.put("Microsoft", Arrays.asList(
            createMockSignal("Microsoft", "Talent Agent", "AI talent acquisition", 82, "talent"),
            createMockSignal("Microsoft", "Patent Agent", "Cloud infrastructure patents", 78, "patent"),
            createMockSignal("Microsoft", "News Agent", "Azure revenue surge", 85, "news"),
            createMockSignal("Microsoft", "Market Agent", "Stock hit new high", 88, "market"),
            createMockSignal("Microsoft", "Regulatory Agent", "No major concerns", 75, "regulatory")
        ));

        log.info("Initialized mock signal database with {} companies", mockSignalsDb.size());
    }

    /**
     * Get mock signals for a company
     */
    public List<Signal> getSignalsForCompany(String companyName) {
        List<Signal> signals = mockSignalsDb.getOrDefault(companyName, new ArrayList<>());
        log.debug("Retrieved {} mock signals for {}", signals.size(), companyName);
        return signals;
    }

    /**
     * Get mock signals for multiple companies
     */
    public Map<String, List<Signal>> getSignalsForCompanies(List<String> companies) {
        Map<String, List<Signal>> result = new HashMap<>();
        for (String company : companies) {
            result.put(company, getSignalsForCompany(company));
        }
        return result;
    }

    /**
     * Get all available companies
     */
    public List<String> getAllCompanies() {
        return new ArrayList<>(mockSignalsDb.keySet());
    }

    /**
     * Add mock signal to database
     */
    public void addSignal(Signal signal) {
        String company = signal.getCompanyName();
        List<Signal> signals = mockSignalsDb.computeIfAbsent(company, k -> new ArrayList<>());
        signals.add(signal);
        log.info("Added mock signal for {} from {} agent", company, signal.getAgentName());
    }

    /**
     * Clear all mock signals for testing
     */
    public void clearAll() {
        mockSignalsDb.clear();
        log.info("Cleared all mock signals");
    }

    /**
     * Reset to default mock data
     */
    public void reset() {
        clearAll();
        initializeMockData();
        log.info("Reset mock signals to default state");
    }

    /**
     * Create a mock signal
     */
    private Signal createMockSignal(String company, String agent, String text,
                                   Integer confidence, String type) {
        return Signal.builder()
            .companyName(company)
            .agentName(agent)
            .signalText(text)
            .confidence(confidence)
            .signalType(type)
            .createdAt(LocalDateTime.now())
            .build();
    }

    /**
     * Get signals by type for a company
     */
    public List<Signal> getSignalsByType(String companyName, String signalType) {
        List<Signal> companySignals = getSignalsForCompany(companyName);
        List<Signal> filtered = new ArrayList<>();
        for (Signal signal : companySignals) {
            if (signalType.equalsIgnoreCase(signal.getSignalType())) {
                filtered.add(signal);
            }
        }
        return filtered;
    }

    /**
     * Get signals with minimum confidence
     */
    public List<Signal> getSignalsAboveConfidence(String companyName, Integer minConfidence) {
        List<Signal> companySignals = getSignalsForCompany(companyName);
        List<Signal> filtered = new ArrayList<>();
        for (Signal signal : companySignals) {
            if (signal.getConfidence() >= minConfidence) {
                filtered.add(signal);
            }
        }
        return filtered;
    }

    /**
     * Statistics about mock data
     */
    public Map<String, Object> getStatistics() {
        Map<String, Object> stats = new HashMap<>();
        stats.put("totalCompanies", mockSignalsDb.size());
        stats.put("totalSignals", mockSignalsDb.values().stream().mapToInt(List::size).sum());
        stats.put("companies", new ArrayList<>(mockSignalsDb.keySet()));
        return stats;
    }
}
