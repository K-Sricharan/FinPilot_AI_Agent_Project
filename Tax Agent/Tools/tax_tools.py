"""
tax_tools.py
Tax calculation tools for the Tax Planning AI Agent.
FY 2024-25 implementation.
"""

from dataclasses import dataclass, asdict
from langchain_core.tools import tool

CESS_RATE = 0.04
STANDARD_DEDUCTION = 50_000


@dataclass
class TaxResult:
    regime: str
    gross_income: float
    total_deductions: float
    taxable_income: float
    tax_before_cess: float
    cess: float
    rebate_87a: float
    final_tax: float


def _apply_slabs(taxable_income: float, slabs):
    tax = 0.0
    for lower, upper, rate in slabs:
        if taxable_income <= lower:
            break
        top = taxable_income if upper is None else min(taxable_income, upper)
        tax += max(0, top - lower) * rate
    return tax


def calculate_hra(
    basic_salary: float,
    hra_received: float,
    rent_paid: float,
    is_metro: bool = True,
):
    if rent_paid <= 0 or hra_received <= 0:
        return 0.0

    return max(
        0,
        min(
            hra_received,
            max(0, rent_paid - (0.10 * basic_salary)),
            (0.50 if is_metro else 0.40) * basic_salary,
        ),
    )


def calculate_tax_old_regime(
    gross_income: float,
    deduction_80c: float = 0,
    deduction_80d: float = 0,
    hra_exemption: float = 0,
    home_loan_interest: float = 0,
    other_deductions: float = 0,
):
    total_deductions = (
        STANDARD_DEDUCTION
        + min(deduction_80c, 150000)
        + deduction_80d
        + hra_exemption
        + min(home_loan_interest, 200000)
        + other_deductions
    )

    taxable_income = max(0, gross_income - total_deductions)

    slabs = [
        (0, 250000, 0.00),
        (250000, 500000, 0.05),
        (500000, 1000000, 0.20),
        (1000000, None, 0.30),
    ]

    tax = _apply_slabs(taxable_income, slabs)

    rebate = min(tax, 12500) if taxable_income <= 500000 else 0

    tax_after_rebate = max(0, tax - rebate)

    cess = tax_after_rebate * CESS_RATE

    return TaxResult(
        regime="Old Regime",
        gross_income=gross_income,
        total_deductions=round(total_deductions),
        taxable_income=round(taxable_income),
        tax_before_cess=round(tax_after_rebate),
        cess=round(cess),
        rebate_87a=round(rebate),
        final_tax=round(tax_after_rebate + cess),
    )


def calculate_tax_new_regime(
    gross_income: float,
    nps_80ccd2: float = 0,
):
    total_deductions = STANDARD_DEDUCTION + nps_80ccd2

    taxable_income = max(0, gross_income - total_deductions)

    slabs = [
        (0, 300000, 0.00),
        (300000, 600000, 0.05),
        (600000, 900000, 0.10),
        (900000, 1200000, 0.15),
        (1200000, 1500000, 0.20),
        (1500000, None, 0.30),
    ]

    tax = _apply_slabs(taxable_income, slabs)

    rebate = min(tax, 25000) if taxable_income <= 700000 else 0

    tax_after_rebate = max(0, tax - rebate)

    cess = tax_after_rebate * CESS_RATE

    return TaxResult(
        regime="New Regime",
        gross_income=gross_income,
        total_deductions=round(total_deductions),
        taxable_income=round(taxable_income),
        tax_before_cess=round(tax_after_rebate),
        cess=round(cess),
        rebate_87a=round(rebate),
        final_tax=round(tax_after_rebate + cess),
    )


@tool
def compare_tax_regimes(
    gross_income: float,
    basic_salary: float = 0,
    hra_received: float = 0,
    rent_paid: float = 0,
    deduction_80c: float = 0,
    deduction_80d: float = 0,
    home_loan_interest: float = 0,
    other_deductions: float = 0,
    nps_80ccd2: float = 0,
    is_metro: bool = True,
):
    """
    What this function does?

    It compares the Old vs. New Tax Regime (FY 2024-25)
    to find which one saves you more money.
    
    What it needs (Inputs)
    gross_income: Your total yearly salary.
    HRA details (Optional): Basic salary, rent paid, and whether you live in a metro city.
    Old Regime Deductions (Optional): Investments like 80C (up to ₹1.5L), 80D (health insurance), home loan interest (up to ₹2L), and other tax-saving proofs.
    New Regime Benefit (Optional): Corporate NPS contributions.

    Compare the Old Tax Regime and New Tax Regime for an individual
    taxpayer (FY 2024-25).

    Parameters
    ----------
    gross_income : float
        Total annual gross income.

    basic_salary : float, optional
        Annual basic salary used for HRA exemption calculation.

    hra_received : float, optional
        Total HRA received from the employer.

    rent_paid : float, optional
        Total annual rent paid.

    deduction_80c : float, optional
        Total eligible deduction under Section 80C
        (Maximum ₹1,50,000).

    deduction_80d : float, optional
        Total eligible deduction under Section 80D.

    home_loan_interest : float, optional
        Interest paid on a self-occupied home loan
        (Maximum ₹2,00,000).

    other_deductions : float, optional
        Any additional deductions under the Old Regime.

    nps_80ccd2 : float, optional
        Employer NPS contribution deductible under
        Section 80CCD(2) (New Regime).

    is_metro : bool, optional
        True if the taxpayer resides in a metro city
        (Delhi, Mumbai, Kolkata, Chennai).

    Returns
    -------
    dict
        {
            "old_regime": {...},
            "new_regime": {...},
            "difference": ...,
            "better_regime": ...
        }
    """
    
    hra_exemption = calculate_hra(
        basic_salary=basic_salary,
        hra_received=hra_received,
        rent_paid=rent_paid,
        is_metro=is_metro,
    )

    old = calculate_tax_old_regime(
        gross_income=gross_income,
        deduction_80c=deduction_80c,
        deduction_80d=deduction_80d,
        hra_exemption=hra_exemption,
        home_loan_interest=home_loan_interest,
        other_deductions=other_deductions,
    )

    new = calculate_tax_new_regime(
        gross_income=gross_income,
        nps_80ccd2=nps_80ccd2,
    )

    difference = abs(old.final_tax - new.final_tax)

    if old.final_tax < new.final_tax:
        better = "Old Regime"
    elif new.final_tax < old.final_tax:
        better = "New Regime"
    else:
        better = "Either"

    result = {
        "old_regime": asdict(old),
        "new_regime": asdict(new),
        "difference": difference,
        "better_regime": better,
    }

    return result

if __name__ == "__main__":

    from pprint import pprint

    result = compare_tax_regimes.invoke(
        {
            "gross_income": 1800000,
            "basic_salary": 900000,
            "hra_received": 300000,
            "rent_paid": 240000,
            "deduction_80c": 150000,
            "deduction_80d": 25000,
            "home_loan_interest": 200000,
            "other_deductions": 0,
            "nps_80ccd2": 0,
            "is_metro": True,
        }
    )

    pprint(result)
