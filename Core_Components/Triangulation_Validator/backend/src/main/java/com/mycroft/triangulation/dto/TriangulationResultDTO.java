package com.mycroft.triangulation.dto;

import lombok.*;
import java.time.LocalDateTime;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TriangulationResultDTO {

    private Long id;
    private String companyName;
    private String consensusLevel;
    private Integer agentsAgreeing;
    private Integer totalAgentsReporting;
    private Integer averageConfidence;
    private Integer triangulatedConfidence;
    private String signalDirection;
    private String recommendation;
    private String riskLevel;
    private List<SignalDTO> signals;
    private LocalDateTime createdAt;
}
