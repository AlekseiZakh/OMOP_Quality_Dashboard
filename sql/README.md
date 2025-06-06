# OMOP SQL Scripts and Sample Data

This directory contains SQL scripts for setting up OMOP CDM tables and sample data for testing the Quality Dashboard.

## 📁 Directory Structure

- `init/` - Database initialization scripts
- `sample_data/` - Sample OMOP data for testing
- `ddl/` - Data Definition Language scripts
- `quality_views/` - Materialized views for performance
- `indexes/` - Recommended indexes for quality checks

## 🚀 Quick Setup

### PostgreSQL
```bash
# Create database
createdb omop_cdm_test

# Run initialization scripts
psql -d omop_cdm_test -f sql/init/01_create_tables.sql
psql -d omop_cdm_test -f sql/init/02_load_sample_data.sql
psql -d omop_cdm_test -f sql/init/03_create_indexes.sql
```

### SQL Server
```sql
-- Create database
CREATE DATABASE omop_cdm_test;
USE omop_cdm_test;

-- Run scripts in order
-- Execute each file content manually or use sqlcmd
```

---

# sql/init/01_create_tables.sql
-- OMOP CDM v5.4 Table Creation Script
-- Simplified version for testing OMOP Quality Dashboard

-- =============================================================================
-- STANDARDIZED CLINICAL DATA TABLES
-- =============================================================================

-- PERSON table
CREATE TABLE person (
    person_id BIGINT NOT NULL,
    gender_concept_id INTEGER NOT NULL,
    year_of_birth INTEGER NOT NULL,
    month_of_birth INTEGER NULL,
    day_of_birth INTEGER NULL,
    birth_datetime TIMESTAMP NULL,
    race_concept_id INTEGER NOT NULL,
    ethnicity_concept_id INTEGER NOT NULL,
    location_id INTEGER NULL,
    provider_id INTEGER NULL,
    care_site_id INTEGER NULL,
    person_source_value VARCHAR(50) NULL,
    gender_source_value VARCHAR(50) NULL,
    gender_source_concept_id INTEGER NULL,
    race_source_value VARCHAR(50) NULL,
    race_source_concept_id INTEGER NULL,
    ethnicity_source_value VARCHAR(50) NULL,
    ethnicity_source_concept_id INTEGER NULL
);

-- OBSERVATION_PERIOD table
CREATE TABLE observation_period (
    observation_period_id BIGINT NOT NULL,
    person_id BIGINT NOT NULL,
    observation_period_start_date DATE NOT NULL,
    observation_period_end_date DATE NOT NULL,
    period_type_concept_id INTEGER NOT NULL
);

-- VISIT_OCCURRENCE table
CREATE TABLE visit_occurrence (
    visit_occurrence_id BIGINT NOT NULL,
    person_id BIGINT NOT NULL,
    visit_concept_id INTEGER NOT NULL,
    visit_start_date DATE NOT NULL,
    visit_start_datetime TIMESTAMP NULL,
    visit_end_date DATE NULL,
    visit_end_datetime TIMESTAMP NULL,
    visit_type_concept_id INTEGER NOT NULL,
    provider_id INTEGER NULL,
    care_site_id INTEGER NULL,
    visit_source_value VARCHAR(50) NULL,
    visit_source_concept_id INTEGER NULL,
    admitted_from_concept_id INTEGER NULL,
    admitted_from_source_value VARCHAR(50) NULL,
    discharged_to_concept_id INTEGER NULL,
    discharged_to_source_value VARCHAR(50) NULL,
    preceding_visit_occurrence_id BIGINT NULL
);

-- CONDITION_OCCURRENCE table
CREATE TABLE condition_occurrence (
    condition_occurrence_id BIGINT NOT NULL,
    person_id BIGINT NOT NULL,
    condition_concept_id INTEGER NOT NULL,
    condition_start_date DATE NOT NULL,
    condition_start_datetime TIMESTAMP NULL,
    condition_end_date DATE NULL,
    condition_end_datetime TIMESTAMP NULL,
    condition_type_concept_id INTEGER NOT NULL,
    condition_status_concept_id INTEGER NULL,
    stop_reason VARCHAR(20) NULL,
    provider_id INTEGER NULL,
    visit_occurrence_id BIGINT NULL,
    visit_detail_id BIGINT NULL,
    condition_source_value VARCHAR(50) NULL,
    condition_source_concept_id INTEGER NULL,
    condition_status_source_value VARCHAR(50) NULL
);

