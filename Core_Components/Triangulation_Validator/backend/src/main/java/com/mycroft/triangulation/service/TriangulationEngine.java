package com.mycroft.triangulation.service;

import com.mycroft.triangulation.domain.Signal;
import com.mycroft.triangulation.domain.TriangulationResult;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Triangulation Engine: Apply consensus logic to validate agent signals
 *
 * Based on Computational Finance textbook triangulation heuristic:
 * If each agent is ~85% accurate independently, consensus validation
 * improves combined accuracy through majority voting.
 */
@Slf4j
@Service
public class TriangulationEngine {

    /**
     * Triangulate signals from multiple agents for a company
     *
     * @param signals List of signals from different agents
     * @return TriangulationResult with consensus, confidence, recommendation
     */
    public TriangulationResult triangulate(List<Signal> signals) {
        if (signals == null || signals.isEmpty()) {
            return buildWeakSignalResult(signals);
        }

        // Group signals by direction (positive/negative/neutral)
        Map<String, List<Signal>> signalsByDirection = groupSignalsByDirection(signals);

        // Calculate agreement statistics
        String dominantDirection = getDominantDirection(signalsByDirection);
        int agentsAgreeing = signalsByDirection.getOrDefault(dominantDirection, new ArrayList<>()).size();
        int totalAgents = signals.size();

        // Calculate confidence scores
        double averageConfidence = calculateAverageConfidence(signals);
        double triangulatedConfidence = calculateTriangulatedConfidence(
            agentsAgreeing, totalAgents, averageConfidence
        );

        // Determine consensus level and recommendation
        String consensusLevel = determineConsensusLevel(agentsAgreeing, totalAgents, signalsByDirection);
        String recommendation = determineRecommendation(consensusLevel, agentsAgreeing, totalAgents);
        String riskLevel = determineRiskLevel(consensusLevel, triangulatedConfidence);

        log.info("Triangulation for {}: {} agents agree on {} with confidence {}%",
            signals.get(0).getCompanyName(), agentsAgreeing, dominantDirection, (int) triangulatedConfidence);

        return TriangulationResult.builder()
            .companyName(signals.get(0).getCompanyName())
            .consensusLevel(consensusLevel)
            .agentsAgreeing(agentsAgreeing)
            .totalAgentsReporting(totalAgents)
            .averageConfidence((int) averageConfidence)
            .triangulatedConfidence((int) triangulatedConfidence)
            .signalDirection(dominantDirection)
            .recommendation(recommendation)
            .riskLevel(riskLevel)
            .signalSummary(serializeSignals(signals))
            .createdAt(LocalDateTime.now())
            .build();
    }

    /**
     * Group signals by their direction (positive, negative, neutral)
     */
    private Map<String, List<Signal>> groupSignalsByDirection(List<Signal> signals) {
        Map<String, List<Signal>> grouped = new HashMap<>();

        for (Signal signal : signals) {
            String direction = classifySignalDirection(signal.getConfidence());
            grouped.computeIfAbsent(direction, k -> new ArrayList<>()).add(signal);
        }

        return grouped;
    }

    /**
     * Classify signal as positive, negative, or neutral based on confidence
     * and signal type
     */
    private String classifySignalDirection(Integer confidence) {
        // Simplified: high confidence = positive, low confidence = negative
        if (confidence >= 70) return "POSITIVE";
        if (confidence <= 40) return "NEGATIVE";
        return "NEUTRAL";
    }

    /**
     * Get dominant direction (most agents agreeing)
     */
    private String getDominantDirection(Map<String, List<Signal>> signalsByDirection) {
        return signalsByDirection.entrySet().stream()
            .max(Comparator.comparingInt(e -> e.getValue().size()))
            .map(Map.Entry::getKey)
            .orElse("NEUTRAL");
    }

    /**
     * Calculate average confidence across all signals
     */
    private double calculateAverageConfidence(List<Signal> signals) {
        if (signals.isEmpty()) return 0;
        return signals.stream()
            .mapToInt(Signal::getConfidence)
            .average()
            .orElse(0);
    }

