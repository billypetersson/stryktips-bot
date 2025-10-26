"""FastAPI routes for Stryktips Bot."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.models import Coupon, Match, SuggestedRow, ExpertItem
from src.jobs.update_coupon import update_coupon_data
from src.services.expert_consensus import ExpertConsensusService

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

    # Get expert consensus for each match
    from collections import Counter, defaultdict
    expert_consensus = {}
    for match in coupon.matches:
        predictions = db.query(ExpertItem).filter(ExpertItem.match_id == match.id).all()

        if predictions:
            picks = [p.pick for p in predictions]
            pick_counts = Counter(picks)
            consensus_pick = pick_counts.most_common(1)[0][0]

            # Source breakdown
            source_breakdown = defaultdict(list)
            for pred in predictions:
                source_breakdown[pred.source].append({
                    "pick": pred.pick,
                    "author": pred.author,
                })

            expert_consensus[match.id] = {
                "prediction_count": len(predictions),
                "consensus_pick": consensus_pick,
                "confidence": round(pick_counts[consensus_pick] / len(predictions), 2),
                "pick_distribution": dict(pick_counts),
                "source_breakdown": dict(source_breakdown),
            }

    return templates.TemplateResponse(
        "analysis.html",
        {
            "request": request,
            "coupon": coupon,
            "suggested_rows": suggested_rows,
            "expert_consensus": expert_consensus,
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


# Expert prediction endpoints
@router.get("/api/experts/latest")
async def get_latest_expert_predictions(
    limit: int = 50,
    source: Optional[str] = None,
    db: Session = Depends(get_db)
) -> JSONResponse:
    """Get latest expert predictions from database.

    Args:
        limit: Maximum number of predictions to return
        source: Filter by source name (optional)
        db: Database session

    Returns:
        JSON response with expert predictions
    """
    query = db.query(ExpertItem).order_by(ExpertItem.published_at.desc()).limit(limit)

    if source:
        query = query.where(ExpertItem.source == source)

    predictions = query.all()

    # Convert to dict format
    results = []
    for pred in predictions:
        results.append({
            "id": pred.id,
            "source": pred.source,
            "author": pred.author,
            "published_at": pred.published_at.isoformat(),
            "url": pred.url,
            "match_id": pred.match_id,
            "pick": pred.pick,
            "rationale": pred.rationale,
            "confidence": pred.confidence,
            "scraped_at": pred.scraped_at.isoformat(),
        })

    return JSONResponse(content={
        "count": len(results),
        "predictions": results
    })


@router.get("/api/experts/consensus/{match_id}")
async def get_expert_consensus_for_match(
    match_id: int,
    db: Session = Depends(get_db)
) -> JSONResponse:
    """Get expert consensus for a specific match.

    Args:
        match_id: Match ID
        db: Database session

    Returns:
        JSON response with consensus data
    """
    # Note: This uses sync Session, but ExpertConsensusService expects AsyncSession
    # For now, we'll query directly
    predictions = db.query(ExpertItem).filter(ExpertItem.match_id == match_id).all()

    if not predictions:
        return JSONResponse(content={
            "match_id": match_id,
            "prediction_count": 0,
            "consensus_pick": None,
            "pick_distribution": {},
        })

    # Count picks
    from collections import Counter
    picks = [p.pick for p in predictions]
    pick_counts = Counter(picks)

    consensus_pick = pick_counts.most_common(1)[0][0]
    consensus_count = pick_counts[consensus_pick]
    confidence = consensus_count / len(predictions)

    # Source breakdown
    from collections import defaultdict
    source_breakdown = defaultdict(list)
    for pred in predictions:
        source_breakdown[pred.source].append({
            "pick": pred.pick,
            "author": pred.author,
            "published_at": pred.published_at.isoformat() if pred.published_at else None,
            "url": pred.url,
            "rationale": pred.rationale,
        })

    return JSONResponse(content={
        "match_id": match_id,
        "prediction_count": len(predictions),
        "consensus_pick": consensus_pick,
        "confidence": round(confidence, 2),
        "pick_distribution": dict(pick_counts),
        "source_breakdown": dict(source_breakdown),
    })


@router.get("/api/experts/consensus/coupon/{coupon_id}")
async def get_expert_consensus_for_coupon(
    coupon_id: int,
    db: Session = Depends(get_db)
) -> JSONResponse:
    """Get expert consensus for all matches in a coupon.

    Args:
        coupon_id: Coupon ID
        db: Database session

    Returns:
        JSON response with consensus data per match
    """
    # Get all matches for this coupon
    matches = db.query(Match).filter(Match.coupon_id == coupon_id).order_by(Match.match_number).all()

    consensus_list = []
    for match in matches:
        # Get predictions for this match
        predictions = db.query(ExpertItem).filter(ExpertItem.match_id == match.id).all()

        if predictions:
            from collections import Counter
            picks = [p.pick for p in predictions]
            pick_counts = Counter(picks)

            consensus_pick = pick_counts.most_common(1)[0][0]
            consensus_count = pick_counts[consensus_pick]
            confidence = consensus_count / len(predictions)
        else:
            consensus_pick = None
            confidence = 0.0
            pick_counts = {}

        consensus_list.append({
            "match_id": match.id,
            "match_number": match.match_number,
            "home_team": match.home_team,
            "away_team": match.away_team,
            "prediction_count": len(predictions),
            "consensus_pick": consensus_pick,
            "confidence": round(confidence, 2) if confidence else 0.0,
            "pick_distribution": dict(pick_counts),
        })

    return JSONResponse(content={
        "coupon_id": coupon_id,
        "matches": consensus_list,
    })


@router.get("/experts", response_class=HTMLResponse)
async def experts_page(
    request: Request,
    source: Optional[str] = None,
    db: Session = Depends(get_db)
) -> HTMLResponse:
    """Show expert predictions page.

    Args:
        request: FastAPI request
        source: Filter by source (optional)
        db: Database session

    Returns:
        HTML response
    """
    # Get latest predictions
    query = db.query(ExpertItem).order_by(ExpertItem.published_at.desc()).limit(100)

    if source:
        query = query.filter(ExpertItem.source == source)

    predictions = query.all()

    # Get all unique sources for filter dropdown
    all_sources = db.query(ExpertItem.source).distinct().all()
    sources = [s[0] for s in all_sources]

    return templates.TemplateResponse(
        "experts.html",
        {
            "request": request,
            "predictions": predictions,
            "sources": sources,
            "selected_source": source,
        },
    )