-- DRUG_EXPOSURE table
CREATE TABLE drug_exposure (
    drug_exposure_id BIGINT NOT NULL,
    person_id BIGINT NOT NULL,
    drug_concept_id INTEGER NOT NULL,
    drug_exposure_start_date DATE NOT NULL,
    drug_exposure_start_datetime TIMESTAMP NULL,
    drug_exposure_end_date DATE NULL,
    drug_exposure_end_datetime TIMESTAMP NULL,
    verbatim_end_date DATE NULL,
    drug_type_concept_id INTEGER NOT NULL,
    stop_reason VARCHAR(20) NULL,
    refills INTEGER NULL,
    quantity NUMERIC NULL,
    days_supply INTEGER NULL,
    sig TEXT NULL,
    route_concept_id INTEGER NULL,
    lot_number VARCHAR(50) NULL,
    provider_id INTEGER NULL,
    visit_occurrence_id BIGINT NULL,
    visit_detail_id BIGINT NULL,
    drug_source_value VARCHAR(50) NULL,
    drug_source_concept_id INTEGER NULL,
    route_source_value VARCHAR(50) NULL,
    dose_unit_source_value VARCHAR(50) NULL
);

-- PROCEDURE_OCCURRENCE table
CREATE TABLE procedure_occurrence (
    procedure_occurrence_id BIGINT NOT NULL,
    person_id BIGINT NOT NULL,
    procedure_concept_id INTEGER NOT NULL,
    procedure_date DATE NOT NULL,
    procedure_datetime TIMESTAMP NULL,
    procedure_end_date DATE NULL,
    procedure_end_datetime TIMESTAMP NULL,
    procedure_type_concept_id INTEGER NOT NULL,
    modifier_concept_id INTEGER NULL,
    quantity INTEGER NULL,
    provider_id INTEGER NULL,
    visit_occurrence_id BIGINT NULL,
    visit_detail_id BIGINT NULL,
    procedure_source_value VARCHAR(50) NULL,
    procedure_source_concept_id INTEGER NULL,
    modifier_source_value VARCHAR(50) NULL
);

-- MEASUREMENT table
CREATE TABLE measurement (
    measurement_id BIGINT NOT NULL,
    person_id BIGINT NOT NULL,
    measurement_concept_id INTEGER NOT NULL,
    measurement_date DATE NOT NULL,
    measurement_datetime TIMESTAMP NULL,
    measurement_time VARCHAR(10) NULL,
    measurement_type_concept_id INTEGER NOT NULL,
    operator_concept_id INTEGER NULL,
    value_as_number NUMERIC NULL,
    value_as_concept_id INTEGER NULL,
    unit_concept_id INTEGER NULL,
    range_low NUMERIC NULL,
    range_high NUMERIC NULL,
    provider_id INTEGER NULL,
    visit_occurrence_id BIGINT NULL,
    visit_detail_id BIGINT NULL,
    measurement_source_value VARCHAR(50) NULL,
    measurement_source_concept_id INTEGER NULL,
    unit_source_value VARCHAR(50) NULL,
    unit_source_concept_id INTEGER NULL,
    value_source_value VARCHAR(50) NULL,
    measurement_event_id BIGINT NULL,
    meas_event_field_concept_id INTEGER NULL
);

-- OBSERVATION table
CREATE TABLE observation (
    observation_id BIGINT NOT NULL,
    person_id BIGINT NOT NULL,
    observation_concept_id INTEGER NOT NULL,
    observation_date DATE NOT NULL,
    observation_datetime TIMESTAMP NULL,
    observation_type_concept_id INTEGER NOT NULL,
    value_as_number NUMERIC NULL,
    value_as_string VARCHAR(60) NULL,
    value_as_concept_id INTEGER NULL,
    qualifier_concept_id INTEGER NULL,
    unit_concept_id INTEGER NULL,
    provider_id INTEGER NULL,
    visit_occurrence_id BIGINT NULL,
    visit_detail_id BIGINT NULL,
    observation_source_value VARCHAR(50) NULL,
    observation_source_concept_id INTEGER NULL,
    unit_source_value VARCHAR(50) NULL,
    qualifier_source_value VARCHAR(50) NULL,
    value_source_value VARCHAR(50) NULL,
    observation_event_id BIGINT NULL,
    obs_event_field_concept_id INTEGER NULL
);

-- DEATH table
CREATE TABLE death (
    person_id BIGINT NOT NULL,
    death_date DATE NOT NULL,
    death_datetime TIMESTAMP NULL,
    death_type_concept_id INTEGER NULL,
    cause_concept_id INTEGER NULL,
    cause_source_value VARCHAR(50) NULL,
    cause_source_concept_id INTEGER NULL
);

-- =============================================================================
-- STANDARDIZED VOCABULARY TABLES
-- =============================================================================