    /**
     * Calculate triangulated confidence using textbook heuristic
     *
     * Assumption: Each agent is ~85% accurate independently.
     * If 2+ agents agree on answer X:
     *   - P(majority correct) = P(all agree and correct) + P(majority agree and correct)
     *
     * Example: 3 agents, 85% accuracy each
     *   - P(all 3 correct) = 0.85^3 = 0.614
     *   - P(exactly 2 correct) = C(3,2) × 0.85^2 × 0.15 = 0.325
     *   - P(majority correct) ≈ 0.939 (94%)
     */
    private double calculateTriangulatedConfidence(int agentsAgreeing, int totalAgents, double baseConfidence) {
        // Normalize base confidence to probability
        double p = baseConfidence / 100.0;

        // Apply triangulation boost based on agreement ratio
        double agreementRatio = (double) agentsAgreeing / totalAgents;

        // If all agents agree, high boost
        if (agreementRatio >= 0.95) {
            return Math.min(100, baseConfidence + 15);
        }
        // If 2/3+ agree, moderate boost
        else if (agreementRatio >= 0.66) {
            return Math.min(100, baseConfidence + 8);
        }
        // If 1/2 agree, slight boost
        else if (agreementRatio >= 0.50) {
            return Math.min(100, baseConfidence + 3);
        }
        // If minority agrees, reduce confidence
        else {
            return Math.max(0, baseConfidence - 10);
        }
    }

    /**
     * Determine consensus level based on agreement and signal direction diversity
     */
    private String determineConsensusLevel(int agentsAgreeing, int totalAgents,
                                          Map<String, List<Signal>> signalsByDirection) {
        if (totalAgents == 0) return "NO_DATA";
        if (totalAgents == 1) return "WEAK";

        double ratio = (double) agentsAgreeing / totalAgents;

        // Check if signals are in conflicting directions (both POSITIVE and NEGATIVE)
        boolean hasPositive = signalsByDirection.containsKey("POSITIVE") && !signalsByDirection.get("POSITIVE").isEmpty();
        boolean hasNegative = signalsByDirection.containsKey("NEGATIVE") && !signalsByDirection.get("NEGATIVE").isEmpty();

        if (hasPositive && hasNegative) {
            // Find the strength of the minority opinion
            List<Signal> minoritySignals = new ArrayList<>();
            List<Signal> majoritySignals = new ArrayList<>();

            if (signalsByDirection.get("POSITIVE").size() > signalsByDirection.get("NEGATIVE").size()) {
                majoritySignals = signalsByDirection.get("POSITIVE");
                minoritySignals = signalsByDirection.get("NEGATIVE");
            } else {
                majoritySignals = signalsByDirection.get("NEGATIVE");
                minoritySignals = signalsByDirection.get("POSITIVE");
            }

            int maxMinorityConfidence = minoritySignals.stream()
                .mapToInt(Signal::getConfidence)
                .max()
                .orElse(0);

            // If minority has strong confidence (>= 70), signals are conflicting
            if (maxMinorityConfidence >= 70) {
                return "CONFLICTING";
            }
        }

        if (ratio >= 0.95) return "UNANIMOUS";
        if (ratio >= 0.66) return "HIGH";
        if (ratio >= 0.50) return "MEDIUM";
        if (ratio >= 0.33) return "CONFLICTING";
        return "WEAK";
    }

    /**
     * Determine recommendation based on consensus
     */
    private String determineRecommendation(String consensusLevel, int agentsAgreeing, int totalAgents) {
        return switch (consensusLevel) {
            case "UNANIMOUS", "HIGH" -> "TRUST_SIGNAL";
            case "MEDIUM" -> "MODERATE_SIGNAL";
            case "CONFLICTING" -> "INVESTIGATE";
            case "WEAK" -> "INSUFFICIENT_DATA";
            default -> "UNKNOWN";
        };
    }

    /**
     * Determine risk level
     */
    private String determineRiskLevel(String consensusLevel, double confidence) {
        if ("CONFLICTING".equals(consensusLevel) || "WEAK".equals(consensusLevel)) {
            return "HIGH";
        }
        if (confidence < 70) {
            return "MEDIUM";
        }
        return "LOW";
    }

    /**
     * Serialize signals to JSON for storage
     */
    private String serializeSignals(List<Signal> signals) {
        // Simplified: just return count and types for now
        String types = signals.stream()
            .map(Signal::getSignalType)
            .distinct()
            .collect(Collectors.joining(", "));
        return String.format("[signals: %d agents, types: %s]", signals.size(), types);
    }

    /**
     * Build a weak signal result when insufficient data
     */
    private TriangulationResult buildWeakSignalResult(List<Signal> signals) {
        String company = signals != null && !signals.isEmpty()
            ? signals.get(0).getCompanyName()
            : "UNKNOWN";

        return TriangulationResult.builder()
            .companyName(company)
            .consensusLevel("NO_DATA")
            .agentsAgreeing(0)
            .totalAgentsReporting(0)
            .averageConfidence(0)
            .triangulatedConfidence(0)
            .signalDirection("NEUTRAL")
            .recommendation("INSUFFICIENT_DATA")
            .riskLevel("HIGH")
            .createdAt(LocalDateTime.now())
            .build();
    }
}
