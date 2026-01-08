# Seller Financing Calculator - Implementation Plan

## Overview
A Streamlit web app for calculating seller financing terms with Texas TILA disclosure output.

## Tech Stack
- Python 3.11+
- Streamlit
- Pillow (for PNG generation)
- NumPy (for financial calculations)
- Hosted on Streamlit Community Cloud

## User Inputs

| Field | Type | Description |
|-------|------|-------------|
| Purchase Price | Currency | Total property price |
| Down Payment | Currency | Money down at closing |
| Closing Costs | Currency | Paid separately (not financed) |
| Interest Rate | Percentage | Annual interest rate |
| Term | Integer (years) | Total loan term |
| Loan Type | Select | Standard / Interest-Only Balloon / Hybrid |
| Interest-Only Period | Integer (years) | Only shown for Hybrid type |

## Loan Types

### 1. Standard Amortization
- Fixed monthly P&I payments over full term
- Classic mortgage calculation

### 2. Interest-Only with Balloon
- Monthly interest-only payments for entire term
- Full principal due as balloon at end of term
- Formula: `Monthly Payment = (Principal × Annual Rate) / 12`

### 3. Hybrid (Interest-Only + Amortizing)
- Interest-only payments for initial period (user-specified years)
- Remaining term: fully amortizing payments
- Example: 3 years I/O, then 27 years amortizing on a 30-year note

## Calculations

### Amount Financed
```
Amount Financed = Purchase Price - Down Payment
```
(Closing costs paid separately, not included)

### APR Calculation (Regulation Z)
For simple seller financing with no fees beyond closing costs:
- APR ≈ Interest Rate (when no points/fees are financed)
- If prepaid finance charges exist, use IRR method

### Finance Charge
```
Finance Charge = Total of Payments - Amount Financed
```

### Total of Payments
Sum of all scheduled payments including balloon (if applicable)

### Monthly Payment Formulas

**Standard Amortization:**
```
M = P × [r(1+r)^n] / [(1+r)^n - 1]
Where:
  P = Principal (Amount Financed)
  r = Monthly interest rate (Annual Rate / 12)
  n = Total number of payments (Term × 12)
```

**Interest-Only:**
```
M = P × r
Where:
  P = Principal
  r = Monthly interest rate
```

**Hybrid:**
- Phase 1: Interest-only payment for I/O period
- Phase 2: Amortizing payment calculated on remaining principal over remaining term

## Output: Texas TILA Disclosure PNG

### Required Disclosure Elements (Reg Z format)
```
┌─────────────────────────────────────────────────────────────────┐
│                    TRUTH IN LENDING DISCLOSURE                  │
├─────────────────┬─────────────────┬─────────────────┬───────────┤
│ ANNUAL          │ FINANCE         │ AMOUNT          │ TOTAL OF  │
│ PERCENTAGE      │ CHARGE          │ FINANCED        │ PAYMENTS  │
│ RATE            │                 │                 │           │
│                 │ The dollar      │ The amount of   │ The amount│
│ The cost of     │ amount the      │ credit provided │ you will  │
│ your credit     │ credit will     │ to you or on    │ have paid │
│ as a yearly     │ cost you.       │ your behalf.    │ after you │
│ rate.           │                 │                 │ have made │
│                 │                 │                 │ all       │
│                 │                 │                 │ payments  │
│                 │                 │                 │ as        │
│                 │                 │                 │ scheduled.│
│                 │                 │                 │           │
│    X.XX%        │   $XX,XXX.XX    │   $XXX,XXX.XX   │$XXX,XXX.XX│
└─────────────────┴─────────────────┴─────────────────┴───────────┘

Your payment schedule will be:
  Number of Payments    Amount of Payments    When Payments Are Due
  ──────────────────    ──────────────────    ─────────────────────
  XXX                   $X,XXX.XX             Monthly beginning [DATE]
  1                     $XXX,XXX.XX           [BALLOON DATE] (Balloon)

```

### Image Specifications
- Format: PNG
- Resolution: 300 DPI (print-quality)
- Background: White
- Font: Monospace or clean sans-serif
- Border: Black, 2px
- Dimensions: ~8.5" × 5" (standard half-letter)

## File Structure
```
seller-financing-calculator/
├── app.py                 # Main Streamlit application
├── calculations.py        # Financial calculation functions
├── disclosure.py          # TILA disclosure image generation
├── pdf_generator.py       # Comparison PDF with all 3 amortization schedules
├── requirements.txt       # Python dependencies
├── README.md              # Deployment guide
└── PLAN.md               # This file
```

## Implementation Steps

### Step 1: Project Setup
- Create directory structure
- Create requirements.txt with dependencies
- Initialize basic Streamlit app

### Step 2: Financial Calculations Module
- Implement standard amortization formula
- Implement interest-only calculation
- Implement hybrid calculation (I/O period + amortizing)
- APR calculation
- Finance charge calculation
- Total of payments calculation

### Step 3: Streamlit UI
- Input form with all fields
- Conditional display of I/O period field (only for Hybrid)
- Calculate button
- Results display (summary before image generation)

### Step 4: TILA Disclosure Image Generation
- Create disclosure layout using Pillow
- Draw bordered boxes per Reg Z format
- Render text with proper formatting
- Add payment schedule section
- Export as PNG with download button

### Step 5: Testing & Validation
- Test all three loan types
- Verify calculations against known amortization tables
- Test edge cases (0% interest, short terms, etc.)

### Step 6: Deployment
- Create GitHub repository
- Connect to Streamlit Community Cloud
- Document custom domain setup (optional)

## Dependencies (requirements.txt)
```
streamlit>=1.28.0
pillow>=10.0.0
numpy>=1.24.0
reportlab>=4.0.0
```

## Deployment Guide (README.md content)

### Streamlit Community Cloud Deployment
1. Push code to GitHub repository
2. Go to share.streamlit.io
3. Connect GitHub account
4. Select repository and app.py
5. Deploy

### Custom Domain (Optional)
1. In Streamlit Cloud dashboard, go to app settings
2. Add custom domain
3. Configure DNS:
   - CNAME record pointing to [app-name].streamlit.app
   - Or A record to Streamlit's IP (check their docs)
4. Wait for SSL provisioning
