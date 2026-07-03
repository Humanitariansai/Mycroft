package com.mycroft.triangulation.controller;

import com.mycroft.triangulation.domain.Signal;
import com.mycroft.triangulation.dto.SignalDTO;
import com.mycroft.triangulation.service.SignalAggregator;
import com.mycroft.triangulation.service.TriangulationEngine;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import static org.hamcrest.Matchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class TriangulationControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    private SignalDTO testSignal;

    @BeforeEach
    void setUp() {
        testSignal = new SignalDTO();
        testSignal.setCompanyName("TestCorp");
        testSignal.setAgentName("Talent Agent");
        testSignal.setSignalText("Strong hiring activity");
        testSignal.setConfidence(85);
        testSignal.setSignalType("talent");
    }

    @Test
    void testIngestSignal_Success() throws Exception {
        mockMvc.perform(post("/api/v1/signals/ingest")
            .contentType(MediaType.APPLICATION_JSON)
            .content(objectMapper.writeValueAsString(testSignal)))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.success").value(true))
            .andExpect(jsonPath("$.company").value("TestCorp"))
            .andExpect(jsonPath("$.agent").value("Talent Agent"));
    }

    @Test
    void testIngestSignal_MissingCompany() throws Exception {
        testSignal.setCompanyName(null);
        mockMvc.perform(post("/api/v1/signals/ingest")
            .contentType(MediaType.APPLICATION_JSON)
            .content(objectMapper.writeValueAsString(testSignal)))
            .andExpect(status().is4xxClientError());
    }

    @Test
    void testAnalyzeCompany_Success() throws Exception {
        // First ingest a signal
        mockMvc.perform(post("/api/v1/signals/ingest")
            .contentType(MediaType.APPLICATION_JSON)
            .content(objectMapper.writeValueAsString(testSignal)));

        // Then analyze
        mockMvc.perform(post("/api/v1/analyze/TestCorp"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.companyName").value("TestCorp"))
            .andExpect(jsonPath("$.consensusLevel").exists());
    }

    @Test
    void testGetLatestResult() throws Exception {
        // Ingest a signal first
        mockMvc.perform(post("/api/v1/signals/ingest")
            .contentType(MediaType.APPLICATION_JSON)
            .content(objectMapper.writeValueAsString(testSignal)));

        // Get latest result
        mockMvc.perform(get("/api/v1/triangulation/TestCorp/latest"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.company").value("TestCorp"))
            .andExpect(jsonPath("$.consensusLevel").exists())
            .andExpect(jsonPath("$.triangulatedConfidence").exists());
    }

    @Test
    void testGetSignalSummary() throws Exception {
        // Ingest signals
        mockMvc.perform(post("/api/v1/signals/ingest")
            .contentType(MediaType.APPLICATION_JSON)
            .content(objectMapper.writeValueAsString(testSignal)));

        // Get summary
        mockMvc.perform(get("/api/v1/signals/TestCorp/summary"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.company").value("TestCorp"))
            .andExpect(jsonPath("$.totalSignals").value(1))
            .andExpect(jsonPath("$.averageConfidence").value(85.0));
    }

    @Test
    void testGetSignalsByType() throws Exception {
        // Ingest signal
        mockMvc.perform(post("/api/v1/signals/ingest")
            .contentType(MediaType.APPLICATION_JSON)
            .content(objectMapper.writeValueAsString(testSignal)));

        // Get by type
        mockMvc.perform(get("/api/v1/signals/TestCorp/type/talent"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$", hasSize(1)))
            .andExpect(jsonPath("$[0].signalType").value("talent"));
    }

    @Test
    void testHealthCheck() throws Exception {
        mockMvc.perform(get("/api/v1/health"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.status").value("UP"))
            .andExpect(jsonPath("$.component").value("Triangulation Validator"));
    }

    @Test
    void testBatchIngestSignals() throws Exception {
        List<SignalDTO> signals = new ArrayList<>();

        SignalDTO signal1 = new SignalDTO();
        signal1.setCompanyName("Company1");
        signal1.setAgentName("Talent Agent");
        signal1.setSignalText("Signal 1");
        signal1.setConfidence(80);
        signal1.setSignalType("talent");
        signals.add(signal1);

        SignalDTO signal2 = new SignalDTO();
        signal2.setCompanyName("Company2");
        signal2.setAgentName("Patent Agent");
        signal2.setSignalText("Signal 2");
        signal2.setConfidence(75);
        signal2.setSignalType("patent");
        signals.add(signal2);

        mockMvc.perform(post("/api/v1/signals/batch")
            .contentType(MediaType.APPLICATION_JSON)
            .content(objectMapper.writeValueAsString(signals)))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.success").value(true))
            .andExpect(jsonPath("$.signalsIngested").value(2));
    }

    @Test
    void testIngestMultipleSignalsForSameCompany() throws Exception {
        // Ingest first signal
        mockMvc.perform(post("/api/v1/signals/ingest")
            .contentType(MediaType.APPLICATION_JSON)
            .content(objectMapper.writeValueAsString(testSignal)))
            .andExpect(status().isOk());

        // Ingest second signal
        SignalDTO signal2 = new SignalDTO();
        signal2.setCompanyName("TestCorp");
        signal2.setAgentName("Patent Agent");
        signal2.setSignalText("Patent filing activity");
        signal2.setConfidence(80);
        signal2.setSignalType("patent");

        mockMvc.perform(post("/api/v1/signals/ingest")
            .contentType(MediaType.APPLICATION_JSON)
            .content(objectMapper.writeValueAsString(signal2)))
            .andExpect(status().isOk());

        // Check summary shows 2 signals
        mockMvc.perform(get("/api/v1/signals/TestCorp/summary"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.totalSignals").value(2));
    }
}