-- CONCEPT table
CREATE TABLE concept (
    concept_id INTEGER NOT NULL,
    concept_name VARCHAR(255) NOT NULL,
    domain_id VARCHAR(20) NOT NULL,
    vocabulary_id VARCHAR(20) NOT NULL,
    concept_class_id VARCHAR(20) NOT NULL,
    standard_concept VARCHAR(1) NULL,
    concept_code VARCHAR(50) NOT NULL,
    valid_start_date DATE NOT NULL,
    valid_end_date DATE NOT NULL,
    invalid_reason VARCHAR(1) NULL
);

-- VOCABULARY table
CREATE TABLE vocabulary (
    vocabulary_id VARCHAR(20) NOT NULL,
    vocabulary_name VARCHAR(255) NOT NULL,
    vocabulary_reference VARCHAR(255) NULL,
    vocabulary_version VARCHAR(255) NULL,
    vocabulary_concept_id INTEGER NOT NULL
);

-- DOMAIN table
CREATE TABLE domain (
    domain_id VARCHAR(20) NOT NULL,
    domain_name VARCHAR(255) NOT NULL,
    domain_concept_id INTEGER NOT NULL
);

-- CONCEPT_CLASS table
CREATE TABLE concept_class (
    concept_class_id VARCHAR(20) NOT NULL,
    concept_class_name VARCHAR(255) NOT NULL,
    concept_class_concept_id INTEGER NOT NULL
);

-- =============================================================================
-- STANDARDIZED HEALTH SYSTEM DATA TABLES
-- =============================================================================

-- LOCATION table
CREATE TABLE location (
    location_id INTEGER NOT NULL,
    address_1 VARCHAR(50) NULL,
    address_2 VARCHAR(50) NULL,
    city VARCHAR(50) NULL,
    state VARCHAR(2) NULL,
    zip VARCHAR(9) NULL,
    county VARCHAR(20) NULL,
    location_source_value VARCHAR(50) NULL,
    country_concept_id INTEGER NULL,
    country_source_value VARCHAR(80) NULL,
    latitude NUMERIC NULL,
    longitude NUMERIC NULL
);

-- CARE_SITE table
CREATE TABLE care_site (
    care_site_id INTEGER NOT NULL,
    care_site_name VARCHAR(255) NULL,
    place_of_service_concept_id INTEGER NULL,
    location_id INTEGER NULL,
    care_site_source_value VARCHAR(50) NULL,
    place_of_service_source_value VARCHAR(50) NULL
);

-- PROVIDER table
CREATE TABLE provider (
    provider_id INTEGER NOT NULL,
    provider_name VARCHAR(255) NULL,
    npi VARCHAR(20) NULL,
    dea VARCHAR(20) NULL,
    specialty_concept_id INTEGER NULL,
    care_site_id INTEGER NULL,
    year_of_birth INTEGER NULL,
    gender_concept_id INTEGER NULL,
    provider_source_value VARCHAR(50) NULL,
    specialty_source_value VARCHAR(50) NULL,
    specialty_source_concept_id INTEGER NULL,
    gender_source_value VARCHAR(50) NULL,
    gender_source_concept_id INTEGER NULL
);

-- =============================================================================
-- PRIMARY KEY CONSTRAINTS
-- =============================================================================

ALTER TABLE person ADD CONSTRAINT xpk_person PRIMARY KEY (person_id);
ALTER TABLE observation_period ADD CONSTRAINT xpk_observation_period PRIMARY KEY (observation_period_id);
ALTER TABLE visit_occurrence ADD CONSTRAINT xpk_visit_occurrence PRIMARY KEY (visit_occurrence_id);
ALTER TABLE condition_occurrence ADD CONSTRAINT xpk_condition_occurrence PRIMARY KEY (condition_occurrence_id);
ALTER TABLE drug_exposure ADD CONSTRAINT xpk_drug_exposure PRIMARY KEY (drug_exposure_id);
ALTER TABLE procedure_occurrence ADD CONSTRAINT xpk_procedure_occurrence PRIMARY KEY (procedure_occurrence_id);
ALTER TABLE measurement ADD CONSTRAINT xpk_measurement PRIMARY KEY (measurement_id);
ALTER TABLE observation ADD CONSTRAINT xpk_observation PRIMARY KEY (observation_id);
ALTER TABLE death ADD CONSTRAINT xpk_death PRIMARY KEY (person_id);
ALTER TABLE concept ADD CONSTRAINT xpk_concept PRIMARY KEY (concept_id);
ALTER TABLE vocabulary ADD CONSTRAINT xpk_vocabulary PRIMARY KEY (vocabulary_id);
ALTER TABLE domain ADD CONSTRAINT xpk_domain PRIMARY KEY (domain_id);
ALTER TABLE concept_class ADD CONSTRAINT xpk_concept_class PRIMARY KEY (concept_class_id);
ALTER TABLE location ADD CONSTRAINT xpk_location PRIMARY KEY (location_id);
ALTER TABLE care_site ADD CONSTRAINT xpk_care_site PRIMARY KEY (care_site_id);
ALTER TABLE provider ADD CONSTRAINT xpk_provider PRIMARY KEY (provider_id);

