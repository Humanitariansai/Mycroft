package com.mycroft.triangulation.service;

import com.mycroft.triangulation.domain.Signal;
import com.mycroft.triangulation.repository.SignalRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;

/**
 * Signal Aggregator: Fetch and aggregate signals from other Mycroft agents
 */
@Slf4j
@Service
public class SignalAggregator {

    @Autowired
    private SignalRepository signalRepository;

    @Value("${signal.lookback.days:7}")
    private int lookbackDays;

    /**
     * Fetch all signals for a company from the past N days
     */
    public List<Signal> aggregateSignals(String companyName) {
        LocalDateTime cutoffDate = LocalDateTime.now().minusDays(lookbackDays);

        List<Signal> signals = signalRepository.findRecentSignalsForCompany(companyName, cutoffDate);

        log.info("Aggregated {} signals for {} from past {} days",
            signals.size(), companyName, lookbackDays);

        return signals;
    }

    /**
     * Fetch signals by type (talent, patent, news, etc.)
     */
    public List<Signal> getSignalsByType(String companyName, String signalType) {
        return signalRepository.findByCompanyAndType(companyName, signalType);
    }

    /**
     * Get summary statistics for a company's signals
     */
    public Map<String, Object> getSignalSummary(String companyName) {
        List<Signal> signals = aggregateSignals(companyName);

        Map<String, Object> summary = new HashMap<>();
        summary.put("company", companyName);
        summary.put("totalSignals", signals.size());
        summary.put("averageConfidence", signals.stream()
            .mapToInt(Signal::getConfidence)
            .average()
            .orElse(0));

        // Group by agent
        Map<String, Long> byAgent = signals.stream()
            .collect(java.util.stream.Collectors.groupingBy(
                Signal::getAgentName,
                java.util.stream.Collectors.counting()
            ));
        summary.put("byAgent", byAgent);

        // Group by type
        Map<String, Long> byType = signals.stream()
            .collect(java.util.stream.Collectors.groupingBy(
                Signal::getSignalType,
                java.util.stream.Collectors.counting()
            ));
        summary.put("byType", byType);

        return summary;
    }

    /**
     * Ingest a new signal from an agent
     */
    public Signal ingestSignal(String companyName, String agentName, String signalText,
                               Integer confidence, String signalType) {
        Signal signal = Signal.builder()
            .companyName(companyName)
            .agentName(agentName)
            .signalText(signalText)
            .confidence(confidence)
            .signalType(signalType)
            .createdAt(LocalDateTime.now())
            .build();

        Signal saved = signalRepository.save(signal);
        log.info("Ingested signal from {} for {}: {}", agentName, companyName, signalText);
        return saved;
    }
}
