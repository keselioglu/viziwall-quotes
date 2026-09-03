from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.config import settings

TEMPLATES_DIR = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))


def render_quotation_html(quotation) -> str:
    template = _env.get_template("quotation.html")
    return template.render(
        quotation=quotation,
        company_name=settings.company_name,
        company_email=settings.company_email,
        company_phone=settings.company_phone,
        company_address=settings.company_address,
    )


def render_quotation_pdf(quotation) -> bytes:
    # Imported lazily: WeasyPrint needs native GTK/Pango libs that are only
    # guaranteed present on the Linux deployment target, not on every dev machine.
    from weasyprint import HTML

    html_content = render_quotation_html(quotation)
    return HTML(string=html_content, base_url=str(TEMPLATES_DIR)).write_pdf()