---

# sql/init/02_load_sample_data.sql
-- Sample Data for OMOP Quality Dashboard Testing
-- This script loads minimal sample data with intentional quality issues

-- =============================================================================
-- VOCABULARY DATA (Essential for concept lookups)
-- =============================================================================

-- Insert core vocabularies
INSERT INTO vocabulary (vocabulary_id, vocabulary_name, vocabulary_reference, vocabulary_version, vocabulary_concept_id) VALUES
('Gender', 'Gender', 'OMOP generated', 'v5.0 22-MAR-18', 0),
('Race', 'Race and Ethnicity Code Set', 'CDC', 'v5.0 22-MAR-18', 0),
('SNOMED', 'Systematic Nomenclature of Medicine Clinical Terms', 'IHTSDO', 'v5.0 22-MAR-18', 0),
('RxNorm', 'RxNorm', 'NLM', 'v5.0 22-MAR-18', 0),
('Visit', 'Visit', 'OMOP generated', 'v5.0 22-MAR-18', 0);

-- Insert core domains
INSERT INTO domain (domain_id, domain_name, domain_concept_id) VALUES
('Condition', 'Condition', 19),
('Drug', 'Drug', 13),
('Procedure', 'Procedure', 10),
('Measurement', 'Measurement', 21),
('Observation', 'Observation', 27),
('Visit', 'Visit', 8),
('Gender', 'Gender', 2),
('Race', 'Race', 4);

-- Insert core concept classes
INSERT INTO concept_class (concept_class_id, concept_class_name, concept_class_concept_id) VALUES
('Gender', 'Gender', 0),
('Race', 'Race', 0),
('Clinical Finding', 'Clinical Finding', 0),
('Ingredient', 'Ingredient', 0),
('Visit', 'Visit', 0);

-- Insert essential concepts
INSERT INTO concept (concept_id, concept_name, domain_id, vocabulary_id, concept_class_id, standard_concept, concept_code, valid_start_date, valid_end_date, invalid_reason) VALUES
-- Gender concepts
(8507, 'MALE', 'Gender', 'Gender', 'Gender', 'S', 'M', '1970-01-01', '2099-12-31', NULL),
(8532, 'FEMALE', 'Gender', 'Gender', 'Gender', 'S', 'F', '1970-01-01', '2099-12-31', NULL),
-- Race concepts
(8527, 'White', 'Race', 'Race', 'Race', 'S', '5', '1970-01-01', '2099-12-31', NULL),
(8515, 'Asian', 'Race', 'Race', 'Race', 'S', '3', '1970-01-01', '2099-12-31', NULL),
(8516, 'Black or African American', 'Race', 'Race', 'Race', 'S', '4', '1970-01-01', '2099-12-31', NULL),
-- Ethnicity concepts
(38003564, 'Not Hispanic or Latino', 'Race', 'Race', 'Race', 'S', '2186-5', '1970-01-01', '2099-12-31', NULL),
(38003563, 'Hispanic or Latino', 'Race', 'Race', 'Race', 'S', '2135-2', '1970-01-01', '2099-12-31', NULL),
-- Condition concepts
(320128, 'Essential hypertension', 'Condition', 'SNOMED', 'Clinical Finding', 'S', '59621000', '1970-01-01', '2099-12-31', NULL),
(201820, 'Diabetes mellitus', 'Condition', 'SNOMED', 'Clinical Finding', 'S', '73211009', '1970-01-01', '2099-12-31', NULL),
(4329847, 'Myocardial infarction', 'Condition', 'SNOMED', 'Clinical Finding', 'S', '22298006', '1970-01-01', '2099-12-31', NULL),
-- Drug concepts
(1503297, 'Metformin', 'Drug', 'RxNorm', 'Ingredient', 'S', '6809', '1970-01-01', '2099-12-31', NULL),
(1308216, 'Lisinopril', 'Drug', 'RxNorm', 'Ingredient', 'S', '29046', '1970-01-01', '2099-12-31', NULL),
-- Visit concepts
(9202, 'Outpatient Visit', 'Visit', 'Visit', 'Visit', 'S', 'OP', '1970-01-01', '2099-12-31', NULL),
(9201, 'Inpatient Visit', 'Visit', 'Visit', 'Visit', 'S', 'IP', '1970-01-01', '2099-12-31', NULL),
(9203, 'Emergency Room Visit', 'Visit', 'Visit', 'Visit', 'S', 'ER', '1970-01-01', '2099-12-31', NULL),
-- Type concepts
(32817, 'EHR', 'Type Concept', 'Type Concept', 'Type Concept', 'S', 'EHR', '1970-01-01', '2099-12-31', NULL),
(32020, 'EHR episode entry', 'Type Concept', 'Type Concept', 'Type Concept', 'S', 'EHR episode entry', '1970-01-01', '2099-12-31', NULL);

