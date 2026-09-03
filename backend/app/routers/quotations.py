from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user
from app.database import get_db
from app.models import Quotation, QuoteLineItem, QuoteStatus, User
from app.pdf import render_quotation_html, render_quotation_pdf
from app.quote_numbering import generate_quote_number
from app.schemas.schemas import QuotationCreate, QuotationListOut, QuotationOut, QuotationUpdate

router = APIRouter(prefix="/quotations", tags=["quotations"], dependencies=[Depends(get_current_user)])


def _with_relations(query):
    return query.options(joinedload(Quotation.customer), joinedload(Quotation.line_items))


@router.get("", response_model=list[QuotationListOut])
def list_quotations(include_archived: bool = False, db: Session = Depends(get_db)):
    query = _with_relations(db.query(Quotation))
    if not include_archived:
        query = query.filter(Quotation.status != QuoteStatus.archived)
    return query.order_by(Quotation.created_at.desc()).all()


@router.post("", response_model=QuotationOut, status_code=201)
def create_quotation(
    quotation_in: QuotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = quotation_in.model_dump(exclude={"line_items", "quote_number"})
    quote_number = quotation_in.quote_number or generate_quote_number(db)
    quotation = Quotation(**data, quote_number=quote_number, created_by_id=current_user.id)
    db.add(quotation)
    db.flush()  # get quotation.id before attaching line items

    for idx, item in enumerate(quotation_in.line_items):
        item_data = item.model_dump(exclude={"sort_order"})
        db.add(QuoteLineItem(**item_data, quotation_id=quotation.id, sort_order=item.sort_order or idx))

    db.commit()
    return _with_relations(db.query(Quotation)).filter(Quotation.id == quotation.id).first()


@router.get("/{quotation_id}", response_model=QuotationOut)
def get_quotation(quotation_id: str, db: Session = Depends(get_db)):
    quotation = _with_relations(db.query(Quotation)).filter(Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return quotation


@router.put("/{quotation_id}", response_model=QuotationOut)
def update_quotation(quotation_id: str, quotation_in: QuotationUpdate, db: Session = Depends(get_db)):
    quotation = db.get(Quotation, quotation_id)
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

    update_data = quotation_in.model_dump(exclude_unset=True, exclude={"line_items"})
    for field, value in update_data.items():
        setattr(quotation, field, value)

    if quotation_in.line_items is not None:
        # Full replace is simplest and safest for a low-volume internal tool —
        # avoids diffing/matching stale line item IDs from the client.
        for item in list(quotation.line_items):
            db.delete(item)
        db.flush()
        for idx, item in enumerate(quotation_in.line_items):
            item_data = item.model_dump(exclude={"sort_order"})
            db.add(QuoteLineItem(**item_data, quotation_id=quotation.id, sort_order=item.sort_order or idx))

    db.commit()
    return _with_relations(db.query(Quotation)).filter(Quotation.id == quotation_id).first()


@router.delete("/{quotation_id}", status_code=204)
def archive_quotation(quotation_id: str, db: Session = Depends(get_db)):
    quotation = db.get(Quotation, quotation_id)
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    quotation.status = QuoteStatus.archived
    db.commit()


@router.post("/{quotation_id}/restore", response_model=QuotationOut)
def restore_quotation(quotation_id: str, db: Session = Depends(get_db)):
    quotation = db.get(Quotation, quotation_id)
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    if quotation.status == QuoteStatus.archived:
        quotation.status = QuoteStatus.draft
    db.commit()
    return _with_relations(db.query(Quotation)).filter(Quotation.id == quotation_id).first()


@router.get("/{quotation_id}/pdf")
def get_quotation_pdf(quotation_id: str, db: Session = Depends(get_db)):
    quotation = _with_relations(db.query(Quotation)).filter(Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

    quotation_out = QuotationOut.model_validate(quotation)
    pdf_bytes = render_quotation_pdf(quotation_out)
    filename = f"{quotation.quote_number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{quotation_id}/view")
def view_quotation(quotation_id: str, db: Session = Depends(get_db)):
    quotation = _with_relations(db.query(Quotation)).filter(Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

    quotation_out = QuotationOut.model_validate(quotation)
    html_content = render_quotation_html(quotation_out)
    return Response(content=html_content, media_type="text/html")
