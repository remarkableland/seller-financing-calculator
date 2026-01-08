# Seller Financing Calculator

A Streamlit web app for calculating seller financing terms with Texas TILA-compliant disclosure generation.

## Features

- **Three Loan Types:**
  - Standard Amortization (fixed P&I payments)
  - Interest-Only with Balloon (I/O payments, principal due at end)
  - Hybrid (Interest-only period followed by amortizing payments)

- **TILA Disclosure PNG:** Generate official Regulation Z format disclosure images

- **Comparison PDF:** Download full amortization schedules for all three loan types

## Local Development

### Prerequisites

- Python 3.11 or higher
- pip

### Installation

```bash
# Clone or navigate to the project directory
cd seller-financing-calculator

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running Locally

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Deployment to Streamlit Community Cloud

### Step 1: Push to GitHub

1. Create a new GitHub repository
2. Push the project files:

```bash
git init
git add .
git commit -m "Initial commit: Seller Financing Calculator"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/seller-financing-calculator.git
git push -u origin main
```

### Step 2: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click "New app"
4. Select your repository: `YOUR_USERNAME/seller-financing-calculator`
5. Set the main file path: `app.py`
6. Click "Deploy"

Your app will be live at: `https://YOUR_USERNAME-seller-financing-calculator.streamlit.app`

### Step 3: Custom Domain (Optional)

1. In the Streamlit Cloud dashboard, go to your app's settings
2. Click "Custom domain"
3. Enter your domain (e.g., `calculator.yourdomain.com`)
4. Configure your DNS:

**Option A: CNAME Record (Recommended for subdomains)**
```
Type: CNAME
Name: calculator (or your subdomain)
Value: YOUR_USERNAME-seller-financing-calculator.streamlit.app
```

**Option B: For apex domain (yourdomain.com)**
- Check Streamlit's documentation for current IP addresses
- Create A records pointing to those IPs

5. Wait for DNS propagation (up to 24-48 hours)
6. Streamlit will automatically provision an SSL certificate

## File Structure

```
seller-financing-calculator/
├── app.py              # Main Streamlit application
├── calculations.py     # Financial calculation functions
├── disclosure.py       # TILA disclosure PNG generator
├── pdf_generator.py    # Comparison PDF generator
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── PLAN.md            # Project planning document
```

## Usage

1. Enter loan parameters in the sidebar:
   - Purchase Price
   - Down Payment
   - Closing Costs (informational, not financed)
   - Interest Rate
   - Term (years)
   - Loan Type

2. For Hybrid loans, specify the interest-only period

3. Click "Calculate"

4. Review the summary and download:
   - **TILA Disclosure PNG** - For the selected loan type
   - **Comparison PDF** - All three loan types with full amortization schedules

## Calculations

### Standard Amortization
```
Monthly Payment = P × [r(1+r)^n] / [(1+r)^n - 1]

Where:
  P = Principal (Amount Financed)
  r = Monthly interest rate
  n = Number of payments
```

### Interest-Only
```
Monthly Payment = P × r

Where:
  P = Principal
  r = Monthly interest rate
```

### Hybrid
- Phase 1: Interest-only payments for specified period
- Phase 2: Fully amortizing payments over remaining term

### TILA Disclosure Values
- **APR:** Annual Percentage Rate (equals interest rate for simple seller financing)
- **Finance Charge:** Total interest paid over loan term
- **Amount Financed:** Purchase price minus down payment
- **Total of Payments:** Sum of all scheduled payments

## License

Private use. All rights reserved.
