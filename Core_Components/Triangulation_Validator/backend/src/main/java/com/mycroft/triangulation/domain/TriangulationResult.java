package com.mycroft.triangulation.domain;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import com.fasterxml.jackson.databind.JsonNode;
import org.hibernate.type.SqlTypes;

@Entity
@Table(name = "triangulation_results", indexes = {
    @Index(name = "idx_company_latest", columnList = "company_name, created_at DESC")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TriangulationResult {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 255)
    private String companyName;

    @Column(length = 50)
    private String consensusLevel; // "HIGH", "MEDIUM", "LOW", "CONFLICTING"

    @Column(nullable = false)
    private Integer agentsAgreeing;

    @Column(nullable = false)
    private Integer totalAgentsReporting;

    @Column(nullable = false)
    private Integer averageConfidence; // 0-100, simple average

    @Column(nullable = false)
    private Integer triangulatedConfidence; // 0-100, boosted by consensus

    @Column(length = 20)
    private String signalDirection; // "POSITIVE", "NEGATIVE", "NEUTRAL"

    @Column(length = 50)
    private String recommendation; // "TRUST_SIGNAL", "CONFLICTING", "WEAK", "INVESTIGATE"

    @Column(length = 20)
    private String riskLevel; // "LOW", "MEDIUM", "HIGH"

    @Column(columnDefinition = "TEXT")
    private String signalSummary; // JSON array of signals that went into calculation

    @Column(nullable = false, columnDefinition = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}