-- =============================================================================
-- SAMPLE PERSON DATA (with quality issues)
-- =============================================================================

INSERT INTO person (person_id, gender_concept_id, year_of_birth, month_of_birth, day_of_birth, race_concept_id, ethnicity_concept_id, location_id, provider_id, care_site_id, person_source_value, gender_source_value, race_source_value, ethnicity_source_value) VALUES
-- Normal patients
(1, 8507, 1980, 5, 15, 8527, 38003564, NULL, NULL, NULL, 'P001', 'M', 'White', 'Not Hispanic'),
(2, 8532, 1975, 8, 22, 8515, 38003564, NULL, NULL, NULL, 'P002', 'F', 'Asian', 'Not Hispanic'),
(3, 8507, 1990, 12, 5, 8527, 38003563, NULL, NULL, NULL, 'P003', 'M', 'White', 'Hispanic'),
(4, 8532, 1985, 3, 10, 8516, 38003564, NULL, NULL, NULL, 'P004', 'F', 'Black', 'Not Hispanic'),
(5, 8507, 1992, 7, 25, 8527, 38003564, NULL, NULL, NULL, 'P005', 'M', 'White', 'Not Hispanic'),
-- Quality issues intentionally included
(6, NULL, 1970, NULL, NULL, 8527, 38003564, NULL, NULL, NULL, 'P006', NULL, 'White', 'Not Hispanic'),  -- Missing gender
(7, 8532, NULL, NULL, NULL, 8515, NULL, NULL, NULL, NULL, 'P007', 'F', 'Asian', NULL),  -- Missing birth year and ethnicity
(8, 8507, 1800, 1, 1, 8527, 38003564, NULL, NULL, NULL, 'P008', 'M', 'White', 'Not Hispanic'),  -- Unrealistic birth year
(9, 8532, 2025, 1, 1, 8515, 38003564, NULL, NULL, NULL, 'P009', 'F', 'Asian', 'Not Hispanic'),  -- Future birth year
(10, 8507, 1995, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'P010', 'M', NULL, NULL);  -- Missing race/ethnicity

-- =============================================================================
-- SAMPLE VISIT DATA
-- =============================================================================

INSERT INTO visit_occurrence (visit_occurrence_id, person_id, visit_concept_id, visit_start_date, visit_end_date, visit_type_concept_id, visit_source_value) VALUES
(1, 1, 9202, '2023-01-15', '2023-01-15', 32817, 'OP'),
(2, 2, 9201, '2023-02-10', '2023-02-12', 32817, 'IP'),
(3, 3, 9203, '2023-03-05', '2023-03-05', 32817, 'ER'),
(4, 4, 9202, '2023-01-20', '2023-01-20', 32817, 'OP'),
(5, 5, 9201, '2023-02-15', '2023-02-18', 32817, 'IP'),
-- Quality issues
(6, 1, 9202, '2023-04-01', '2023-03-30', 32817, 'OP'),  -- End before start
(7, 2, 9201, '2023-01-01', '2024-06-01', 32817, 'IP'),  -- Extremely long visit
(8, 999, 9202, '2023-05-01', '2023-05-01', 32817, 'OP');  -- Non-existent person_id

-- =============================================================================
-- SAMPLE CONDITION DATA (with quality issues)
-- =============================================================================

