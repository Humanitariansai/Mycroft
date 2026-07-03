package com.mycroft.triangulation.domain;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "signal_agreements")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class SignalAgreement {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 255)
    private String companyName;

    @Column(nullable = false)
    private Integer signalsAnalyzed;

    @Column(nullable = false)
    private Integer agreementCount; // How many agreed?

    @Column(nullable = false)
    private Integer conflictFlags; // How many conflicts detected?

    @Column(nullable = false, columnDefinition = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}
