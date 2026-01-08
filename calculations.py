"""
Financial calculations for seller financing calculator.
Supports: Standard Amortization, Interest-Only Balloon, and Hybrid (I/O + Amortizing)
"""

from dataclasses import dataclass
from typing import List, Optional
import numpy as np


@dataclass
class PaymentScheduleRow:
    """Single row in an amortization schedule."""
    payment_number: int
    payment_amount: float
    principal: float
    interest: float
    balance: float
    is_balloon: bool = False


@dataclass
class LoanSummary:
    """Summary of loan calculations for TILA disclosure."""
    amount_financed: float
    apr: float
    finance_charge: float
    total_of_payments: float
    monthly_payment: float
    monthly_payment_amortizing: Optional[float]  # For hybrid loans
    num_payments: int
    num_io_payments: int  # For hybrid loans
    balloon_amount: Optional[float]
    balloon_payment_number: Optional[int]
    loan_type: str
    schedule: List[PaymentScheduleRow]
    monthly_servicing_fee: float = 0.0
    # Transaction details for full disclosure
    purchase_price: float = 0.0
    down_payment: float = 0.0
    closing_costs: float = 0.0


def calculate_monthly_payment(principal: float, annual_rate: float, num_payments: int) -> float:
    """
    Calculate monthly payment for a fully amortizing loan.

    Args:
        principal: Loan amount
        annual_rate: Annual interest rate as decimal (e.g., 0.06 for 6%)
        num_payments: Total number of monthly payments

    Returns:
        Monthly payment amount
    """
    if annual_rate == 0:
        return principal / num_payments

    monthly_rate = annual_rate / 12
    payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / \
              ((1 + monthly_rate) ** num_payments - 1)
    return payment


def calculate_interest_only_payment(principal: float, annual_rate: float) -> float:
    """
    Calculate monthly interest-only payment.

    Args:
        principal: Loan amount
        annual_rate: Annual interest rate as decimal

    Returns:
        Monthly interest-only payment
    """
    return principal * annual_rate / 12


def generate_standard_amortization(
    principal: float,
    annual_rate: float,
    term_years: int,
    monthly_servicing_fee: float = 0.0
) -> LoanSummary:
    """
    Generate full amortization schedule for standard loan.

    Args:
        principal: Amount financed
        annual_rate: Annual interest rate as decimal
        term_years: Loan term in years
        monthly_servicing_fee: Monthly servicing fee

    Returns:
        LoanSummary with complete schedule
    """
    num_payments = term_years * 12
    monthly_rate = annual_rate / 12
    monthly_payment = calculate_monthly_payment(principal, annual_rate, num_payments)
    total_monthly = monthly_payment + monthly_servicing_fee

    schedule = []
    balance = principal
    total_interest = 0

    for i in range(1, num_payments + 1):
        interest = balance * monthly_rate
        principal_payment = monthly_payment - interest
        balance = max(0, balance - principal_payment)
        total_interest += interest

        # Fix final payment rounding
        if i == num_payments and balance > 0:
            principal_payment += balance
            balance = 0

        schedule.append(PaymentScheduleRow(
            payment_number=i,
            payment_amount=round(total_monthly, 2),
            principal=round(principal_payment, 2),
            interest=round(interest, 2),
            balance=round(balance, 2)
        ))

    total_of_payments = total_monthly * num_payments
    finance_charge = total_of_payments - principal

    return LoanSummary(
        amount_financed=principal,
        apr=annual_rate * 100,  # Convert to percentage
        finance_charge=round(finance_charge, 2),
        total_of_payments=round(total_of_payments, 2),
        monthly_payment=round(total_monthly, 2),
        monthly_payment_amortizing=None,
        num_payments=num_payments,
        num_io_payments=0,
        balloon_amount=None,
        balloon_payment_number=None,
        loan_type="Standard Amortization",
        schedule=schedule,
        monthly_servicing_fee=monthly_servicing_fee
    )