INSERT INTO condition_occurrence (condition_occurrence_id, person_id, condition_concept_id, condition_start_date, condition_end_date, condition_type_concept_id, visit_occurrence_id, condition_source_value) VALUES
-- Normal conditions
(1, 1, 320128, '2023-01-15', '2023-01-20', 32020, 1, 'I10'),
(2, 2, 201820, '2023-02-10', NULL, 32020, 2, 'E11.9'),
(3, 3, 4329847, '2023-03-05', '2023-03-10', 32020, 3, 'I21.9'),
(4, 4, 320128, '2023-01-20', NULL, 32020, 4, 'I10'),
(5, 5, 201820, '2023-02-15', NULL, 32020, 5, 'E11.9'),
-- Quality issues
(6, 1, 0, '2023-01-16', NULL, 32020, 1, 'UNMAPPED_CODE'),  -- Unmapped concept
(7, 2, 320128, '2025-06-01', NULL, 32020, 2, 'I10'),  -- Future date
(8, 999, 201820, '2023-03-01', NULL, 32020, NULL, 'E11.9'),  -- Non-existent person
(9, 8, 320128, '1790-01-01', NULL, 32020, NULL, 'I10'),  -- Date before birth
(10, 1, 320128, '2023-01-10', NULL, 32020, 999, 'I10');  -- Non-existent visit

-- =============================================================================
-- SAMPLE DRUG DATA (with quality issues)  
-- =============================================================================

INSERT INTO drug_exposure (drug_exposure_id, person_id, drug_concept_id, drug_exposure_start_date, drug_exposure_end_date, drug_type_concept_id, quantity, days_supply, visit_occurrence_id, drug_source_value) VALUES
-- Normal drugs
(1, 1, 1503297, '2023-01-16', '2023-02-15', 32817, 90, 30, 1, 'metformin'),
(2, 2, 1308216, '2023-02-11', '2023-03-13', 32817, 30, 30, 2, 'lisinopril'),
(3, 3, 1503297, '2023-03-06', '2023-04-05', 32817, 90, 30, 3, 'metformin'),
(4, 4, 1308216, '2023-01-21', '2023-02-20', 32817, 30, 30, 4, 'lisinopril'),
(5, 5, 1503297, '2023-02-16', '2023-03-18', 32817, 90, 30, 5, 'metformin'),
-- Quality issues
(6, 1, 0, '2023-01-17', '2023-02-16', 32817, 60, 30, 1, 'unknown_drug'),  -- Unmapped concept
(7, 2, 1308216, '2023-02-12', '2023-03-14', 32817, -10, 30, 2, 'lisinopril'),  -- Negative quantity
(8, 3, 1503297, '2023-03-07', '2023-04-06', 32817, 50000, 30, 3, 'metformin'),  -- Extreme quantity
(9, 4, 1308216, '2023-01-22', '2023-02-21', 32817, 30, -5, 4, 'lisinopril'),  -- Negative days supply
(10, 5, 1503297, '2023-02-17', '2023-03-19', 32817, 90, 400, 5, 'metformin');  -- Extreme days supply

-- =============================================================================
-- SAMPLE DEATH DATA (with temporal issues)
-- =============================================================================

INSERT INTO death (person_id, death_date, death_type_concept_id, cause_concept_id) VALUES
(8, '1790-01-01', 32817, 4329847),  -- Death before birth (quality issue)
(9, '2020-01-01', 32817, 4329847);  -- Death before birth year (quality issue)

-- =============================================================================
-- SAMPLE MEASUREMENT DATA (with outliers)
-- =============================================================================

INSERT INTO measurement (measurement_id, person_id, measurement_concept_id, measurement_date, measurement_type_concept_id, value_as_number, unit_concept_id, visit_occurrence_id, measurement_source_value) VALUES
-- Normal measurements (heart rate concept_id would be 3027018 in full OMOP)
(1, 1, 3027018, '2023-01-15', 32817, 72, 8541, 1, 'HR'),  -- Normal heart rate
(2, 2, 3027018, '2023-02-10', 32817, 85, 8541, 2, 'HR'),  -- Normal heart rate
(3, 3, 3027018, '2023-03-05', 32817, 95, 8541, 3, 'HR'),  -- Normal heart rate
-- Outliers
(4, 4, 3027018, '2023-01-20', 32817, 300, 8541, 4, 'HR'),  -- Impossible heart rate
(5, 5, 3027018, '2023-02-15', 32817, -10, 8541, 5, 'HR');  -- Negative heart rate

---

# sql/init/03_create_indexes.sql
-- Performance indexes for OMOP Quality Dashboard queries
-- These indexes optimize the most common quality check queries

-- =============================================================================
-- PERSON TABLE INDEXES
-- =============================================================================

CREATE INDEX idx_person_birth_year ON person(year_of_birth);
CREATE INDEX idx_person_gender ON person(gender_concept_id);
CREATE INDEX idx_person_race ON person(race_concept_id);
CREATE INDEX idx_person_ethnicity ON person(ethnicity_concept_id);

-- =============================================================================
-- CLINICAL EVENT TABLE INDEXES  
-- =============================================================================

