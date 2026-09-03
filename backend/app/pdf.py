from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.config import settings

TEMPLATES_DIR = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

# Category short names for the auto-generated service description headline,
# in display order. "services" is deliberately excluded — it's not rented equipment.
CATEGORY_SHORT_NAMES = {
    "led_wall": "LED Wall",
    "displays": "Displays",
    "audio": "Audio",
    "it_equipment": "Equipment",
}


def _service_description_headline(quotation) -> str | None:
    present_types = {
        li.product_type for li in quotation.line_items if li.product_type is not None
    }
    short_names = [
        label for key, label in CATEGORY_SHORT_NAMES.items() if key in present_types
    ]
    if not short_names:
        return None
    if len(short_names) == 1:
        joined = short_names[0]
    else:
        joined = ", ".join(short_names[:-1]) + " & " + short_names[-1]
    return f"End-to-End {joined} Rental and Setup"


def render_quotation_html(quotation) -> str:
    template = _env.get_template("quotation.html")
    product_names = [
        li.product.name for li in quotation.line_items if li.product is not None
    ]
    has_26mm = any(name.lower().startswith("2.6mm") for name in product_names)
    has_19mm = any(name.lower().replace(" ", "").startswith("1.9mm") for name in product_names)
    return template.render(
        quotation=quotation,
        company_name=settings.company_name,
        company_email=settings.company_email,
        company_phone=settings.company_phone,
        company_address=settings.company_address,
        has_26mm_product=has_26mm,
        has_19mm_product=has_19mm,
        service_description_headline=_service_description_headline(quotation),
    )


def render_quotation_pdf(quotation) -> bytes:
    # Imported lazily: WeasyPrint needs native GTK/Pango libs that are only
    # guaranteed present on the Linux deployment target, not on every dev machine.
    from weasyprint import HTML

    html_content = render_quotation_html(quotation)
    return HTML(string=html_content, base_url=str(TEMPLATES_DIR)).write_pdf()
