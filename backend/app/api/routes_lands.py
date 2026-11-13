from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Response
from app.models.land import LandListing, LandFilterParams, LandComparisonRequest
from app.services.land_service import land_service
from app.services.report_service import report_service

router = APIRouter(prefix="/api/lands", tags=["Lands"])

@router.get("", response_model=List[LandListing])
def get_lands(
    district: Optional[str] = Query(None),
    min_acres: Optional[float] = Query(None),
    max_acres: Optional[float] = Query(None),
    max_budget_lakhs: Optional[float] = Query(None),
    land_type: Optional[str] = Query(None),
    legal_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    params = LandFilterParams(
        district=district,
        min_acres=min_acres,
        max_acres=max_acres,
        max_budget_lakhs=max_budget_lakhs,
        land_type=land_type,
        legal_status=legal_status,
        search=search
    )
    return land_service.get_all(params)

@router.get("/stats")
def get_stats():
    return land_service.get_stats()

@router.get("/{land_id}", response_model=LandListing)
def get_land(land_id: str):
    land = land_service.get_by_id(land_id)
    if not land:
        raise HTTPException(status_code=404, detail=f"Land listing '{land_id}' not found.")
    return land

@router.post("/compare", response_model=List[LandListing])
def compare_lands(req: LandComparisonRequest):
    if not req.land_ids:
        raise HTTPException(status_code=400, detail="Please provide at least one land id to compare.")
    return land_service.compare(req.land_ids)

@router.get("/{land_id}/report")
def get_land_report(land_id: str):
    land = land_service.get_by_id(land_id)
    if not land:
        raise HTTPException(status_code=404, detail=f"Land listing '{land_id}' not found.")

    pdf_bytes = report_service.generate_land_report(land)
    filename = f"BhoomiVaani_Report_{land.id}_{land.survey_number.replace('/', '_')}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