-- Condition occurrence indexes
CREATE INDEX idx_condition_person_id ON condition_occurrence(person_id);
CREATE INDEX idx_condition_concept_id ON condition_occurrence(condition_concept_id);
CREATE INDEX idx_condition_start_date ON condition_occurrence(condition_start_date);
CREATE INDEX idx_condition_visit_id ON condition_occurrence(visit_occurrence_id);
CREATE INDEX idx_condition_person_date ON condition_occurrence(person_id, condition_start_date);

-- Drug exposure indexes
CREATE INDEX idx_drug_person_id ON drug_exposure(person_id);
CREATE INDEX idx_drug_concept_id ON drug_exposure(drug_concept_id);
CREATE INDEX idx_drug_start_date ON drug_exposure(drug_exposure_start_date);
CREATE INDEX idx_drug_visit_id ON drug_exposure(visit_occurrence_id);
CREATE INDEX idx_drug_person_date ON drug_exposure(person_id, drug_exposure_start_date);

-- Procedure occurrence indexes
CREATE INDEX idx_procedure_person_id ON procedure_occurrence(person_id);
CREATE INDEX idx_procedure_concept_id ON procedure_occurrence(procedure_concept_id);
CREATE INDEX idx_procedure_date ON procedure_occurrence(procedure_date);
CREATE INDEX idx_procedure_visit_id ON procedure_occurrence(visit_occurrence_id);

-- Measurement indexes
CREATE INDEX idx_measurement_person_id ON measurement(person_id);
CREATE INDEX idx_measurement_concept_id ON measurement(measurement_concept_id);
CREATE INDEX idx_measurement_date ON measurement(measurement_date);
CREATE INDEX idx_measurement_value ON measurement(value_as_number);
CREATE INDEX idx_measurement_visit_id ON measurement(visit_occurrence_id);

-- Visit occurrence indexes
CREATE INDEX idx_visit_person_id ON visit_occurrence(person_id);
CREATE INDEX idx_visit_concept_id ON visit_occurrence(visit_concept_id);
CREATE INDEX idx_visit_start_date ON visit_occurrence(visit_start_date);
CREATE INDEX idx_visit_end_date ON visit_occurrence(visit_end_date);
CREATE INDEX idx_visit_dates ON visit_occurrence(visit_start_date, visit_end_date);

-- Death indexes
CREATE INDEX idx_death_person_id ON death(person_id);
CREATE INDEX idx_death_date ON death(death_date);

-- =============================================================================
-- VOCABULARY INDEXES
-- =============================================================================

CREATE INDEX idx_concept_domain ON concept(domain_id);
CREATE INDEX idx_concept_vocabulary ON concept(vocabulary_id);
CREATE INDEX idx_concept_class ON concept(concept_class_id);
CREATE INDEX idx_concept_standard ON concept(standard_concept);
CREATE INDEX idx_concept_code ON concept(concept_code);
CREATE INDEX idx_concept_name ON concept(concept_name);

-- =============================================================================
-- COMPOSITE INDEXES FOR QUALITY CHECKS
-- =============================================================================

-- For unmapped concept detection
CREATE INDEX idx_condition_unmapped ON condition_occurrence(condition_concept_id) WHERE condition_concept_id = 0;
CREATE INDEX idx_drug_unmapped ON drug_exposure(drug_concept_id) WHERE drug_concept_id = 0;

-- For temporal consistency checks
CREATE INDEX idx_condition_future ON condition_occurrence(condition_start_date) WHERE condition_start_date > CURRENT_DATE;
CREATE INDEX idx_drug_future ON drug_exposure(drug_exposure_start_date) WHERE drug_exposure_start_date > CURRENT_DATE;

-- For referential integrity checks
CREATE INDEX idx_condition_person_ref ON condition_occurrence(person_id, condition_start_date);
CREATE INDEX idx_drug_person_ref ON drug_exposure(person_id, drug_exposure_start_date);

-- =============================================================================
-- STATISTICS UPDATE
-- =============================================================================

-- Update table statistics for query optimization (PostgreSQL)
ANALYZE person;
ANALYZE condition_occurrence;
ANALYZE drug_exposure;
ANALYZE procedure_occurrence;
ANALYZE measurement;
ANALYZE visit_occurrence;
ANALYZE death;
ANALYZE concept;

---

# logs/README.md
# OMOP Quality Dashboard Logs

This directory contains application logs for the OMOP Quality Dashboard.

## 📁 Log Files

- `omop_dashboard.log` - Main application log
- `quality_checks.log` - Quality check execution logs
- `database.log` - Database connection and query logs
- `errors.log` - Error and exception logs
- `performance.log` - Performance monitoring logs

