import structlog
import pandas as pd

logger = structlog.get_logger()

# Filing status mapping: canonical → Tax-Calculator MARS codes
FILING_STATUS_TO_MARS = {
    "SINGLE": 1,
    "MFJ": 2,
    "MFS": 3,
    "HOH": 4,
    "QSS": 5,
}


class TaxCalcAdapter:
    """Adapter between canonical TaxFacts and PSLmodels Tax-Calculator."""

    def __init__(self) -> None:
        self._engine_version: str | None = None

    def get_engine_version(self) -> str:
        if self._engine_version:
            return self._engine_version
        try:
            import taxcalc
            self._engine_version = getattr(taxcalc, "__version__", "unknown")
        except ImportError:
            self._engine_version = "not-installed"
        return self._engine_version

    def map_facts_to_engine_input(self, facts_data: dict) -> dict:
        """Map canonical TaxFacts to Tax-Calculator input variables."""
        filing_status = facts_data.get("filing_status", "SINGLE")
        mars = FILING_STATUS_TO_MARS.get(filing_status, 1)

        # Aggregate W-2 wages
        w2_list = facts_data.get("income", {}).get("w2", [])
        total_wages = sum(w.get("wages_box1", 0) for w in w2_list)

        # Count dependents
        dependents = facts_data.get("dependents", [])
        # n24 = dependents under 17 (Child Tax Credit eligible)
        # For MVP, we count all dependents as n24 since we don't have DOB validation yet
        n24 = len(dependents)

        # Age/blind adjustments for standard deduction
        primary = facts_data.get("primary_taxpayer", {})
        age_head = 1 if primary.get("is_over_65") else 0
        blind_head = 1 if primary.get("is_blind") else 0

        # Spouse info for MFJ
        spouse = facts_data.get("spouse", {})
        age_spouse = 1 if spouse.get("is_over_65") else 0
        blind_spouse = 1 if spouse.get("is_blind") else 0

        engine_input = {
            "RECID": 1,
            "MARS": mars,
            "FLPDYR": facts_data.get("tax_year", 2025),
            "e00200": total_wages,  # Wages, salaries, tips
            "e00200p": total_wages if mars != 2 else total_wages,  # Primary earner wages
            "n24": n24,  # Number of CTC-eligible dependents
            "XTOT": 1 + (1 if mars == 2 else 0) + len(dependents),  # Total exemptions
            "age_head": 0,  # Placeholder (Tax-Calculator uses this for age-based std deduction)
            "age_spouse": 0,
            "blind_head": blind_head,
            "blind_spouse": blind_spouse,
        }

        return engine_input

    def compute(self, facts_data: dict, tax_year: int) -> dict:
        """Run Tax-Calculator and return results."""
        try:
            from taxcalc import Calculator, Policy, Records

            engine_input = self.map_facts_to_engine_input(facts_data)
            engine_input["FLPDYR"] = tax_year

            # Create a single-record DataFrame
            df = pd.DataFrame([engine_input])

            # Create Tax-Calculator objects
            pol = Policy()
            rec = Records(data=df, start_year=tax_year, gfactors=None, weights=None)
            calc = Calculator(policy=pol, records=rec)
            calc.calc_all()

            # Extract results
            iitax = float(calc.array("iitax")[0])  # Individual income tax
            payrolltax = float(calc.array("payrolltax")[0])  # Payroll tax
            combined = float(calc.array("combined")[0])  # Combined tax
            standard_deduction = float(calc.array("standard")[0])
            agi = float(calc.array("c00100")[0])  # AGI
            taxable_income = float(calc.array("c04800")[0])  # Taxable income

            total_wages = engine_input["e00200"]
            total_withheld = facts_data.get("payments", {}).get("fed_income_tax_withheld", 0)
            refund_or_balance = total_withheld - iitax

            results = {
                "tax_year": tax_year,
                "total_income": total_wages,
                "adjusted_gross_income": agi,
                "standard_deduction": standard_deduction,
                "taxable_income": taxable_income,
                "income_tax": iitax,
                "payroll_tax": payrolltax,
                "total_tax": combined,
                "withholding": total_withheld,
                "refund_or_balance": refund_or_balance,
                "line_items": [
                    {"label": "Total W-2 Wages", "value": total_wages, "line_ref": "Line 1a"},
                    {"label": "Adjusted Gross Income", "value": agi, "line_ref": "Line 11"},
                    {"label": "Standard Deduction", "value": standard_deduction, "line_ref": "Line 13"},
                    {"label": "Taxable Income", "value": taxable_income, "line_ref": "Line 15"},
                    {"label": "Income Tax", "value": iitax, "line_ref": "Line 16"},
                    {"label": "Total Tax", "value": combined, "line_ref": "Line 24"},
                    {"label": "Federal Tax Withheld", "value": total_withheld, "line_ref": "Line 25a"},
                    {
                        "label": "Refund" if refund_or_balance >= 0 else "Amount Owed",
                        "value": abs(refund_or_balance),
                        "line_ref": "Line 34" if refund_or_balance >= 0 else "Line 37",
                    },
                ],
            }

            logger.info(
                "tax_computed",
                tax_year=tax_year,
                income_tax=iitax,
                refund=refund_or_balance,
            )

            return results

        except ImportError:
            logger.warning("taxcalc_not_installed, using fallback calculation")
            return self._fallback_compute(facts_data, tax_year)

    def _fallback_compute(self, facts_data: dict, tax_year: int) -> dict:
        """Fallback computation when Tax-Calculator is not installed.

        Uses simplified 2025 federal tax brackets for demonstration.
        This is NOT authoritative — install Tax-Calculator for production use.
        """
        filing_status = facts_data.get("filing_status", "SINGLE")
        w2_list = facts_data.get("income", {}).get("w2", [])
        total_wages = sum(w.get("wages_box1", 0) for w in w2_list)
        total_withheld = facts_data.get("payments", {}).get("fed_income_tax_withheld", 0)

        # 2025 standard deductions (approximate)
        std_deductions = {
            "SINGLE": 15000,
            "MFJ": 30000,
            "MFS": 15000,
            "HOH": 22500,
            "QSS": 30000,
        }
        standard_deduction = std_deductions.get(filing_status, 15000)

        # Age/blind increases (approximate $1,600 single, $1,300 married per qualifier)
        primary = facts_data.get("primary_taxpayer", {})
        if primary.get("is_over_65"):
            standard_deduction += 1600 if filing_status in ("SINGLE", "HOH") else 1300
        if primary.get("is_blind"):
            standard_deduction += 1600 if filing_status in ("SINGLE", "HOH") else 1300

        taxable_income = max(0, total_wages - standard_deduction)

        # 2025 tax brackets (approximate, single filer — simplified)
        if filing_status == "SINGLE":
            brackets = [
                (11925, 0.10),
                (48475, 0.12),
                (103350, 0.22),
                (197300, 0.24),
                (250525, 0.32),
                (626350, 0.35),
                (float("inf"), 0.37),
            ]
        elif filing_status in ("MFJ", "QSS"):
            brackets = [
                (23850, 0.10),
                (96950, 0.12),
                (206700, 0.22),
                (394600, 0.24),
                (501050, 0.32),
                (751600, 0.35),
                (float("inf"), 0.37),
            ]
        else:  # MFS, HOH (simplified)
            brackets = [
                (11925, 0.10),
                (48475, 0.12),
                (103350, 0.22),
                (197300, 0.24),
                (250525, 0.32),
                (626350, 0.35),
                (float("inf"), 0.37),
            ]

        income_tax = 0.0
        prev_limit = 0
        remaining = taxable_income
        for limit, rate in brackets:
            bracket_income = min(remaining, limit - prev_limit)
            if bracket_income <= 0:
                break
            income_tax += bracket_income * rate
            remaining -= bracket_income
            prev_limit = limit

        refund_or_balance = total_withheld - income_tax

        return {
            "tax_year": tax_year,
            "total_income": total_wages,
            "adjusted_gross_income": total_wages,
            "standard_deduction": standard_deduction,
            "taxable_income": taxable_income,
            "income_tax": round(income_tax, 2),
            "payroll_tax": 0,
            "total_tax": round(income_tax, 2),
            "withholding": total_withheld,
            "refund_or_balance": round(refund_or_balance, 2),
            "line_items": [
                {"label": "Total W-2 Wages", "value": total_wages, "line_ref": "Line 1a"},
                {"label": "Adjusted Gross Income", "value": total_wages, "line_ref": "Line 11"},
                {"label": "Standard Deduction", "value": standard_deduction, "line_ref": "Line 13"},
                {"label": "Taxable Income", "value": taxable_income, "line_ref": "Line 15"},
                {"label": "Income Tax", "value": round(income_tax, 2), "line_ref": "Line 16"},
                {"label": "Federal Tax Withheld", "value": total_withheld, "line_ref": "Line 25a"},
                {
                    "label": "Refund" if refund_or_balance >= 0 else "Amount Owed",
                    "value": round(abs(refund_or_balance), 2),
                    "line_ref": "Line 34" if refund_or_balance >= 0 else "Line 37",
                },
            ],
            "_fallback": True,
            "_warning": "Computed using simplified tax brackets. Install Tax-Calculator for authoritative results.",
        }


# Singleton
tax_calc_adapter = TaxCalcAdapter()
