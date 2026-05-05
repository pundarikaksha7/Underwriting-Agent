"""Test utilities and sample data generation."""

import random
from datetime import datetime, timedelta
from app.models.schemas import ApplicationCreate


def generate_sample_application() -> ApplicationCreate:
    """Generate a random sample application for testing."""
    return ApplicationCreate(
        full_name=f"John Applicant {random.randint(1000, 9999)}",
        email=f"applicant{random.randint(1, 10000)}@example.com",
        phone=f"555-{random.randint(1000, 9999)}",
        date_of_birth=(datetime.now() - timedelta(days=365*28)).strftime("%Y-%m-%d"),
        gender=random.choice(["male", "female", "other"]),
        street_address=f"{random.randint(1, 999)} Main St",
        city=random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
        state=random.choice(["NY", "CA", "IL", "TX", "AZ"]),
        postal_code=f"{random.randint(10000, 99999)}",
        country="USA",
        annual_income=random.uniform(30000, 150000),
        monthly_expenses=random.uniform(1000, 5000),
        employment_status=random.choice(["employed", "self-employed", "retired"]),
        years_employed=random.uniform(1, 20),
        employer=random.choice(["Tech Corp", "Finance Inc", "Healthcare LLC", "Retail Co"]),
        credit_score=random.randint(500, 800),
        existing_debts=random.uniform(5000, 100000),
        number_of_accounts=random.randint(1, 15),
        delinquencies=random.randint(0, 3),
        loan_amount=random.uniform(5000, 50000),
        loan_term_months=random.choice([24, 36, 48, 60, 72]),
        loan_purpose=random.choice(["personal", "home", "auto", "consolidation"]),
        collateral_value=random.uniform(5000, 100000) if random.random() > 0.5 else None,
        applicant_notes=random.choice([
            "Good customer, stable employment",
            "Recent job change, but strong credentials",
            "High debt load but excellent payment history",
            "First time applicant",
            None,
        ]),
    )


def generate_multiple_applications(count: int = 10):
    """Generate multiple sample applications."""
    return [generate_sample_application() for _ in range(count)]
