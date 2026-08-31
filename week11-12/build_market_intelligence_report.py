"""Build the one-page Irvine market intelligence report as a PDF."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


WEEK_DIR = Path(__file__).resolve().parent
DEFAULT_METRICS = WEEK_DIR / "irvine_market_metrics.json"
DEFAULT_OUTPUT = WEEK_DIR / "irvine_market_intelligence_report.pdf"

NAVY = HexColor("#17365D")
BLUE = HexColor("#4F81BD")
LIGHT_BLUE = HexColor("#EAF2F8")
PALE_BLUE = HexColor("#F5F9FC")
ORANGE = HexColor("#F28E2B")
INK = HexColor("#20262E")
MUTED = HexColor("#5D6875")
GRID = HexColor("#D9E1E8")


def money(value: float, decimals: int = 1) -> str:
    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:.{decimals}f}B"
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.{decimals}f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:.0f}K"
    return f"${value:,.0f}"


def signed_percent(value: float) -> str:
    return f"{value:+.1f}%"


def draw_wrapped_text(
    pdf: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    font: str = "Helvetica",
    size: float = 8.5,
    leading: float = 11,
    color=INK,
) -> float:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if stringWidth(candidate, font, size) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    pdf.setFont(font, size)
    pdf.setFillColor(color)
    for line in lines:
        pdf.drawString(x, y, line)
        y -= leading
    return y


def draw_kpi(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    label: str,
    value: str,
    comparison: str,
) -> None:
    pdf.setFillColor(PALE_BLUE)
    pdf.roundRect(x, y, width, 72, 5, fill=1, stroke=0)
    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica-Bold", 17)
    pdf.drawString(x + 10, y + 39, value)
    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica-Bold", 7.3)
    pdf.drawString(x + 10, y + 57, label.upper())
    pdf.setFont("Helvetica", 7.2)
    pdf.drawString(x + 10, y + 18, comparison)


def draw_price_trend(
    pdf: canvas.Canvas, monthly: list[dict[str, object]], x: float, y: float
) -> None:
    width, height = 250, 105
    data = monthly[-12:]
    values = [float(row["median_close_price"]) for row in data]
    minimum = min(values) * 0.97
    maximum = max(values) * 1.03
    span = maximum - minimum or 1

    pdf.setFillColor(INK)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(x, y + height + 18, "Median close price trend")
    pdf.setFont("Helvetica", 7)
    pdf.setFillColor(MUTED)
    pdf.drawString(x, y + height + 7, "May 2025-April 2026")

    for step in range(3):
        grid_y = y + step * height / 2
        pdf.setStrokeColor(GRID)
        pdf.setLineWidth(0.5)
        pdf.line(x, grid_y, x + width, grid_y)
        label_value = minimum + step * span / 2
        pdf.setFillColor(MUTED)
        pdf.setFont("Helvetica", 6)
        pdf.drawRightString(x - 4, grid_y - 2, money(label_value, 2))

    points = []
    for index, value in enumerate(values):
        point_x = x + index * width / (len(values) - 1)
        point_y = y + (value - minimum) / span * height
        points.append((point_x, point_y))
    pdf.setStrokeColor(BLUE)
    pdf.setLineWidth(2)
    path = pdf.beginPath()
    path.moveTo(*points[0])
    for point in points[1:]:
        path.lineTo(*point)
    pdf.drawPath(path, stroke=1, fill=0)
    pdf.setFillColor(BLUE)
    for point in points:
        pdf.circle(point[0], point[1], 2.2, fill=1, stroke=0)
    for index in (0, 3, 6, 9, 11):
        pdf.setFillColor(MUTED)
        pdf.setFont("Helvetica", 6)
        pdf.drawCentredString(points[index][0], y - 10, str(data[index]["month"])[5:])


def draw_activity_comparison(
    pdf: canvas.Canvas,
    latest: dict[str, object],
    prior: dict[str, object],
    x: float,
    y: float,
) -> None:
    width, height = 215, 105
    categories = ["New listings", "Closed sales"]
    current_values = [int(latest["new_listings"]), int(latest["closed_sales"])]
    prior_values = [int(prior["new_listings"]), int(prior["closed_sales"])]
    maximum = max(current_values + prior_values) * 1.12

    pdf.setFillColor(INK)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(x, y + height + 18, "April market activity")
    pdf.setFont("Helvetica", 7)
    pdf.setFillColor(MUTED)
    pdf.drawString(x, y + height + 7, "2026 compared with 2025")

    group_width = width / 2
    for index, category in enumerate(categories):
        center = x + group_width * index + group_width / 2
        for offset, (value, color) in enumerate(
            ((prior_values[index], GRID), (current_values[index], BLUE))
        ):
            bar_width = 27
            bar_x = center - 31 + offset * 34
            bar_height = value / maximum * height
            pdf.setFillColor(color)
            pdf.rect(bar_x, y, bar_width, bar_height, fill=1, stroke=0)
            pdf.setFillColor(INK)
            pdf.setFont("Helvetica-Bold", 6.5)
            pdf.drawCentredString(bar_x + bar_width / 2, y + bar_height + 4, str(value))
        pdf.setFillColor(MUTED)
        pdf.setFont("Helvetica", 6.5)
        pdf.drawCentredString(center, y - 10, category)
    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica", 6.2)
    pdf.drawString(x + width - 92, y + height + 7, "Gray: 2025  Blue: 2026")


def draw_competitor_list(
    pdf: canvas.Canvas,
    title: str,
    rows: list[dict[str, object]],
    x: float,
    y: float,
    width: float,
) -> None:
    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica-Bold", 8.5)
    pdf.drawString(x, y, title)
    pdf.setStrokeColor(GRID)
    pdf.line(x, y - 5, x + width, y - 5)
    row_y = y - 20
    for index, row in enumerate(rows[:3], 1):
        name = str(row["name"])
        if len(name) > 31:
            name = name[:29] + "..."
        pdf.setFillColor(INK)
        pdf.setFont("Helvetica-Bold", 7.2)
        pdf.drawString(x, row_y, f"{index}. {name}")
        pdf.setFillColor(MUTED)
        pdf.setFont("Helvetica", 7)
        pdf.drawRightString(
            x + width,
            row_y,
            f"{money(float(row['sales_volume']))} | {int(row['units_sold'])} units",
        )
        row_y -= 17


def build_report(metrics_path: Path, output_path: Path) -> None:
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    latest = metrics["latest_month"]
    prior = metrics["year_ago_month"]
    changes = metrics["changes"]
    current_12m = metrics["current_trailing_12_months"]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output_path), pagesize=letter)
    page_width, page_height = letter
    pdf.setTitle("Irvine Market Intelligence Brief")
    pdf.setAuthor("Peggy Chiu")

    pdf.setFillColor(NAVY)
    pdf.rect(0, page_height - 78, page_width, 78, fill=1, stroke=0)
    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 21)
    pdf.drawString(36, page_height - 39, "Irvine Market Intelligence Brief")
    pdf.setFont("Helvetica", 8.5)
    pdf.drawString(
        36,
        page_height - 58,
        "Orange County, California | Clean Residential MLS records | April 2026",
    )

    kpi_y = 620
    card_width = 127
    gap = 10
    draw_kpi(
        pdf,
        36,
        kpi_y,
        card_width,
        "Median close price",
        money(float(latest["median_close_price"]), 2),
        f"{signed_percent(float(changes['median_close_price_yoy_pct']))} year over year",
    )
    draw_kpi(
        pdf,
        36 + (card_width + gap),
        kpi_y,
        card_width,
        "Average days on market",
        f"{float(latest['average_days_on_market']):.1f} days",
        f"{float(changes['days_on_market_yoy_days']):+.1f} days year over year",
    )
    draw_kpi(
        pdf,
        36 + 2 * (card_width + gap),
        kpi_y,
        card_width,
        "Median price per sq. ft.",
        f"${float(latest['median_price_per_sq_ft']):,.0f}",
        f"{signed_percent(float(changes['price_per_sq_ft_yoy_pct']))} year over year",
    )
    draw_kpi(
        pdf,
        36 + 3 * (card_width + gap),
        kpi_y,
        card_width,
        "Close-to-original-list ratio",
        f"{float(latest['average_close_to_original_list_ratio']) * 100:.1f}%",
        "Average for April closed sales",
    )

    draw_price_trend(pdf, metrics["monthly"], 62, 466)
    draw_activity_comparison(pdf, latest, prior, 355, 466)

    pdf.setFillColor(LIGHT_BLUE)
    pdf.roundRect(36, 320, 540, 118, 5, fill=1, stroke=0)
    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(48, 418, "Competitive landscape - trailing 12 months")
    draw_competitor_list(pdf, "Top listing agents", metrics["top_agents"], 48, 398, 238)
    draw_competitor_list(pdf, "Top listing offices", metrics["top_offices"], 318, 398, 246)

    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(36, 296, "Key takeaways")
    takeaways = [
        (
            f"Pricing softened: the April median close price was "
            f"{money(float(latest['median_close_price']), 2)}, "
            f"{abs(float(changes['median_close_price_yoy_pct'])):.1f}% below April 2025."
        ),
        (
            f"Homes took longer to sell: average market time increased by "
            f"{float(changes['days_on_market_yoy_days']):.1f} days to "
            f"{float(latest['average_days_on_market']):.1f} days."
        ),
        (
            f"April activity improved year over year, with {int(latest['new_listings'])} "
            f"new listings and {int(latest['closed_sales'])} closed sales."
        ),
        (
            f"The latest 12-month sales volume was {money(float(current_12m['sales_volume']))}, "
            f"down {abs(float(changes['trailing_12m_sales_volume_pct'])):.1f}% from the prior period."
        ),
        (
            f"Broker competition remained fragmented: the leading office held only "
            f"{float(metrics['top_office_volume_share_pct']):.1f}% of Irvine sales volume."
        ),
    ]
    bullet_y = 277
    for takeaway in takeaways:
        pdf.setFillColor(BLUE)
        pdf.circle(41, bullet_y + 2, 2.2, fill=1, stroke=0)
        bullet_y = draw_wrapped_text(pdf, takeaway, 49, bullet_y, 522, size=8.1, leading=10)
        bullet_y -= 4

    pdf.setFillColor(PALE_BLUE)
    pdf.roundRect(36, 86, 540, 70, 5, fill=1, stroke=0)
    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(48, 137, "Market interpretation")
    draw_wrapped_text(
        pdf,
        (
            "Irvine is shifting toward a more balanced market: buyers gained some "
            "pricing leverage and more time to decide, while April transaction "
            "activity remained resilient. Sellers should price close to current "
            "comparables and expect longer marketing periods than a year ago."
        ),
        48,
        121,
        516,
        size=8.2,
        leading=10.5,
    )

    pdf.setStrokeColor(GRID)
    pdf.line(36, 60, 576, 60)
    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica", 6.4)
    pdf.drawString(
        36,
        46,
        "Source: IDX Exchange cleaned Residential MLS analysis datasets. "
        "April 2026 is the latest complete market-activity month; closed-sale coverage extends through June 2026.",
    )
    pdf.drawString(
        36,
        35,
        "Method: Week 7 IQR-filtered records; medians for price and price per sq. ft.; averages for days on market and close-to-original-list ratio.",
    )
    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica-Bold", 7)
    pdf.drawRightString(576, 35, "Prepared by Peggy Chiu")
    pdf.showPage()
    pdf.save()
    print(f"Created {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_report(args.metrics, args.output)


if __name__ == "__main__":
    main()
