package com.mycroft.triangulation.controller;

import com.mycroft.triangulation.domain.Signal;
import com.mycroft.triangulation.domain.TriangulationResult;
import com.mycroft.triangulation.dto.SignalDTO;
import com.mycroft.triangulation.dto.TriangulationResultDTO;
import com.mycroft.triangulation.service.SignalAggregator;
import com.mycroft.triangulation.service.TriangulationEngine;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/v1")
@Tag(name = "Triangulation", description = "Signal triangulation and consensus validation")
public class TriangulationController {

    @Autowired
    private SignalAggregator signalAggregator;

    @Autowired
    private TriangulationEngine triangulationEngine;

    /**
     * Ingest a new signal from an agent
     */
    @PostMapping("/signals/ingest")
    @Operation(summary = "Ingest a signal from an agent", description = "Accept a signal from any Mycroft agent")
    public ResponseEntity<Map<String, Object>> ingestSignal(@RequestBody SignalDTO signalDTO) {
        try {
            log.info("Ingesting signal for {} from {} agent", signalDTO.getCompanyName(), signalDTO.getAgentName());

            Signal saved = signalAggregator.ingestSignal(
                signalDTO.getCompanyName(),
                signalDTO.getAgentName(),
                signalDTO.getSignalText(),
                signalDTO.getConfidence(),
                signalDTO.getSignalType()
            );

            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("signalId", saved.getId());
            response.put("company", saved.getCompanyName());
            response.put("agent", saved.getAgentName());
            response.put("confidence", saved.getConfidence());

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Error ingesting signal: {}", e.getMessage(), e);
            Map<String, Object> error = new HashMap<>();
            error.put("success", false);
            error.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(error);
        }
    }

    /**
     * Analyze signals for a company and return triangulation result
     */
    @PostMapping("/analyze/{company}")
    @Operation(summary = "Analyze signals for a company", description = "Triangulate signals and return consensus result")
    public ResponseEntity<TriangulationResultDTO> analyzeCompany(@PathVariable String company) {
        try {
            log.info("Analyzing signals for company: {}", company);

            List<Signal> signals = signalAggregator.aggregateSignals(company);
            TriangulationResult result = triangulationEngine.triangulate(signals);

            TriangulationResultDTO dto = mapToDTO(result, signals);
            return ResponseEntity.ok(dto);
        } catch (Exception e) {
            log.error("Error analyzing company {}: {}", company, e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    /**
     * Get latest triangulation result for a company
     */
    @GetMapping("/triangulation/{company}/latest")
    @Operation(summary = "Get latest analysis", description = "Retrieve the most recent triangulation result for a company")
    public ResponseEntity<Map<String, Object>> getLatestResult(@PathVariable String company) {
        try {
            List<Signal> signals = signalAggregator.aggregateSignals(company);
            TriangulationResult result = triangulationEngine.triangulate(signals);

            Map<String, Object> response = new HashMap<>();
            response.put("company", company);
            response.put("consensusLevel", result.getConsensusLevel());
            response.put("agentsAgreeing", result.getAgentsAgreeing());
            response.put("totalAgents", result.getTotalAgentsReporting());
            response.put("triangulatedConfidence", result.getTriangulatedConfidence());
            response.put("recommendation", result.getRecommendation());
            response.put("riskLevel", result.getRiskLevel());
            response.put("signalDirection", result.getSignalDirection());

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Error getting latest result for {}: {}", company, e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    /**
     * Get signal summary for a company
     */
    @GetMapping("/signals/{company}/summary")
    @Operation(summary = "Get signal summary", description = "Retrieve statistics about signals for a company")
    public ResponseEntity<Map<String, Object>> getSignalSummary(@PathVariable String company) {
        try {
            Map<String, Object> summary = signalAggregator.getSignalSummary(company);
            return ResponseEntity.ok(summary);
        } catch (Exception e) {
            log.error("Error getting signal summary for {}: {}", company, e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    /**
     * Get signals by type for a company
     */
    @GetMapping("/signals/{company}/type/{type}")
    @Operation(summary = "Get signals by type", description = "Retrieve signals of a specific type for a company")
    public ResponseEntity<List<Signal>> getSignalsByType(@PathVariable String company, @PathVariable String type) {
        try {
            List<Signal> signals = signalAggregator.getSignalsByType(company, type);
            return ResponseEntity.ok(signals);
        } catch (Exception e) {
            log.error("Error getting signals by type: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    /**
     * Health check endpoint
     */
    @GetMapping("/health")
    @Operation(summary = "Health check", description = "Verify the service is running")
    public ResponseEntity<Map<String, String>> health() {
        Map<String, String> response = new HashMap<>();
        response.put("status", "UP");
        response.put("component", "Triangulation Validator");
        response.put("version", "0.1.0");
        return ResponseEntity.ok(response);
    }

    /**
     * Batch ingest signals
     */
    @PostMapping("/signals/batch")
    @Operation(summary = "Batch ingest signals", description = "Ingest multiple signals at once")
    public ResponseEntity<Map<String, Object>> batchIngestSignals(@RequestBody List<SignalDTO> signals) {
        try {
            log.info("Batch ingesting {} signals", signals.size());
            int count = 0;

            for (SignalDTO signal : signals) {
                signalAggregator.ingestSignal(
                    signal.getCompanyName(),
                    signal.getAgentName(),
                    signal.getSignalText(),
                    signal.getConfidence(),
                    signal.getSignalType()
                );
                count++;
            }

            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("signalsIngested", count);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Error batch ingesting signals: {}", e.getMessage(), e);
            Map<String, Object> error = new HashMap<>();
            error.put("success", false);
            error.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(error);
        }
    }

    /**
     * Map TriangulationResult to DTO
     */
    private TriangulationResultDTO mapToDTO(TriangulationResult result, List<Signal> signals) {
        TriangulationResultDTO dto = new TriangulationResultDTO();
        dto.setCompanyName(result.getCompanyName());
        dto.setConsensusLevel(result.getConsensusLevel());
        dto.setAgentsAgreeing(result.getAgentsAgreeing());
        dto.setTotalAgentsReporting(result.getTotalAgentsReporting());
        dto.setAverageConfidence(result.getAverageConfidence());
        dto.setTriangulatedConfidence(result.getTriangulatedConfidence());
        dto.setSignalDirection(result.getSignalDirection());
        dto.setRecommendation(result.getRecommendation());
        dto.setRiskLevel(result.getRiskLevel());

        // Convert signals to DTOs
        List<SignalDTO> signalDTOs = new java.util.ArrayList<>();
        for (Signal signal : signals) {
            SignalDTO signalDTO = new SignalDTO();
            signalDTO.setId(signal.getId());
            signalDTO.setCompanyName(signal.getCompanyName());
            signalDTO.setAgentName(signal.getAgentName());
            signalDTO.setSignalText(signal.getSignalText());
            signalDTO.setConfidence(signal.getConfidence());
            signalDTO.setSignalType(signal.getSignalType());
            signalDTOs.add(signalDTO);
        }
        dto.setSignals(signalDTOs);
        return dto;
    }
}
