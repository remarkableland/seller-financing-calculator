"""
Seller Financing Calculator - Streamlit App
Texas TILA-compliant disclosure generator with multiple loan type options.
"""

import streamlit as st
from calculations import (
    calculate_all_scenarios,
    calculate_discount_scenarios,
    LoanSummary
)
from disclosure import generate_tila_disclosure


def format_currency(amount: float) -> str:
    """Format number as currency."""
    return f"${amount:,.2f}"


def format_currency_whole(amount: float) -> str:
    """Format number as currency without cents."""
    return f"${amount:,.0f}"


def display_loan_summary(summary: LoanSummary, column):
    """Display a single loan summary in a column."""
    with column:
        st.subheader(summary.loan_type)

        # Row 1: Monthly Payment (all have this)
        st.metric("Monthly Payment", format_currency(summary.monthly_payment))

        # Row 2: Second payment info (balloon or payment after I/O or N/A)
        if summary.balloon_amount:
            st.metric("Balloon Payment", format_currency(summary.balloon_amount))
        elif summary.monthly_payment_amortizing:
            st.metric("Payment After I/O", format_currency(summary.monthly_payment_amortizing))
        else:
            st.metric("Final Payment", format_currency(summary.monthly_payment))

        st.divider()

        st.write(f"**APR:** {summary.apr:.3f}%")
        st.write(f"**Finance Charge:** {format_currency(summary.finance_charge)}")
        st.write(f"**Amount Financed:** {format_currency(summary.amount_financed)}")
        st.write(f"**Total of Payments:** {format_currency(summary.total_of_payments)}")

        # Download TILA disclosure
        png_bytes = generate_tila_disclosure(summary)
        st.download_button(
            label="Download TILA Disclosure",
            data=png_bytes,
            file_name=f"tila_{summary.loan_type.replace(' ', '_').replace('(', '').replace(')', '').lower()}.png",
            mime="image/png",
            use_container_width=True,
            key=f"png_{summary.loan_type}"
        )


