package com.mycroft.triangulation;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.context.annotation.Configuration;

@SpringBootApplication
@EnableScheduling
@Configuration
public class TriangulationValidatorApplication {

    public static void main(String[] args) {
        SpringApplication.run(TriangulationValidatorApplication.class, args);
    }
}
