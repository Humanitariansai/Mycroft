package com.mycroft.triangulation.client;

import com.mycroft.triangulation.domain.Signal;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.*;

@Slf4j
@Service
public class SignalClient {

    @Autowired
    private RestTemplate restTemplate;

    @Value("${agent.talent.url:http://localhost:8081}")
    private String talentAgentUrl;

    @Value("${agent.patent.url:http://localhost:8082}")
    private String patentAgentUrl;

    @Value("${agent.news.url:http://localhost:8083}")
    private String newsAgentUrl;

    @Value("${agent.market.url:http://localhost:8084}")
    private String marketAgentUrl;

    @Value("${agent.regulatory.url:http://localhost:8085}")
    private String regulatoryAgentUrl;

    @Value("${signal.fetch.timeout:5000}")
    private int fetchTimeout;

    /**
     * Fetch signals for a company from all available agents
     */
    public List<Signal> fetchSignalsForCompany(String companyName) {
        List<Signal> allSignals = new ArrayList<>();

        allSignals.addAll(fetchFromAgent(companyName, "talent", talentAgentUrl));
        allSignals.addAll(fetchFromAgent(companyName, "patent", patentAgentUrl));
        allSignals.addAll(fetchFromAgent(companyName, "news", newsAgentUrl));
        allSignals.addAll(fetchFromAgent(companyName, "market", marketAgentUrl));
        allSignals.addAll(fetchFromAgent(companyName, "regulatory", regulatoryAgentUrl));

        log.info("Fetched {} total signals for company {}", allSignals.size(), companyName);
        return allSignals;
    }

    /**
     * Fetch signals from a specific agent
     */
    private List<Signal> fetchFromAgent(String companyName, String agentType, String agentUrl) {
        try {
            String endpoint = String.format("%s/api/v1/signals/%s", agentUrl, companyName);

            SignalResponse response = restTemplate.getForObject(endpoint, SignalResponse.class);
            if (response != null && response.signals != null) {
                List<Signal> signals = new ArrayList<>();
                for (SignalPayload payload : response.signals) {
                    signals.add(mapToSignal(companyName, agentType, payload));
                }
                log.debug("Fetched {} signals from {} agent for {}", signals.size(), agentType, companyName);
                return signals;
            }
        } catch (RestClientException e) {
            log.warn("Failed to fetch signals from {} agent for {}: {}", agentType, companyName, e.getMessage());
        } catch (Exception e) {
            log.error("Unexpected error fetching from {} agent: {}", agentType, e.getMessage(), e);
        }
        return new ArrayList<>();
    }

    /**
     * Map API response to Signal entity
     */
    private Signal mapToSignal(String companyName, String agentType, SignalPayload payload) {
        return Signal.builder()
            .companyName(companyName)
            .agentName(agentType.substring(0, 1).toUpperCase() + agentType.substring(1) + " Agent")
            .signalText(payload.signalText != null ? payload.signalText : "")
            .confidence(payload.confidence != null ? payload.confidence : 50)
            .signalType(agentType)
            .metadata(payload.metadata)
            .createdAt(LocalDateTime.now())
            .build();
    }

    /**
     * Fetch signals for multiple companies
     */
    public Map<String, List<Signal>> fetchSignalsForCompanies(List<String> companies) {
        Map<String, List<Signal>> result = new HashMap<>();
        for (String company : companies) {
            result.put(company, fetchSignalsForCompany(company));
        }
        return result;
    }

    /**
     * Health check for all agents
     */
    public Map<String, Boolean> checkAgentHealth() {
        Map<String, Boolean> health = new HashMap<>();

        health.put("talent", checkAgentHealthEndpoint(talentAgentUrl));
        health.put("patent", checkAgentHealthEndpoint(patentAgentUrl));
        health.put("news", checkAgentHealthEndpoint(newsAgentUrl));
        health.put("market", checkAgentHealthEndpoint(marketAgentUrl));
        health.put("regulatory", checkAgentHealthEndpoint(regulatoryAgentUrl));

        return health;
    }

    /**
     * Check if an agent is healthy
     */
    private Boolean checkAgentHealthEndpoint(String agentUrl) {
        try {
            String healthEndpoint = String.format("%s/health", agentUrl);
            Object response = restTemplate.getForObject(healthEndpoint, Object.class);
            log.debug("Agent health check successful: {}", agentUrl);
            return true;
        } catch (Exception e) {
            log.warn("Agent health check failed for {}: {}", agentUrl, e.getMessage());
            return false;
        }
    }

    /**
     * Inner class for API response
     */
    public static class SignalResponse {
        public List<SignalPayload> signals;
        public String company;
        public Long timestamp;
    }

    /**
     * Inner class for signal payload
     */
    public static class SignalPayload {
        public String signalText;
        public Integer confidence;
        public String type;
        public String metadata;
    }
}
