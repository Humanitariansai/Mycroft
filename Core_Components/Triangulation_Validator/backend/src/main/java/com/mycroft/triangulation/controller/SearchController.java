package com.mycroft.triangulation.controller;

import com.mycroft.triangulation.domain.Signal;
import com.mycroft.triangulation.repository.SignalRepository;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@RestController
@RequestMapping("/api/v1/search")
@Tag(name = "Search", description = "Advanced search and filtering capabilities")
public class SearchController {

    @Autowired
    private SignalRepository signalRepository;

    /**
     * Search signals by criteria
     */
    @PostMapping("/signals")
    @Operation(summary = "Search signals", description = "Advanced search with multiple filters")
    public ResponseEntity<Map<String, Object>> searchSignals(
            @RequestParam(required = false) String company,
            @RequestParam(required = false) String agentName,
            @RequestParam(required = false) String signalType,
            @RequestParam(required = false) Integer minConfidence,
            @RequestParam(required = false) Integer maxConfidence,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size) {
        try {
            log.info("Searching signals: company={}, agent={}, type={}", company, agentName, signalType);

            // Fetch all signals and filter
            List<Signal> signals = signalRepository.findAll();

            // Apply filters
            if (company != null && !company.isEmpty()) {
                signals = signals.stream()
                    .filter(s -> s.getCompanyName().equalsIgnoreCase(company))
                    .collect(Collectors.toList());
            }

            if (agentName != null && !agentName.isEmpty()) {
                signals = signals.stream()
                    .filter(s -> s.getAgentName().equalsIgnoreCase(agentName))
                    .collect(Collectors.toList());
            }

            if (signalType != null && !signalType.isEmpty()) {
                signals = signals.stream()
                    .filter(s -> s.getSignalType().equalsIgnoreCase(signalType))
                    .collect(Collectors.toList());
            }

            if (minConfidence != null) {
                signals = signals.stream()
                    .filter(s -> s.getConfidence() >= minConfidence)
                    .collect(Collectors.toList());
            }

            if (maxConfidence != null) {
                signals = signals.stream()
                    .filter(s -> s.getConfidence() <= maxConfidence)
                    .collect(Collectors.toList());
            }

            // Sort by date descending
            signals.sort((s1, s2) -> s2.getCreatedAt().compareTo(s1.getCreatedAt()));

            // Paginate
            int totalResults = signals.size();
            int totalPages = (totalResults + size - 1) / size;
            int startIdx = page * size;
            int endIdx = Math.min(startIdx + size, totalResults);

            List<Signal> pageResults = signals.subList(startIdx, endIdx);

            Map<String, Object> response = new HashMap<>();
            response.put("total_results", totalResults);
            response.put("page", page);
            response.put("size", size);
            response.put("total_pages", totalPages);
            response.put("signals", pageResults);

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Error searching signals: {}", e.getMessage(), e);
            Map<String, Object> error = new HashMap<>();
            error.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }

    /**
     * Get distinct companies
     */
    @GetMapping("/companies")
    @Operation(summary = "Get all companies", description = "Retrieve list of all companies with signals")
    public ResponseEntity<Map<String, Object>> getCompanies() {
        try {
            List<String> companies = signalRepository.findDistinctCompanies();

            Map<String, Object> response = new HashMap<>();
            response.put("total_companies", companies.size());
            response.put("companies", companies);

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Error getting companies: {}", e.getMessage(), e);
            Map<String, Object> error = new HashMap<>();
            error.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }

    /**
     * Get distinct agents
     */
    @GetMapping("/agents")
    @Operation(summary = "Get all agents", description = "Retrieve list of all agents that have submitted signals")
    public ResponseEntity<Map<String, Object>> getAgents() {
        try {
            List<Signal> allSignals = signalRepository.findAll();

            Set<String> agents = allSignals.stream()
                .map(Signal::getAgentName)
                .collect(Collectors.toSet());

            List<String> agentList = new ArrayList<>(agents);
            Collections.sort(agentList);

            Map<String, Object> response = new HashMap<>();
            response.put("total_agents", agentList.size());
            response.put("agents", agentList);

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Error getting agents: {}", e.getMessage(), e);
            Map<String, Object> error = new HashMap<>();
            error.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }

    /**
     * Get distinct signal types
     */
    @GetMapping("/types")
    @Operation(summary = "Get signal types", description = "Retrieve list of all signal types")
    public ResponseEntity<Map<String, Object>> getSignalTypes() {
        try {
            List<Signal> allSignals = signalRepository.findAll();

            Set<String> types = allSignals.stream()
                .map(Signal::getSignalType)
                .collect(Collectors.toSet());

            List<String> typeList = new ArrayList<>(types);
            Collections.sort(typeList);

            Map<String, Object> response = new HashMap<>();
            response.put("total_types", typeList.size());
            response.put("types", typeList);

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Error getting signal types: {}", e.getMessage(), e);
            Map<String, Object> error = new HashMap<>();
            error.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }

    /**
     * Get confidence distribution
     */
    @GetMapping("/confidence-distribution")
    @Operation(summary = "Get confidence distribution", description = "Analyze distribution of confidence scores")
    public ResponseEntity<Map<String, Object>> getConfidenceDistribution() {
        try {
            List<Signal> allSignals = signalRepository.findAll();

            // Create buckets: 0-20, 20-40, 40-60, 60-80, 80-100
            Map<String, Long> distribution = new HashMap<>();
            distribution.put("0-20", 0L);
            distribution.put("20-40", 0L);
            distribution.put("40-60", 0L);
            distribution.put("60-80", 0L);
            distribution.put("80-100", 0L);

            for (Signal signal : allSignals) {
                int confidence = signal.getConfidence();
                if (confidence < 20) distribution.put("0-20", distribution.get("0-20") + 1);
                else if (confidence < 40) distribution.put("20-40", distribution.get("20-40") + 1);
                else if (confidence < 60) distribution.put("40-60", distribution.get("40-60") + 1);
                else if (confidence < 80) distribution.put("60-80", distribution.get("60-80") + 1);
                else distribution.put("80-100", distribution.get("80-100") + 1);
            }

            double avgConfidence = allSignals.stream()
                .mapToInt(Signal::getConfidence)
                .average()
                .orElse(0);

            Map<String, Object> response = new HashMap<>();
            response.put("total_signals", allSignals.size());
            response.put("average_confidence", Math.round(avgConfidence * 100.0) / 100.0);
            response.put("distribution", distribution);

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Error getting confidence distribution: {}", e.getMessage(), e);
            Map<String, Object> error = new HashMap<>();
            error.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }

    /**
     * Get agent performance statistics
     */
    @GetMapping("/agent-stats")
    @Operation(summary = "Get agent statistics", description = "Analyze agent performance and signal distribution")
    public ResponseEntity<Map<String, Object>> getAgentStats() {
        try {
            List<Signal> allSignals = signalRepository.findAll();

            // Group by agent
            Map<String, List<Signal>> byAgent = allSignals.stream()
                .collect(Collectors.groupingBy(Signal::getAgentName));

            Map<String, Map<String, Object>> agentStats = new HashMap<>();

            for (Map.Entry<String, List<Signal>> entry : byAgent.entrySet()) {
                String agent = entry.getKey();
                List<Signal> signals = entry.getValue();

                double avgConfidence = signals.stream()
                    .mapToInt(Signal::getConfidence)
                    .average()
                    .orElse(0);

                Map<String, Object> stats = new HashMap<>();
                stats.put("signal_count", signals.size());
                stats.put("average_confidence", Math.round(avgConfidence * 100.0) / 100.0);
                stats.put("company_count", signals.stream()
                    .map(Signal::getCompanyName)
                    .distinct()
                    .count());

                agentStats.put(agent, stats);
            }

            Map<String, Object> response = new HashMap<>();
            response.put("total_agents", agentStats.size());
            response.put("agent_statistics", agentStats);

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Error getting agent stats: {}", e.getMessage(), e);
            Map<String, Object> error = new HashMap<>();
            error.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }
}