## 🔧 Log Configuration

Logging is configured via environment variables in `.env`:

```bash
# Logging settings
LOG_LEVEL=INFO
LOG_FILE=logs/omop_dashboard.log
LOG_MAX_SIZE=10485760  # 10MB
LOG_BACKUP_COUNT=5
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# Component-specific logging
LOG_DATABASE_QUERIES=false
LOG_QUALITY_CHECKS=true
LOG_USER_ACTIONS=true
```

## 📊 Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General application flow information
- **WARNING**: Something unexpected happened
- **ERROR**: Serious problem occurred
- **CRITICAL**: Very serious error occurred

## 🔍 Log Analysis

### Common Log Patterns

#### Application Startup
```
2024-01-15 10:30:00 - omop_dashboard - INFO - Starting OMOP Quality Dashboard
2024-01-15 10:30:01 - database.connection - INFO - Database connection established
2024-01-15 10:30:02 - main - INFO - Dashboard ready at http://localhost:8501
```

#### Quality Check Execution
```
2024-01-15 10:35:00 - quality_checks.completeness - INFO - Starting completeness checks
2024-01-15 10:35:05 - quality_checks.completeness - INFO - Completeness checks completed: 4 PASS, 1 WARNING
2024-01-15 10:35:10 - quality_checks.temporal - WARNING - Found 5 future dates in condition_occurrence
```

#### Database Queries
```
2024-01-15 10:40:00 - database.queries - DEBUG - Executing query: SELECT COUNT(*) FROM person
2024-01-15 10:40:01 - database.queries - DEBUG - Query completed in 0.05 seconds
```

#### Errors
```
2024-01-15 10:45:00 - database.connection - ERROR - Database connection failed: FATAL: password authentication failed
2024-01-15 10:50:00 - quality_checks.temporal - ERROR - Query execution failed: relation "death" does not exist
```

## 🚨 Monitoring and Alerts

### Log Rotation
Logs are automatically rotated when they reach the maximum size:
- Keep 5 backup files
- Compress old log files
- Maximum size: 10MB per file

### Error Monitoring
Monitor error logs for:
- Database connection failures
- Query execution errors
- Authentication issues
- Memory/performance problems

### Performance Monitoring
Track performance metrics:
- Query execution times
- Memory usage patterns
- User session duration
- Quality check completion times

## 🔧 Log Management

### Viewing Logs
```bash
# View latest logs
tail -f logs/omop_dashboard.log

# Search for errors
grep ERROR logs/omop_dashboard.log

# View specific time range
grep "2024-01-15 10:" logs/omop_dashboard.log

# Monitor quality checks
grep "quality_checks" logs/omop_dashboard.log
```

### Log Cleanup
```bash
# Clean old logs (older than 30 days)
find logs/ -name "*.log.*" -mtime +30 -delete

# Archive logs
tar -czf logs_archive_$(date +%Y%m%d).tar.gz logs/

# Clear current logs (careful!)
> logs/omop_dashboard.log
```

### Log Analysis Tools
```bash
# Install log analysis tools
pip install loguru
pip install matplotlib

# Generate log report
python scripts/analyze_logs.py logs/omop_dashboard.log
```

## 📈 Log-Based Metrics

### Quality Check Performance
- Average execution time per check type
- Most common quality issues
- Quality score trends over time
- User interaction patterns

### System Health
- Database connection reliability
- Memory usage patterns
- Error frequency and types
- Performance bottlenecks

### Usage Analytics
- Peak usage hours
- Most used quality checks
- User session patterns
- Export/download frequency

## 🔒 Log Security

### Sensitive Data
Logs are configured to exclude:
- Database passwords
- Patient identifiers
- Sensitive query results
- Personal information

### Access Control
- Logs directory permissions: 750
- Log files permissions: 640
- Only dashboard user can write logs
- Admin group can read logs

### Compliance
- Logs retain for audit requirements
- No PHI in log files
- Secure log transmission
- Regular log integrity checks

## 🚀 Best Practices

### Log Monitoring
1. **Set up alerts** for ERROR and CRITICAL logs
2. **Monitor disk space** for log directory
3. **Regular log review** for performance issues
4. **Archive old logs** to prevent disk full

### Troubleshooting
1. **Check recent logs** first for error context
2. **Increase log level** temporarily for debugging
3. **Monitor resource usage** during heavy operations
4. **Document recurring issues** and solutions

### Performance
1. **Use appropriate log levels** in production
2. **Rotate logs regularly** to prevent large files
3. **Consider centralized logging** for multiple instances
4. **Monitor log write performance** impact
