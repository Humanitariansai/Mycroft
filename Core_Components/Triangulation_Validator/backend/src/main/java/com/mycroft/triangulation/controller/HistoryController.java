package com.mycroft.triangulation.controller;

import com.mycroft.triangulation.domain.TriangulationResult;
import com.mycroft.triangulation.repository.TriangulationResultRepository;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@RestController
@RequestMapping("/api/v1/history")
@Tag(name = "History", description = "Historical triangulation results and analysis")
public class HistoryController {

    @Autowired
    private TriangulationResultRepository resultRepository;

    /**
     * Get triangulation history for a company
     */
    @GetMapping("/{company}")
    @Operation(summary = "Get company history", description = "Retrieve all triangulation results for a company")
    public ResponseEntity<Map<String, Object>> getHistory(
            @PathVariable String company,
            @RequestParam(defaultValue = "30") int days,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        try {
            log.info("Getting history for {} (past {} days)", company, days);

            LocalDateTime startDate = LocalDateTime.now().minusDays(days);
            List<TriangulationResult> results = resultRepository.findHistoryForCompany(company, startDate);

            // Paginate results
            int totalResults = results.size();
            int totalPages = (totalResults + size - 1) / size;
            int startIdx = page * size;
            int endIdx = Math.min(startIdx + size, totalResults);

            List<TriangulationResult> pageResults = results.subList(startIdx, endIdx);

            Map<String, Object> response = new HashMap<>();
            response.put("company", company);
            response.put("period_days", days);
            response.put("total_results", totalResults);
            response.put("page", page);
            response.put("size", size);
            response.put("total_pages", totalPages);
            response.put("results", pageResults);

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Error getting history for {}: {}", company, e.getMessage(), e);
            Map<String, Object> error = new HashMap<>();
            error.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }

    /**
     * Get consensus trend for a company
     */
    @GetMapping("/{company}/trend")
    @Operation(summary = "Get consensus trend", description = "Analyze consensus level changes over time")
    public ResponseEntity<Map<String, Object>> getConsensusTrend(
            @PathVariable String company,
            @RequestParam(defaultValue = "7") int days) {
        try {
            LocalDateTime startDate = LocalDateTime.now().minusDays(days);
            List<TriangulationResult> results = resultRepository.findHistoryForCompany(company, startDate);

            // Group by consensus level
            Map<String, Long> consensusCounts = results.stream()
                .collect(Collectors.groupingBy(
                    TriangulationResult::getConsensusLevel,
                    Collectors.counting()
                ));

            // Calculate average confidence over time
            Double avgConfidence = results.stream()
                .mapToInt(TriangulationResult::getTriangulatedConfidence)
                .average()
                .orElse(0);

            Map<String, Object> response = new HashMap<>();
            response.put("company", company);
            response.put("period_days", days);
            response.put("total_analyses", results.size());
            response.put("consensus_distribution", consensusCounts);
            response.put("average_confidence", avgConfidence);
            response.put("most_recent", results.isEmpty() ? null : results.get(0));

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Error getting trend for {}: {}", company, e.getMessage(), e);
            Map<String, Object> error = new HashMap<>();
            error.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }

    /**
     * Compare companies
     */
    @PostMapping("/compare")
    @Operation(summary = "Compare companies", description = "Compare triangulation results across multiple companies")
    public ResponseEntity<Map<String, Object>> compareCompanies(@RequestBody List<String> companies) {
        try {
            log.info("Comparing {} companies", companies.size());

            Map<String, Object> comparison = new HashMap<>();
            Map<String, Map<String, Object>> companyData = new HashMap<>();

            for (String company : companies) {
                List<TriangulationResult> results = resultRepository.findHistoryForCompany(company, LocalDateTime.now().minusDays(1));

                if (!results.isEmpty()) {
                    TriangulationResult latest = results.get(0);
                    Map<String, Object> data = new HashMap<>();
                    data.put("consensusLevel", latest.getConsensusLevel());
                    data.put("agentsAgreeing", latest.getAgentsAgreeing());
                    data.put("totalAgents", latest.getTotalAgentsReporting());
                    data.put("triangulatedConfidence", latest.getTriangulatedConfidence());
                    data.put("recommendation", latest.getRecommendation());
                    data.put("riskLevel", latest.getRiskLevel());
                    data.put("lastUpdated", latest.getCreatedAt());

                    companyData.put(company, data);
                }
            }

            comparison.put("companies_compared", companies.size());
            comparison.put("comparison_data", companyData);
            comparison.put("timestamp", LocalDateTime.now());

            return ResponseEntity.ok(comparison);
        } catch (Exception e) {
            log.error("Error comparing companies: {}", e.getMessage(), e);
            Map<String, Object> error = new HashMap<>();
            error.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }

    /**
     * Get conflicting signals analysis
     */
    @GetMapping("/conflicts")
    @Operation(summary = "Get conflicting signals", description = "Find results with conflicting signals")
    public ResponseEntity<Map<String, Object>> getConflictingSignals(
            @RequestParam(defaultValue = "7") int days) {
        try {
            LocalDateTime startDate = LocalDateTime.now().minusDays(days);
            List<TriangulationResult> conflicts = resultRepository.findConflictingSignals();

            // Filter by date
            List<TriangulationResult> recentConflicts = conflicts.stream()
                .filter(r -> r.getCreatedAt().isAfter(startDate))
                .collect(Collectors.toList());

            Map<String, Object> response = new HashMap<>();
            response.put("period_days", days);
            response.put("total_conflicts", recentConflicts.size());
            response.put("conflicts", recentConflicts);

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Error getting conflicting signals: {}", e.getMessage(), e);
            Map<String, Object> error = new HashMap<>();
            error.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }

    /**
     * Get high-risk signals
     */
    @GetMapping("/risks")
    @Operation(summary = "Get high-risk signals", description = "Find results marked as HIGH risk")
    public ResponseEntity<Map<String, Object>> getHighRiskSignals(
            @RequestParam(defaultValue = "7") int days) {
        try {
            LocalDateTime startDate = LocalDateTime.now().minusDays(days);
            List<TriangulationResult> highRisks = resultRepository.findHighRiskSignals();

            // Filter by date
            List<TriangulationResult> recentHighRisks = highRisks.stream()
                .filter(r -> r.getCreatedAt().isAfter(startDate))
                .collect(Collectors.toList());

            Map<String, Object> response = new HashMap<>();
            response.put("period_days", days);
            response.put("total_high_risks", recentHighRisks.size());
            response.put("high_risks", recentHighRisks);

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Error getting high-risk signals: {}", e.getMessage(), e);
            Map<String, Object> error = new HashMap<>();
            error.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }

    /**
     * Get statistics summary
     */
    @GetMapping("/statistics")
    @Operation(summary = "Get statistics", description = "Get overall system statistics")
    public ResponseEntity<Map<String, Object>> getStatistics(
            @RequestParam(defaultValue = "7") int days) {
        try {
            LocalDateTime startDate = LocalDateTime.now().minusDays(days);

            // Get all recent results
            List<TriangulationResult> allResults = resultRepository.findAll();
            List<TriangulationResult> recentResults = allResults.stream()
                .filter(r -> r.getCreatedAt().isAfter(startDate))
                .collect(Collectors.toList());

            // Calculate statistics
            long totalAnalyses = recentResults.size();

            Map<String, Long> consensusDistribution = recentResults.stream()
                .collect(Collectors.groupingBy(
                    TriangulationResult::getConsensusLevel,
                    Collectors.counting()
                ));

            Map<String, Long> recommendationDistribution = recentResults.stream()
                .collect(Collectors.groupingBy(
                    TriangulationResult::getRecommendation,
                    Collectors.counting()
                ));

            double avgConfidence = recentResults.stream()
                .mapToInt(TriangulationResult::getTriangulatedConfidence)
                .average()
                .orElse(0);

            long highRiskCount = recentResults.stream()
                .filter(r -> "HIGH".equals(r.getRiskLevel()))
                .count();

            Map<String, Object> response = new HashMap<>();
            response.put("period_days", days);
            response.put("total_analyses", totalAnalyses);
            response.put("average_confidence", Math.round(avgConfidence * 100.0) / 100.0);
            response.put("consensus_distribution", consensusDistribution);
            response.put("recommendation_distribution", recommendationDistribution);
            response.put("high_risk_count", highRiskCount);
            response.put("timestamp", LocalDateTime.now());

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Error getting statistics: {}", e.getMessage(), e);
            Map<String, Object> error = new HashMap<>();
            error.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }
}
