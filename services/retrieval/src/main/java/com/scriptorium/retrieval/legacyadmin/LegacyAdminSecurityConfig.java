package com.scriptorium.retrieval.legacyadmin;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.annotation.Order;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.provisioning.InMemoryUserDetailsManager;
import org.springframework.security.web.SecurityFilterChain;

/**
 * Security split (Section 12): the human-facing legacy console requires HTTP
 * Basic auth; the internal REST API stays open, trusted to the cluster
 * network exactly as before (tenant scope is enforced by the BFF upstream).
 */
@Configuration
@EnableWebSecurity
public class LegacyAdminSecurityConfig {

    /** Console chain: Basic auth over every /legacy/admin/** request. */
    @Bean
    @Order(1)
    public SecurityFilterChain legacyAdminChain(HttpSecurity http) throws Exception {
        http.securityMatcher("/legacy/admin/**")
                .authorizeHttpRequests(auth -> auth.anyRequest().hasRole("LEGACY_ADMIN"))
                .httpBasic(Customizer.withDefaults());
        return http.build();
    }

    /**
     * Internal API chain: service-to-service REST with no cookies or
     * sessions, so CSRF protection does not apply; disabling it keeps the
     * BFF's POST /retrieve working unchanged.
     */
    @Bean
    @Order(2)
    public SecurityFilterChain internalApiChain(HttpSecurity http) throws Exception {
        // nosemgrep: java.spring.security.audit.spring-csrf-disabled.spring-csrf-disabled
        http.csrf(csrf -> csrf.disable())
                .authorizeHttpRequests(auth -> auth.anyRequest().permitAll());
        return http.build();
    }

    @Bean
    public UserDetailsService legacyAdminUsers(
            @Value("${scriptorium.legacy-admin.user}") String user,
            @Value("${scriptorium.legacy-admin.password}") String password,
            PasswordEncoder encoder) {
        return new InMemoryUserDetailsManager(
                User.withUsername(user)
                        .password(encoder.encode(password))
                        .roles("LEGACY_ADMIN")
                        .build());
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
