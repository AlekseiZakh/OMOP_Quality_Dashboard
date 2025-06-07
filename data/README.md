# data/README.md
# Sample Test Data for OMOP Quality Dashboard

This directory contains sample test data for demonstrating and testing the OMOP Quality Dashboard functionality.

## 📁 Directory Contents

- `sample_omop_data.csv` - Sample OMOP data for testing
- `generate_sample_data.py` - Script to generate synthetic OMOP data
- `data_dictionary.md` - Documentation of sample data structure
- `quality_issues_examples.csv` - Examples of common data quality issues

## 🎯 Purpose

The sample data is designed to:
- Demonstrate all quality check functionality
- Include common data quality issues for testing
- Provide realistic OMOP CDM data patterns
- Support automated testing and CI/CD

## ⚠️ Important Notes

- **This is synthetic data only** - No real patient information
- Data is generated for testing purposes
- Includes intentional quality issues for demonstration
- Do not use for actual research or clinical purposes

## 🚀 Usage

```python
# Load sample data in your tests
import pandas as pd

# Load sample person data
persons = pd.read_csv('data/sample_person.csv')

# Load sample conditions
conditions = pd.read_csv('data/sample_condition_occurrence.csv')
```

---

# data/generate_sample_data.py
"""
Generate synthetic OMOP data for testing and demonstration
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from pathlib import Path

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

def generate_sample_person_data(n_patients=1000):
    """Generate sample person table data"""
    
    # Gender concepts (OMOP standard)
    gender_concepts = {
        8507: 'MALE',
        8532: 'FEMALE'
    }
    
    # Race concepts
    race_concepts = {
        8527: 'White',
        8515: 'Asian',
        8516: 'Black or African American',
        8557: 'Native Hawaiian or Other Pacific Islander'
    }
    
    # Ethnicity concepts
    ethnicity_concepts = {
        38003564: 'Not Hispanic or Latino',
        38003563: 'Hispanic or Latino'
    }
    
    data = []
    for i in range(1, n_patients + 1):
        # Generate birth year (1920-2010)
        birth_year = random.randint(1920, 2010)
        
        # Some records with missing month/day (quality issue)
        month_of_birth = random.randint(1, 12) if random.random() > 0.1 else None
        day_of_birth = random.randint(1, 28) if month_of_birth and random.random() > 0.2 else None
        
        # Some records with missing demographics (quality issue)
        gender_concept_id = random.choice(list(gender_concepts.keys())) if random.random() > 0.02 else None
        race_concept_id = random.choice(list(race_concepts.keys())) if random.random() > 0.05 else None
        ethnicity_concept_id = random.choice(list(ethnicity_concepts.keys())) if random.random() > 0.08 else None
        
        # Intentional quality issues for testing
        if i <= 5:  # First 5 records have specific issues
            if i == 1:
                birth_year = 1800  # Too old
            elif i == 2:
                birth_year = 2025  # Future birth year
            elif i == 3:
                gender_concept_id = None  # Missing gender
            elif i == 4:
                race_concept_id = None  # Missing race
            elif i == 5:
                birth_year = None  # Missing birth year
        
        data.append({
            'person_id': i,
            'gender_concept_id': gender_concept_id,
            'year_of_birth': birth_year,
            'month_of_birth': month_of_birth,
            'day_of_birth': day_of_birth,
            'race_concept_id': race_concept_id,
            'ethnicity_concept_id': ethnicity_concept_id,
            'location_id': random.randint(1, 100) if random.random() > 0.3 else None,
            'provider_id': random.randint(1, 50) if random.random() > 0.5 else None,
            'care_site_id': random.randint(1, 20) if random.random() > 0.4 else None
        })
    
    return pd.DataFrame(data)

def generate_sample_condition_data(person_df, n_conditions=5000):
    """Generate sample condition_occurrence data"""
    
    # Common condition concepts
    condition_concepts = {
        320128: 'Essential hypertension',
        201820: 'Diabetes mellitus',
        4329847: 'Myocardial infarction',
        132797: 'Pneumonia',
        80180: 'Osteoarthritis',
        0: 'Unmapped condition'  # Quality issue
    }
    
    data = []
    for i in range(1, n_conditions + 1):
        person_id = random.choice(person_df['person_id'].tolist())
        person_birth_year = person_df[person_df['person_id'] == person_id]['year_of_birth'].iloc[0]
        
        # Generate condition date
        if person_birth_year:
            min_date = datetime(person_birth_year + 18, 1, 1)  # Assume adult conditions
        else:
            min_date = datetime(2000, 1, 1)
        
        max_date = datetime(2024, 12, 31)
        condition_start_date = min_date + timedelta(
            days=random.randint(0, (max_date - min_date).days)
        )
        
        # Some conditions have end dates
        condition_end_date = None
        if random.random() > 0.6:
            condition_end_date = condition_start_date + timedelta(days=random.randint(1, 365))
        
        # Intentional quality issues
        condition_concept_id = random.choice(list(condition_concepts.keys()))
        
        # Add future dates (quality issue)
        if i <= 10:
            condition_start_date = datetime(2025, 6, 1)  # Future date
        
        # Add unmapped concepts (quality issue) 
        if random.random() < 0.05:
            condition_concept_id = 0
        
        data.append({
            'condition_occurrence_id': i,
            'person_id': person_id,
            'condition_concept_id': condition_concept_id,
            'condition_start_date': condition_start_date.strftime('%Y-%m-%d'),
            'condition_end_date': condition_end_date.strftime('%Y-%m-%d') if condition_end_date else None,
            'condition_type_concept_id': random.choice([32020, 32817, 32840]),  # EHR, Claims, etc.
            'condition_source_value': f"ICD{random.randint(10, 99)}.{random.randint(0, 9)}",
            'visit_occurrence_id': random.randint(1, 2000) if random.random() > 0.1 else None
        })
    
    return pd.DataFrame(data)

def generate_sample_drug_data(person_df, n_drugs=3000):
    """Generate sample drug_exposure data"""
    
    # Common drug concepts
    drug_concepts = {
        1503297: 'Metformin',
        1308216: 'Lisinopril', 
        1118084: 'Simvastatin',
        923645: 'Aspirin',
        40239216: 'Ibuprofen',
        0: 'Unmapped drug'  # Quality issue
    }
    
    data = []
    for i in range(1, n_drugs + 1):
        person_id = random.choice(person_df['person_id'].tolist())
        
        # Generate drug dates
        drug_start_date = datetime(2020, 1, 1) + timedelta(
            days=random.randint(0, 1460)  # 4 years of data
        )
        
        # Drug duration
        days_supply = random.randint(7, 90)
        drug_end_date = drug_start_date + timedelta(days=days_supply)
        
        # Quantity with some outliers (quality issues)
        quantity = random.randint(30, 90)
        if random.random() < 0.01:  # 1% outliers
            quantity = random.choice([-5, 0, 500, 10000])  # Negative or extreme values
        
        # Days supply outliers
        if random.random() < 0.01:
            days_supply = random.choice([-1, 0, 400, 1000])  # Invalid values
        
        # Unmapped concepts
        drug_concept_id = random.choice(list(drug_concepts.keys()))
        if random.random() < 0.03:
            drug_concept_id = 0
        
        data.append({
            'drug_exposure_id': i,
            'person_id': person_id,
            'drug_concept_id': drug_concept_id,
            'drug_exposure_start_date': drug_start_date.strftime('%Y-%m-%d'),
            'drug_exposure_end_date': drug_end_date.strftime('%Y-%m-%d'),
            'drug_type_concept_id': random.choice([32817, 32838, 32869]),
            'quantity': quantity,
            'days_supply': days_supply,
            'drug_source_value': f"NDC{random.randint(10000, 99999)}",
            'visit_occurrence_id': random.randint(1, 2000) if random.random() > 0.2 else None
        })
    
    return pd.DataFrame(data)

def generate_sample_visit_data(person_df, n_visits=2000):
    """Generate sample visit_occurrence data"""
    
    visit_concepts = {
        9202: 'Outpatient Visit',
        9201: 'Inpatient Visit',
        9203: 'Emergency Room Visit',
        581477: 'Telehealth Visit'
    }
    
    data = []
    for i in range(1, n_visits + 1):
        person_id = random.choice(person_df['person_id'].tolist())
        
        # Visit dates
        visit_start_date = datetime(2020, 1, 1) + timedelta(
            days=random.randint(0, 1460)
        )
        
        # Visit duration based on type
        visit_concept_id = random.choice(list(visit_concepts.keys()))
        if visit_concept_id == 9201:  # Inpatient
            duration = random.randint(1, 14)
        elif visit_concept_id == 9203:  # Emergency
            duration = 0  # Same day
        else:  # Outpatient/Telehealth
            duration = 0
        
        visit_end_date = visit_start_date + timedelta(days=duration)
        
        # Quality issues: visits with problematic durations
        if random.random() < 0.01:
            # Negative duration
            visit_end_date = visit_start_date - timedelta(days=random.randint(1, 5))
        elif random.random() < 0.005:
            # Extremely long visit
            visit_end_date = visit_start_date + timedelta(days=random.randint(400, 1000))
        
        data.append({
            'visit_occurrence_id': i,
            'person_id': person_id,
            'visit_concept_id': visit_concept_id,
            'visit_start_date': visit_start_date.strftime('%Y-%m-%d'),
            'visit_end_date': visit_end_date.strftime('%Y-%m-%d') if duration >= 0 else None,
            'visit_type_concept_id': 32817,  # EHR
            'visit_source_value': random.choice(['OP', 'IP', 'ER', 'TEL']),
            'care_site_id': random.randint(1, 20) if random.random() > 0.3 else None
        })
    
    return pd.DataFrame(data)

def generate_sample_death_data(person_df, n_deaths=50):
    """Generate sample death data with temporal issues"""
    
    # Select random patients for death records
    dead_patients = random.sample(person_df['person_id'].tolist(), n_deaths)
    
    data = []
    for person_id in dead_patients:
        person_birth_year = person_df[person_df['person_id'] == person_id]['year_of_birth'].iloc[0]
        
        if person_birth_year:
            # Normal death date
            min_death_date = datetime(person_birth_year + 50, 1, 1)
            death_date = min_death_date + timedelta(days=random.randint(0, 18250))  # Up to 50 years later
            
            # Quality issue: some deaths before birth (first 3 records)
            if person_id <= 3:
                death_date = datetime(person_birth_year - random.randint(1, 5), 1, 1)
        else:
            death_date = datetime(2023, 1, 1)
        
        data.append({
            'person_id': person_id,
            'death_date': death_date.strftime('%Y-%m-%d'),
            'death_type_concept_id': 32817,  # EHR
            'cause_concept_id': random.choice([4306655, 4132309, 4013502]) if random.random() > 0.3 else None
        })
    
    return pd.DataFrame(data)

def generate_concept_data():
    """Generate sample concept data"""
    concepts = [
        # Gender
        (8507, 'MALE', 'Gender', 'Gender', 'Gender', 'S'),
        (8532, 'FEMALE', 'Gender', 'Gender', 'Gender', 'S'),
        
        # Race
        (8527, 'White', 'Race', 'Race', 'Race', 'S'),
        (8515, 'Asian', 'Race', 'Race', 'Race', 'S'),
        (8516, 'Black or African American', 'Race', 'Race', 'Race', 'S'),
        
        # Conditions
        (320128, 'Essential hypertension', 'Condition', 'SNOMED', 'Clinical Finding', 'S'),
        (201820, 'Diabetes mellitus', 'Condition', 'SNOMED', 'Clinical Finding', 'S'),
        (4329847, 'Myocardial infarction', 'Condition', 'SNOMED', 'Clinical Finding', 'S'),
        
        # Drugs
        (1503297, 'Metformin', 'Drug', 'RxNorm', 'Ingredient', 'S'),
        (1308216, 'Lisinopril', 'Drug', 'RxNorm', 'Ingredient', 'S'),
        
        # Visits
        (9202, 'Outpatient Visit', 'Visit', 'Visit', 'Visit', 'S'),
        (9201, 'Inpatient Visit', 'Visit', 'Visit', 'Visit', 'S'),
    ]
    
    data = []
    for concept_id, name, domain, vocab, class_id, standard in concepts:
        data.append({
            'concept_id': concept_id,
            'concept_name': name,
            'domain_id': domain,
            'vocabulary_id': vocab,
            'concept_class_id': class_id,
            'standard_concept': standard,
            'concept_code': f'CODE_{concept_id}',
            'valid_start_date': '1970-01-01',
            'valid_end_date': '2099-12-31',
            'invalid_reason': None
        })
    
    return pd.DataFrame(data)

def main():
    """Generate all sample data files"""
    print("🔄 Generating synthetic OMOP data...")
    
    # Create data directory
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    
    # Generate data
    print("   Generating person data...")
    person_df = generate_sample_person_data(1000)
    person_df.to_csv(data_dir / 'sample_person.csv', index=False)
    
    print("   Generating condition data...")
    condition_df = generate_sample_condition_data(person_df, 5000)
    condition_df.to_csv(data_dir / 'sample_condition_occurrence.csv', index=False)
    
    print("   Generating drug data...")
    drug_df = generate_sample_drug_data(person_df, 3000)
    drug_df.to_csv(data_dir / 'sample_drug_exposure.csv', index=False)
    
    print("   Generating visit data...")
    visit_df = generate_sample_visit_data(person_df, 2000)
    visit_df.to_csv(data_dir / 'sample_visit_occurrence.csv', index=False)
    
    print("   Generating death data...")
    death_df = generate_sample_death_data(person_df, 50)
    death_df.to_csv(data_dir / 'sample_death.csv', index=False)
    
    print("   Generating concept data...")
    concept_df = generate_concept_data()
    concept_df.to_csv(data_dir / 'sample_concept.csv', index=False)
    
    # Generate summary
    summary = {
        'generation_date': datetime.now().isoformat(),
        'total_persons': len(person_df),
        'total_conditions': len(condition_df),
        'total_drugs': len(drug_df),
        'total_visits': len(visit_df),
        'total_deaths': len(death_df),
        'total_concepts': len(concept_df),
        'intentional_quality_issues': [
            'Future birth years (person_id 2)',
            'Very old patients (person_id 1)', 
            'Missing demographics (person_id 3-5)',
            'Future condition dates (first 10 conditions)',
            'Unmapped concepts (5% of conditions, 3% of drugs)',
            'Invalid drug quantities (1% of drugs)',
            'Deaths before birth (person_id 1-3)',
            'Negative visit durations (1% of visits)'
        ]
    }
    
    import json
    with open(data_dir / 'data_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("✅ Sample data generation complete!")
    print(f"   Generated files in: {data_dir.absolute()}")
    print(f"   Total records: {sum([len(person_df), len(condition_df), len(drug_df), len(visit_df), len(death_df)])}")

if __name__ == "__main__":
    main()

---

# data/data_dictionary.md
# OMOP Sample Data Dictionary

## Overview
This document describes the structure and content of the synthetic OMOP data used for testing the Quality Dashboard.

## Tables Generated

### person
- **Description**: Patient demographics
- **Records**: 1,000 patients
- **Quality Issues**: 
  - Missing demographics (2-8% of records)
  - Invalid birth years (too old/future dates)
  - Missing birth year entirely

| Field | Type | Description | Quality Issues |
|-------|------|-------------|----------------|
| person_id | INTEGER | Unique patient identifier | None |
| gender_concept_id | INTEGER | Gender (8507=Male, 8532=Female) | 2% missing |
| year_of_birth | INTEGER | Birth year | 5% missing, some invalid |
| month_of_birth | INTEGER | Birth month | 10% missing |
| day_of_birth | INTEGER | Birth day | 20% missing |
| race_concept_id | INTEGER | Race concept | 5% missing |
| ethnicity_concept_id | INTEGER | Ethnicity concept | 8% missing |

### condition_occurrence
- **Description**: Patient conditions/diagnoses
- **Records**: 5,000 conditions
- **Quality Issues**:
  - 5% unmapped concepts (concept_id = 0)
  - Future dates in first 10 records
  - Missing visit associations

### drug_exposure
- **Description**: Patient medications
- **Records**: 3,000 drug exposures  
- **Quality Issues**:
  - 3% unmapped concepts
  - 1% invalid quantities (negative or extreme values)
  - 1% invalid days_supply values

### visit_occurrence
- **Description**: Healthcare visits
- **Records**: 2,000 visits
- **Quality Issues**:
  - 1% negative durations (end before start)
  - 0.5% extremely long visits (>365 days)

### death
- **Description**: Patient deaths
- **Records**: 50 deaths
- **Quality Issues**:
  - First 3 records have death before birth
  - Used to test temporal consistency

### concept
- **Description**: Standard OMOP concepts
- **Records**: Core concepts for testing
- **Content**: Essential concepts for gender, race, conditions, drugs, visits

## Intentional Quality Issues

The sample data includes these intentional issues for testing:

1. **Completeness Issues**:
   - Missing required demographics
   - NULL values in critical fields

2. **Temporal Issues**:
   - Future dates
   - Events after death
   - Negative visit durations
   - Birth/death inconsistencies

3. **Concept Mapping Issues**:
   - Unmapped concepts (concept_id = 0)
   - Missing source values

4. **Referential Integrity Issues**:
   - Missing visit associations
   - Orphaned records

5. **Statistical Outliers**:
   - Extreme drug quantities
   - Unrealistic ages
   - Invalid measurements

## Usage in Testing

```python
# Load data for testing
import pandas as pd

# Basic loading
person_df = pd.read_csv('data/sample_person.csv')
conditions_df = pd.read_csv('data/sample_condition_occurrence.csv')

# Check for quality issues
missing_gender = person_df['gender_concept_id'].isnull().sum()
unmapped_conditions = conditions_df[conditions_df['condition_concept_id'] == 0]

# Use in quality checker tests
from quality_checks.completeness import CompletenessChecker
checker = CompletenessChecker(mock_database)
results = checker.run_checks()
```

## Data Generation

Regenerate sample data:
```bash
cd data/
python generate_sample_data.py
```