def main():
    st.set_page_config(
        page_title="Seller Financing Calculator",
        page_icon="🏠",
        layout="wide"
    )

    st.title("Seller Financing Calculator")
    st.markdown("Calculate and compare seller financing options with Texas TILA-compliant disclosures.")

    # Sidebar inputs
    st.sidebar.header("Loan Parameters")

    purchase_price = st.sidebar.number_input(
        "Purchase Price ($)",
        min_value=0.0,
        value=100000.0,
        step=1000.0,
        format="%.2f",
        help="Total property purchase price"
    )

    down_payment = st.sidebar.number_input(
        "Down Payment ($)",
        min_value=0.0,
        max_value=purchase_price,
        value=25000.0,
        step=1000.0,
        format="%.2f",
        help="Amount buyer pays at closing"
    )

    closing_costs = st.sidebar.number_input(
        "Closing Costs ($)",
        min_value=0.0,
        value=999.0,
        step=100.0,
        format="%.2f",
        help="Paid separately by buyer (not financed)"
    )

    asset_cost_basis = st.sidebar.number_input(
        "Asset Cost Basis ($)",
        min_value=0.0,
        value=60000.0,
        step=1000.0,
        format="%.2f",
        help="Your acquisition cost for the property"
    )

    interest_rate = st.sidebar.number_input(
        "Interest Rate (%)",
        min_value=0.0,
        max_value=30.0,
        value=10.0,
        step=0.125,
        format="%.3f",
        help="Annual interest rate"
    )

    term_years = st.sidebar.number_input(
        "Loan Term (Years)",
        min_value=1,
        max_value=40,
        value=5,
        step=1,
        help="Total loan term in years"
    )

    monthly_servicing_fee = st.sidebar.number_input(
        "Monthly Servicing Fee ($)",
        min_value=0.0,
        value=29.99,
        step=1.0,
        format="%.2f",
        help="Monthly fee for loan servicing"
    )

    st.sidebar.divider()

    io_period_years = st.sidebar.number_input(
        "Interest-Only Period (Years)",
        min_value=1,
        max_value=max(1, term_years - 1),
        value=min(3, max(1, term_years - 1)),
        step=1,
        help="For Hybrid loan: years of interest-only payments before amortization"
    )

    # Validation
    amount_financed = purchase_price - down_payment
    if amount_financed <= 0:
        st.error("Down payment must be less than purchase price.")
        return

    if interest_rate == 0:
        st.warning("Interest rate is 0%. Calculations will proceed with no interest.")

    # Calculate button
    if st.sidebar.button("Calculate All Options", type="primary", use_container_width=True):
        annual_rate = interest_rate / 100

        # Calculate all scenarios
        scenarios = calculate_all_scenarios(
            purchase_price, down_payment, annual_rate, term_years, io_period_years,
            monthly_servicing_fee, closing_costs
        )

        st.session_state['scenarios'] = scenarios
        st.session_state['params'] = {
            'purchase_price': purchase_price,
            'down_payment': down_payment,
            'closing_costs': closing_costs,
            'asset_cost_basis': asset_cost_basis,
            'interest_rate': annual_rate,
            'term_years': term_years,
            'io_period_years': io_period_years,
            'monthly_servicing_fee': monthly_servicing_fee
        }

    # Display results
    if 'scenarios' in st.session_state:
        scenarios = st.session_state['scenarios']
        params = st.session_state['params']

        # Warnings
        if params['term_years'] > 7:
            st.error(f"Term exceeds 7 years ({params['term_years']} years). Longer terms may increase risk.")
        if params['interest_rate'] < 0.10:
            st.error(f"Interest rate is below 10% ({params['interest_rate']*100:.3f}%). Consider whether this rate is sufficient.")

        # Summary header
        st.header("Loan Comparison")
        st.write(f"**Purchase Price:** {format_currency(params['purchase_price'])}")
        st.write(f"**Down Payment:** {format_currency(params['down_payment'])}")
        st.write(f"**Amount Financed:** {format_currency(params['purchase_price'] - params['down_payment'])}")
        st.write(f"**Term:** {params['term_years']} years")
        st.write(f"**Rate:** {params['interest_rate']*100:.3f}%")
        st.write(f"**Servicing Fee:** {format_currency(params['monthly_servicing_fee'])}/mo")

        st.divider()

        # Amount Due at Closing
        st.subheader("Amount Due at Closing")
        closing_total = params['down_payment'] + params['closing_costs']
        st.write(f"**Down Payment:** {format_currency(params['down_payment'])}")
        st.write(f"**Closing Costs:** {format_currency(params['closing_costs'])}")
        st.write(f"**Total Due at Closing:** {format_currency(closing_total)}")

        st.divider()

        # Three columns for the three loan types
        col1, col2, col3 = st.columns(3)

        display_loan_summary(scenarios["standard"], col1)
        display_loan_summary(scenarios["interest_only"], col2)
        display_loan_summary(scenarios["hybrid"], col3)

        # Note Sale Analysis section
        st.divider()
        st.header("Note Sale Analysis (Discount to Par)")
        st.markdown("*What a note buyer would pay at different required yields:*")

        cost_basis = params['asset_cost_basis']
        cash_at_closing = params['down_payment'] + params['closing_costs']

        # Calculate discount scenarios for each loan type
        for loan_key, loan_name in [
            ("standard", "Standard Amortization"),
            ("interest_only", "Interest-Only with Balloon"),
            ("hybrid", "Hybrid (I/O + Amortizing)")
        ]:
            summary = scenarios[loan_key]
            discount_scenarios = calculate_discount_scenarios(summary)

            st.subheader(loan_name)

            # Create a table-like display for discount to par
            cols = st.columns(4)
            for i, analysis in enumerate(discount_scenarios):
                with cols[i]:
                    st.metric(
                        f"{analysis.buyer_yield:.0f}% Yield",
                        format_currency_whole(analysis.sale_price),
                        f"-{format_currency_whole(analysis.discount_amount)} ({analysis.discount_percent:.1f}%)",
                        delta_color="normal"
                    )

            # Return Analysis
            ret_cols = st.columns(4)
            for i, analysis in enumerate(discount_scenarios):
                total_cash = cash_at_closing + analysis.sale_price
                profit = total_cash - cost_basis
                roi = (profit / cost_basis) * 100 if cost_basis > 0 else 0

                with ret_cols[i]:
                    st.write(f"**{analysis.buyer_yield:.0f}% Yield**")
                    st.write(f"Cash at Closing: {format_currency_whole(cash_at_closing)}")
                    st.write(f"Note Sale: {format_currency_whole(analysis.sale_price)}")
                    st.write(f"Total Cash: {format_currency_whole(total_cash)}")
                    st.write(f"**Profit: {format_currency_whole(profit)}**")
                    st.write(f"**ROI: {roi:.1f}%**")


if __name__ == "__main__":
    main()
