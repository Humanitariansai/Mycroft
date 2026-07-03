package com.mycroft.triangulation.repository;

import com.mycroft.triangulation.domain.Signal;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface SignalRepository extends JpaRepository<Signal, Long> {

    List<Signal> findByCompanyNameOrderByCreatedAtDesc(String companyName);

    @Query("SELECT s FROM Signal s WHERE s.companyName = :companyName " +
           "AND s.createdAt >= :since ORDER BY s.createdAt DESC")
    List<Signal> findRecentSignalsForCompany(
        @Param("companyName") String companyName,
        @Param("since") LocalDateTime since
    );

    @Query("SELECT s FROM Signal s WHERE s.companyName = :companyName " +
           "AND s.signalType = :signalType ORDER BY s.createdAt DESC")
    List<Signal> findByCompanyAndType(
        @Param("companyName") String companyName,
        @Param("signalType") String signalType
    );

    @Query("SELECT DISTINCT s.companyName FROM Signal s ORDER BY s.companyName")
    List<String> findDistinctCompanies();
}
