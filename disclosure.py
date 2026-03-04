"""
TILA Disclosure PNG generator for Texas seller financing.
Generates official Regulation Z format disclosure box.
"""

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from calculations import LoanSummary


# Image dimensions - 850px wide (letter-width at 100 DPI) for screen readability
WIDTH = 850
DPI = 100
MARGIN = 30
BORDER_WIDTH = 2

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get a font, falling back to default if custom fonts unavailable."""
    try:
        if bold:
            return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size, index=1)
        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size, index=0)
    except (OSError, IOError):
        try:
            if bold:
                return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
            return ImageFont.truetype("DejaVuSans.ttf", size)
        except (OSError, IOError):
            try:
                return ImageFont.load_default(size=size)
            except TypeError:
                return ImageFont.load_default()


def format_currency(amount: float) -> str:
    """Format number as currency."""
    return f"${amount:,.2f}"


def format_percent(rate: float) -> str:
    """Format number as percentage."""
    return f"{rate:.3f}%"


def draw_centered_text(draw: ImageDraw, text: str, x: int, y: int, width: int, font: ImageFont, fill=BLACK):
    """Draw text centered within a given width."""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    draw.text((x + (width - text_width) // 2, y), text, font=font, fill=fill)


def draw_wrapped_text(draw: ImageDraw, text: str, x: int, y: int, width: int, font: ImageFont, fill=BLACK, line_height: int = None):
    """Draw text wrapped within a given width."""
    if line_height is None:
        line_height = font.size + 4

    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    for i, line in enumerate(lines):
        draw.text((x, y + i * line_height), line, font=font, fill=fill)

    return y + len(lines) * line_height


def generate_tila_disclosure(summary: LoanSummary) -> bytes:
    """
    Generate TILA disclosure image in Regulation Z format.

    Args:
        summary: LoanSummary object with calculated values

    Returns:
        PNG image as bytes
    """
    # Create image with max possible height (will be cropped later)
    img = Image.new('RGB', (WIDTH, 1200), WHITE)
    draw = ImageDraw.Draw(img)

    # Fonts - sized for 850px wide canvas (screen-readable)
    title_font = get_font(22, bold=True)
    header_font = get_font(16, bold=True)
    desc_font = get_font(11)
    value_font = get_font(20, bold=True)
    schedule_font = get_font(14)
    small_font = get_font(11)

    # Title
    title = "TRUTH IN LENDING DISCLOSURE"
    draw_centered_text(draw, title, MARGIN, MARGIN, WIDTH - 2 * MARGIN, title_font)

    # Main disclosure box
    box_top = MARGIN + 40
    box_left = MARGIN
    box_right = WIDTH - MARGIN
    box_bottom = box_top + 220
    box_width = box_right - box_left
    col_width = box_width // 4

    # Outer border
    draw.rectangle([box_left, box_top, box_right, box_bottom], outline=BLACK, width=BORDER_WIDTH)

    # Column dividers
    for i in range(1, 4):
        x = box_left + col_width * i
        draw.line([(x, box_top), (x, box_bottom)], fill=BLACK, width=BORDER_WIDTH)

    # Column headers and descriptions
    columns = [
        {
            "header": "ANNUAL\nPERCENTAGE\nRATE",
            "description": "The cost of your credit as a yearly rate.",
            "value": format_percent(summary.apr)
        },
        {
            "header": "FINANCE\nCHARGE",
            "description": "The dollar amount the credit will cost you.",
            "value": format_currency(summary.finance_charge)
        },
        {
            "header": "AMOUNT\nFINANCED",
            "description": "The amount of credit provided to you or on your behalf.",
            "value": format_currency(summary.amount_financed)
        },
        {
            "header": "TOTAL OF\nPAYMENTS",
            "description": "The amount you will have paid after you have made all payments as scheduled.",
            "value": format_currency(summary.total_of_payments)
        }
    ]

    for i, col in enumerate(columns):
        col_x = box_left + col_width * i + 8
        col_content_width = col_width - 16

        # Header
        header_y = box_top + 8
        for j, line in enumerate(col["header"].split("\n")):
            draw_centered_text(draw, line, col_x, header_y + j * 18, col_content_width, header_font)

        # Description
        desc_y = box_top + 72
        draw_wrapped_text(draw, col["description"], col_x, desc_y, col_content_width, desc_font, line_height=14)

        # Value
        value_y = box_bottom - 35
        draw_centered_text(draw, col["value"], col_x, value_y, col_content_width, value_font)

    # Payment Schedule section
    schedule_top = box_bottom + 25
    draw.text((MARGIN, schedule_top), "Your payment schedule will be:", font=header_font, fill=BLACK)

    # Schedule table header
    table_top = schedule_top + 28
    col_widths = [200, 200, 280]
    headers = ["Number of Payments", "Amount of Payments", "When Payments Are Due"]

    x = MARGIN
    for i, (hdr, w) in enumerate(zip(headers, col_widths)):
        draw.text((x, table_top), hdr, font=schedule_font, fill=BLACK)
        x += w

    # Underline
    draw.line([(MARGIN, table_top + 20), (MARGIN + sum(col_widths), table_top + 20)], fill=BLACK, width=1)

    # Schedule rows
    row_y = table_top + 28
    row_height = 24

    if summary.loan_type == "Standard Amortization":
        x = MARGIN
        draw.text((x, row_y), str(summary.num_payments), font=schedule_font, fill=BLACK)
        x += col_widths[0]
        draw.text((x, row_y), format_currency(summary.monthly_payment), font=schedule_font, fill=BLACK)
        x += col_widths[1]
        draw.text((x, row_y), "Monthly", font=schedule_font, fill=BLACK)

    elif summary.loan_type == "Interest-Only with Balloon":
        x = MARGIN
        draw.text((x, row_y), str(summary.num_payments - 1), font=schedule_font, fill=BLACK)
        x += col_widths[0]
        draw.text((x, row_y), format_currency(summary.monthly_payment), font=schedule_font, fill=BLACK)
        x += col_widths[1]
        draw.text((x, row_y), "Monthly (Interest Only)", font=schedule_font, fill=BLACK)

        row_y += row_height
        x = MARGIN
        draw.text((x, row_y), "1", font=schedule_font, fill=BLACK)
        x += col_widths[0]
        draw.text((x, row_y), format_currency(summary.balloon_amount + summary.monthly_payment), font=schedule_font, fill=BLACK)
        x += col_widths[1]
        draw.text((x, row_y), f"Final Payment (Balloon - Month {summary.num_payments})", font=schedule_font, fill=BLACK)

    elif summary.loan_type == "Hybrid (Interest-Only + Amortizing)":
        x = MARGIN
        draw.text((x, row_y), str(summary.num_io_payments), font=schedule_font, fill=BLACK)
        x += col_widths[0]
        draw.text((x, row_y), format_currency(summary.monthly_payment), font=schedule_font, fill=BLACK)
        x += col_widths[1]
        draw.text((x, row_y), "Monthly (Interest Only)", font=schedule_font, fill=BLACK)

        row_y += row_height
        x = MARGIN
        num_amort = summary.num_payments - summary.num_io_payments
        draw.text((x, row_y), str(num_amort), font=schedule_font, fill=BLACK)
        x += col_widths[0]
        draw.text((x, row_y), format_currency(summary.monthly_payment_amortizing), font=schedule_font, fill=BLACK)
        x += col_widths[1]
        draw.text((x, row_y), "Monthly (Principal & Interest)", font=schedule_font, fill=BLACK)

    # Transaction Summary section
    content_bottom = row_y + 30
    trans_section_y = content_bottom + 15
    draw.text((MARGIN, trans_section_y), "Transaction Summary:", font=header_font, fill=BLACK)

    trans_y = trans_section_y + 28
    line_height = 20

    draw.text((MARGIN, trans_y), "Purchase Price:", font=schedule_font, fill=BLACK)
    draw.text((MARGIN + 240, trans_y), format_currency(summary.purchase_price), font=schedule_font, fill=BLACK)
    trans_y += line_height

    draw.text((MARGIN, trans_y), "Down Payment:", font=schedule_font, fill=BLACK)
    draw.text((MARGIN + 240, trans_y), format_currency(summary.down_payment), font=schedule_font, fill=BLACK)
    trans_y += line_height

    draw.text((MARGIN, trans_y), "Amount Financed:", font=schedule_font, fill=BLACK)
    draw.text((MARGIN + 240, trans_y), format_currency(summary.amount_financed), font=schedule_font, fill=BLACK)
    trans_y += line_height

    draw.text((MARGIN, trans_y), "Closing Costs:", font=schedule_font, fill=BLACK)
    draw.text((MARGIN + 240, trans_y), format_currency(summary.closing_costs), font=schedule_font, fill=BLACK)
    trans_y += line_height

    draw.text((MARGIN, trans_y), "Monthly Servicing Fee:", font=schedule_font, fill=BLACK)
    draw.text((MARGIN + 240, trans_y), format_currency(summary.monthly_servicing_fee), font=schedule_font, fill=BLACK)
    trans_y += line_height

    # Divider line
    draw.line([(MARGIN, trans_y + 4), (MARGIN + 380, trans_y + 4)], fill=BLACK, width=1)
    trans_y += 12

    amount_due = summary.down_payment + summary.closing_costs
    draw.text((MARGIN, trans_y), "Amount Due at Closing:", font=schedule_font, fill=BLACK)
    draw.text((MARGIN + 240, trans_y), format_currency(amount_due), font=schedule_font, fill=BLACK)
    trans_y += line_height + 10

    # Loan type indicator
    loan_type_y = trans_y + 10
    draw.text((MARGIN, loan_type_y), f"Loan Type: {summary.loan_type}", font=small_font, fill=GRAY)

    # Footer
    footer_y = loan_type_y + 22
    draw.text((MARGIN, footer_y), "This disclosure is provided in accordance with the Truth in Lending Act (Regulation Z).",
              font=small_font, fill=GRAY)

    # Disclaimer
    disclaimer_y = footer_y + 18
    draw.text((MARGIN, disclaimer_y),
              "This disclosure is provided for informational purposes only and does not constitute a commitment or guarantee of credit.",
              font=small_font, fill=GRAY)
    disclaimer_y2 = disclaimer_y + 16
    draw.text((MARGIN, disclaimer_y2),
              "Actual terms are subject to final contract and applicable law.",
              font=small_font, fill=GRAY)
    disclaimer_y3 = disclaimer_y2 + 16
    draw.text((MARGIN, disclaimer_y3),
              "Monthly payment does not include property taxes, insurance, or other expenses which are the buyer's responsibility.",
              font=small_font, fill=GRAY)

    # Crop image to actual content height
    final_height = disclaimer_y3 + 30
    img = img.crop((0, 0, WIDTH, final_height))

    # Convert to bytes
    buffer = BytesIO()
    img.save(buffer, format='PNG', dpi=(DPI, DPI))
    buffer.seek(0)
    return buffer.getvalue()
