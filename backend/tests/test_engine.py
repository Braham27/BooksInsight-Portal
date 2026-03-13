from app.services.engine_adapter import tax_calc_adapter


def test_fallback_compute_single():
    facts = {
        "filing_status": "single",
        "income": {
            "w2_wages": 75000,
            "w2_withholding": 10000,
        },
        "payments": {
            "federal_withheld": 10000,
            "estimated_payments": 0,
        },
    }
    result = tax_calc_adapter.compute(facts, 2025)
    assert "income_tax" in result
    assert "payroll_tax" in result
    assert "refund_or_balance" in result
    assert "line_items" in result
    assert result["total_income"] == 75000


def test_fallback_compute_mfj():
    facts = {
        "filing_status": "mfj",
        "income": {
            "w2_wages": 150000,
            "w2_withholding": 25000,
        },
        "payments": {
            "federal_withheld": 25000,
            "estimated_payments": 0,
        },
    }
    result = tax_calc_adapter.compute(facts, 2025)
    assert result["standard_deduction"] == 30000
    assert result["total_income"] == 150000