def generate_interest_only_balloon(
    principal: float,
    annual_rate: float,
    term_years: int,
    monthly_servicing_fee: float = 0.0
) -> LoanSummary:
    """
    Generate schedule for interest-only loan with balloon payment.

    Args:
        principal: Amount financed
        annual_rate: Annual interest rate as decimal
        term_years: Loan term in years (balloon due at end)
        monthly_servicing_fee: Monthly servicing fee

    Returns:
        LoanSummary with complete schedule
    """
    num_payments = term_years * 12
    monthly_rate = annual_rate / 12
    io_payment = calculate_interest_only_payment(principal, annual_rate)
    total_monthly = io_payment + monthly_servicing_fee

    schedule = []
    total_interest = 0

    for i in range(1, num_payments + 1):
        interest = principal * monthly_rate
        total_interest += interest

        # Last payment includes balloon
        if i == num_payments:
            schedule.append(PaymentScheduleRow(
                payment_number=i,
                payment_amount=round(total_monthly + principal, 2),
                principal=round(principal, 2),
                interest=round(interest, 2),
                balance=0,
                is_balloon=True
            ))
        else:
            schedule.append(PaymentScheduleRow(
                payment_number=i,
                payment_amount=round(total_monthly, 2),
                principal=0,
                interest=round(interest, 2),
                balance=round(principal, 2)
            ))

    total_of_payments = (total_monthly * num_payments) + principal
    finance_charge = total_of_payments - principal

    return LoanSummary(
        amount_financed=principal,
        apr=annual_rate * 100,
        finance_charge=round(finance_charge, 2),
        total_of_payments=round(total_of_payments, 2),
        monthly_payment=round(total_monthly, 2),
        monthly_payment_amortizing=None,
        num_payments=num_payments,
        num_io_payments=num_payments,
        balloon_amount=round(principal, 2),
        balloon_payment_number=num_payments,
        loan_type="Interest-Only with Balloon",
        schedule=schedule,
        monthly_servicing_fee=monthly_servicing_fee
    )


def generate_hybrid(
    principal: float,
    annual_rate: float,
    term_years: int,
    io_period_years: int,
    monthly_servicing_fee: float = 0.0
) -> LoanSummary:
    """
    Generate schedule for hybrid loan (interest-only period then amortizing).

    Args:
        principal: Amount financed
        annual_rate: Annual interest rate as decimal
        term_years: Total loan term in years
        io_period_years: Interest-only period in years
        monthly_servicing_fee: Monthly servicing fee

    Returns:
        LoanSummary with complete schedule
    """
    if io_period_years >= term_years:
        raise ValueError("Interest-only period must be less than total term")

    num_io_payments = io_period_years * 12
    num_amort_payments = (term_years - io_period_years) * 12
    total_payments = term_years * 12
    monthly_rate = annual_rate / 12

    io_payment = calculate_interest_only_payment(principal, annual_rate)
    amort_payment = calculate_monthly_payment(principal, annual_rate, num_amort_payments)
    total_io_monthly = io_payment + monthly_servicing_fee
    total_amort_monthly = amort_payment + monthly_servicing_fee

    schedule = []
    balance = principal
    total_interest = 0

    # Interest-only period
    for i in range(1, num_io_payments + 1):
        interest = balance * monthly_rate
        total_interest += interest

        schedule.append(PaymentScheduleRow(
            payment_number=i,
            payment_amount=round(total_io_monthly, 2),
            principal=0,
            interest=round(interest, 2),
            balance=round(balance, 2)
        ))

    # Amortizing period
    for i in range(num_io_payments + 1, total_payments + 1):
        interest = balance * monthly_rate
        principal_payment = amort_payment - interest
        balance = max(0, balance - principal_payment)
        total_interest += interest

        # Fix final payment rounding
        if i == total_payments and balance > 0:
            principal_payment += balance
            balance = 0

        schedule.append(PaymentScheduleRow(
            payment_number=i,
            payment_amount=round(total_amort_monthly, 2),
            principal=round(principal_payment, 2),
            interest=round(interest, 2),
            balance=round(balance, 2)
        ))

    total_of_payments = (total_io_monthly * num_io_payments) + (total_amort_monthly * num_amort_payments)
    finance_charge = total_of_payments - principal

    return LoanSummary(
        amount_financed=principal,
        apr=annual_rate * 100,
        finance_charge=round(finance_charge, 2),
        total_of_payments=round(total_of_payments, 2),
        monthly_payment=round(total_io_monthly, 2),
        monthly_payment_amortizing=round(total_amort_monthly, 2),
        num_payments=total_payments,
        num_io_payments=num_io_payments,
        balloon_amount=None,
        balloon_payment_number=None,
        loan_type="Hybrid (Interest-Only + Amortizing)",
        schedule=schedule,
        monthly_servicing_fee=monthly_servicing_fee
    )


