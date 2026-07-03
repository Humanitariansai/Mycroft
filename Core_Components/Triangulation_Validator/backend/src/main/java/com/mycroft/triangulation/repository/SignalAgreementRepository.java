package com.mycroft.triangulation.repository;

import com.mycroft.triangulation.domain.SignalAgreement;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface SignalAgreementRepository extends JpaRepository<SignalAgreement, Long> {

    List<SignalAgreement> findByCompanyNameOrderByCreatedAtDesc(String companyName);
}
