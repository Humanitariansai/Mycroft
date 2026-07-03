package com.mycroft.triangulation.domain;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "signals", indexes = {
    @Index(name = "idx_company_date", columnList = "company_name, created_at")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Signal {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 255)
    private String companyName;

    @Column(nullable = false, length = 255)
    private String agentName;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String signalText;

    @Column(nullable = false)
    private Integer confidence; // 0-100

    @Column(length = 50)
    private String signalType; // "talent", "patent", "news", "market", "regulatory", etc.

    @Column(columnDefinition = "JSONB")
    private String metadata; // Additional agent-specific data

    @Column(nullable = false, columnDefinition = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}