def calculate_all_scenarios(
    purchase_price: float,
    down_payment: float,
    annual_rate: float,
    term_years: int,
    io_period_years: int = 3,
    monthly_servicing_fee: float = 0.0,
    closing_costs: float = 0.0
) -> dict:
    """
    Calculate all three loan scenarios for comparison.

    Args:
        purchase_price: Total property price
        down_payment: Down payment amount
        annual_rate: Annual interest rate as decimal
        term_years: Loan term in years
        io_period_years: Interest-only period for hybrid (default 3)
        monthly_servicing_fee: Monthly servicing fee
        closing_costs: Closing costs (paid separately)

    Returns:
        Dictionary with all three LoanSummary objects
    """
    principal = purchase_price - down_payment

    # Ensure io_period is valid for hybrid
    io_years = min(io_period_years, term_years - 1) if io_period_years > 0 else 1

    standard = generate_standard_amortization(principal, annual_rate, term_years, monthly_servicing_fee)
    interest_only = generate_interest_only_balloon(principal, annual_rate, term_years, monthly_servicing_fee)
    hybrid = generate_hybrid(principal, annual_rate, term_years, io_years, monthly_servicing_fee)

    # Add transaction details to each summary
    for summary in [standard, interest_only, hybrid]:
        summary.purchase_price = purchase_price
        summary.down_payment = down_payment
        summary.closing_costs = closing_costs

    return {
        "standard": standard,
        "interest_only": interest_only,
        "hybrid": hybrid
    }


@dataclass
class NoteSaleAnalysis:
    """Analysis of note sale at a given buyer yield."""
    buyer_yield: float  # As percentage
    sale_price: float
    discount_amount: float
    discount_percent: float


def calculate_note_sale_price(summary: LoanSummary, buyer_yield: float) -> NoteSaleAnalysis:
    """
    Calculate what a note buyer would pay at a given required yield.

    Args:
        summary: LoanSummary with payment schedule
        buyer_yield: Buyer's required annual yield as decimal (e.g., 0.12 for 12%)

    Returns:
        NoteSaleAnalysis with sale price and discount info
    """
    monthly_rate = buyer_yield / 12
    principal = summary.amount_financed

    # Calculate present value of all payments at buyer's required yield
    pv = 0.0
    for row in summary.schedule:
        # Discount each payment back to present
        # Use payment amount minus servicing fee (buyer gets the P&I, not the servicing fee)
        payment = row.payment_amount - summary.monthly_servicing_fee
        discount_factor = (1 + monthly_rate) ** row.payment_number
        pv += payment / discount_factor

    sale_price = pv
    discount_amount = principal - sale_price
    discount_percent = (discount_amount / principal) * 100 if principal > 0 else 0

    return NoteSaleAnalysis(
        buyer_yield=buyer_yield * 100,
        sale_price=round(sale_price),
        discount_amount=round(discount_amount),
        discount_percent=round(discount_percent, 1)
    )


def calculate_discount_scenarios(summary: LoanSummary, yields: List[float] = None) -> List[NoteSaleAnalysis]:
    """
    Calculate note sale prices at multiple buyer yields.

    Args:
        summary: LoanSummary with payment schedule
        yields: List of annual yields as decimals (default: [0.12, 0.14, 0.16, 0.18])

    Returns:
        List of NoteSaleAnalysis for each yield
    """
    if yields is None:
        yields = [0.10, 0.12, 0.14, 0.16]

    return [calculate_note_sale_price(summary, y) for y in yields]
