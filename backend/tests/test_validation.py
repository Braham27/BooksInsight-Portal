from app.services.validation_service import validate_tax_facts


def test_validate_missing_filing_status():
    facts = {
        "taxpayer": {"first_name": "John", "last_name": "Doe", "ssn_last4": "1234"},
        "income": {"w2_wages": 50000, "w2_withholding": 5000, "employers": []},
        "dependents": [],
        "payments": {"federal_withheld": 5000, "estimated_payments": 0},
    }
    result = validate_tax_facts(facts, 2025)
    assert not result["valid"]
    field_names = [e["field"] for e in result["errors"]]
    assert "filing_status" in field_names


def test_validate_valid_facts():
    facts = {
        "filing_status": "single",
        "taxpayer": {"first_name": "Jane", "last_name": "Smith", "ssn_last4": "5678"},
        "income": {"w2_wages": 60000, "w2_withholding": 8000, "employers": [
            {"name": "Acme", "ein": "12-3456789", "wages": 60000, "federal_withheld": 8000}
        ]},
        "dependents": [],
        "payments": {"federal_withheld": 8000, "estimated_payments": 0},
    }
    result = validate_tax_facts(facts, 2025)
    assert result["valid"]
    assert len(result["errors"]) == 0


def test_validate_withholding_exceeds_wages():
    facts = {
        "filing_status": "single",
        "taxpayer": {"first_name": "Bob", "last_name": "Test", "ssn_last4": "0000"},
        "income": {"w2_wages": 50000, "w2_withholding": 60000, "employers": []},
        "dependents": [],
        "payments": {"federal_withheld": 60000, "estimated_payments": 0},
    }
    result = validate_tax_facts(facts, 2025)
    assert not result["valid"]
    field_names = [e["field"] for e in result["errors"]]
    assert "income.w2_withholding" in field_names
