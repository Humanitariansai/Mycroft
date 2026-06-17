package com.mycroft.triangulation.dto;

import lombok.*;
import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class SignalDTO {

    private Long id;
    private String companyName;
    private String agentName;
    private String signalText;
    private Integer confidence;
    private String signalType;
    private String metadata;
    private LocalDateTime createdAt;
}
