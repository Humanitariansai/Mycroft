package com.mycroft.triangulation.repository;

import com.mycroft.triangulation.domain.TriangulationResult;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface TriangulationResultRepository extends JpaRepository<TriangulationResult, Long> {

    @Query("SELECT t FROM TriangulationResult t WHERE t.companyName = :companyName " +
           "ORDER BY t.createdAt DESC LIMIT 1")
    Optional<TriangulationResult> findLatestForCompany(@Param("companyName") String companyName);

    @Query("SELECT t FROM TriangulationResult t WHERE t.companyName = :companyName " +
           "AND t.createdAt >= :since ORDER BY t.createdAt DESC")
    List<TriangulationResult> findHistoryForCompany(
        @Param("companyName") String companyName,
        @Param("since") LocalDateTime since
    );

    @Query("SELECT t FROM TriangulationResult t WHERE t.consensusLevel = 'CONFLICTING' " +
           "ORDER BY t.createdAt DESC")
    List<TriangulationResult> findConflictingSignals();

    @Query("SELECT t FROM TriangulationResult t WHERE t.riskLevel = 'HIGH' " +
           "ORDER BY t.createdAt DESC")
    List<TriangulationResult> findHighRiskSignals();
}
