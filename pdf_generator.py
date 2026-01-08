"""
PDF generator for amortization schedule comparison.
Creates a PDF with all three loan type schedules side by side.
"""

from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus import KeepTogether
from calculations import LoanSummary, PaymentScheduleRow
from typing import List


def format_currency(amount: float) -> str:
    """Format number as currency."""
    return f"${amount:,.2f}"


def create_summary_table(scenarios: dict) -> Table:
    """Create comparison summary table for all three loan types."""
    data = [
        ["", "Standard\nAmortization", "Interest-Only\nw/ Balloon", "Hybrid\n(I/O + Amort)"],
        ["Amount Financed",
         format_currency(scenarios["standard"].amount_financed),
         format_currency(scenarios["interest_only"].amount_financed),
         format_currency(scenarios["hybrid"].amount_financed)],
        ["APR",
         f"{scenarios['standard'].apr:.3f}%",
         f"{scenarios['interest_only'].apr:.3f}%",
         f"{scenarios['hybrid'].apr:.3f}%"],
        ["Monthly Payment\n(Initial)",
         format_currency(scenarios["standard"].monthly_payment),
         format_currency(scenarios["interest_only"].monthly_payment),
         format_currency(scenarios["hybrid"].monthly_payment)],
        ["Monthly Payment\n(After I/O Period)",
         "N/A",
         "N/A",
         format_currency(scenarios["hybrid"].monthly_payment_amortizing) if scenarios["hybrid"].monthly_payment_amortizing else "N/A"],
        ["Balloon Amount",
         "None",
         format_currency(scenarios["interest_only"].balloon_amount) if scenarios["interest_only"].balloon_amount else "None",
         "None"],
        ["Finance Charge\n(Total Interest)",
         format_currency(scenarios["standard"].finance_charge),
         format_currency(scenarios["interest_only"].finance_charge),
         format_currency(scenarios["hybrid"].finance_charge)],
        ["Total of Payments",
         format_currency(scenarios["standard"].total_of_payments),
         format_currency(scenarios["interest_only"].total_of_payments),
         format_currency(scenarios["hybrid"].total_of_payments)],
    ]

    table = Table(data, colWidths=[1.8*inch, 1.6*inch, 1.6*inch, 1.6*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#ecf0f1')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
        ('ROWBACKGROUNDS', (1, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    return table


def create_amortization_table(schedule: List[PaymentScheduleRow], title: str, show_every_n: int = 12) -> List:
    """
    Create amortization schedule table.

    Args:
        schedule: List of PaymentScheduleRow objects
        title: Table title
        show_every_n: Show every Nth payment (12 = annual summary, 1 = all payments)

    Returns:
        List of flowables for the PDF
    """
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#2c3e50')
    )

    elements = []
    elements.append(Paragraph(title, title_style))

    # Header row
    data = [["Payment #", "Payment", "Principal", "Interest", "Balance"]]

    # Add rows (every Nth payment for readability, plus first, last, and balloon)
    for i, row in enumerate(schedule):
        # Always show first payment, every Nth payment, balloon payments, and last payment
        show_row = (
            i == 0 or  # First
            (i + 1) % show_every_n == 0 or  # Every Nth
            row.is_balloon or  # Balloon
            i == len(schedule) - 1  # Last
        )

        if show_row:
            payment_num = str(row.payment_number)
            if row.is_balloon:
                payment_num += " (Balloon)"

            data.append([
                payment_num,
                format_currency(row.payment_amount),
                format_currency(row.principal),
                format_currency(row.interest),
                format_currency(row.balance)
            ])

    table = Table(data, colWidths=[1.2*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 0.3*inch))

    return elements


def generate_comparison_pdf(
    scenarios: dict,
    purchase_price: float,
    down_payment: float,
    closing_costs: float,
    interest_rate: float,
    term_years: int,
    io_period_years: int
) -> bytes:
    """
    Generate PDF with all three amortization schedules.

    Args:
        scenarios: Dictionary with 'standard', 'interest_only', 'hybrid' LoanSummary objects
        purchase_price: Original purchase price
        down_payment: Down payment amount
        closing_costs: Closing costs (paid separately)
        interest_rate: Annual interest rate as decimal
        term_years: Loan term in years
        io_period_years: Interest-only period for hybrid

    Returns:
        PDF as bytes
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=20,
        alignment=1,  # Center
        textColor=colors.HexColor('#2c3e50')
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        alignment=1
    )
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=16,
        spaceBefore=20,
        spaceAfter=12,
        textColor=colors.HexColor('#2c3e50')
    )

    elements = []

    # Title
    elements.append(Paragraph("Seller Financing Comparison", title_style))
    elements.append(Paragraph(f"Purchase Price: {format_currency(purchase_price)}", subtitle_style))
    elements.append(Paragraph(f"Down Payment: {format_currency(down_payment)}", subtitle_style))
    elements.append(Paragraph(f"Closing Costs: {format_currency(closing_costs)} (paid separately)", subtitle_style))
    elements.append(Paragraph(f"Interest Rate: {interest_rate*100:.2f}% | Term: {term_years} years", subtitle_style))
    if io_period_years > 0:
        elements.append(Paragraph(f"Interest-Only Period (Hybrid): {io_period_years} years", subtitle_style))
    elements.append(Spacer(1, 0.3*inch))

    # Summary comparison table
    elements.append(Paragraph("Loan Comparison Summary", section_style))
    elements.append(create_summary_table(scenarios))
    elements.append(Spacer(1, 0.3*inch))

    # Page break before amortization schedules
    elements.append(PageBreak())

    # Standard Amortization Schedule
    elements.append(Paragraph("Amortization Schedules", section_style))
    elements.append(Paragraph(
        "Note: Showing annual snapshots (every 12th payment) for readability. "
        "First payment, last payment, and balloon payments always shown.",
        ParagraphStyle('Note', parent=styles['Normal'], fontSize=9, textColor=colors.gray, spaceAfter=12)
    ))

    elements.extend(create_amortization_table(
        scenarios["standard"].schedule,
        "Option 1: Standard Amortization",
        show_every_n=12
    ))

    elements.extend(create_amortization_table(
        scenarios["interest_only"].schedule,
        "Option 2: Interest-Only with Balloon",
        show_every_n=12
    ))

    elements.extend(create_amortization_table(
        scenarios["hybrid"].schedule,
        f"Option 3: Hybrid ({io_period_years} Years I/O + Amortizing)",
        show_every_n=12
    ))

    # Disclaimer
    elements.append(Spacer(1, 0.3*inch))
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.gray,
        alignment=1
    )
    elements.append(Paragraph(
        "This document is for informational purposes only. Actual loan terms may vary. "
        "Consult with a qualified professional before making financial decisions. "
        "Generated by Seller Financing Calculator.",
        disclaimer_style
    ))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
