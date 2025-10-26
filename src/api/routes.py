"""FastAPI routes for Stryktips Bot."""

import logging
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.models import Coupon, Match, SuggestedRow
from src.jobs.update_coupon import update_coupon_data

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Home page - show latest coupon."""
    # Get latest active coupon
    coupon = db.query(Coupon).filter(Coupon.is_active == True).order_by(
        Coupon.week_number.desc()
    ).first()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "coupon": coupon,
        },
    )


@router.get("/coupon/{coupon_id}", response_class=HTMLResponse)
async def get_coupon(
    request: Request, coupon_id: int, db: Session = Depends(get_db)
) -> HTMLResponse:
    """Show specific coupon with analysis."""
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    # Get suggested rows
    suggested_rows = db.query(SuggestedRow).filter(
        SuggestedRow.coupon_id == coupon_id
    ).order_by(SuggestedRow.expected_value.desc()).all()

    return templates.TemplateResponse(
        "coupon.html",
        {
            "request": request,
            "coupon": coupon,
            "suggested_rows": suggested_rows,
        },
    )


@router.get("/analysis/{coupon_id}", response_class=HTMLResponse)
async def get_analysis(
    request: Request, coupon_id: int, db: Session = Depends(get_db)
) -> HTMLResponse:
    """Show detailed analysis for a coupon."""
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    # Get suggested rows
    suggested_rows = db.query(SuggestedRow).filter(
        SuggestedRow.coupon_id == coupon_id
    ).order_by(SuggestedRow.expected_value.desc()).all()

    return templates.TemplateResponse(
        "analysis.html",
        {
            "request": request,
            "coupon": coupon,
            "suggested_rows": suggested_rows,
        },
    )


@router.post("/refresh", response_class=HTMLResponse)
async def refresh_coupon(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Manually trigger coupon update (HTMX endpoint)."""
    try:
        logger.info("Manual refresh triggered")
        coupon = await update_coupon_data(db)

        # Return updated coupon partial
        return templates.TemplateResponse(
            "components/coupon_summary.html",
            {
                "request": request,
                "coupon": coupon,
            },
        )
    except Exception as e:
        logger.error(f"Failed to refresh coupon: {e}")
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for K8s."""
    return {"status": "healthy"}
