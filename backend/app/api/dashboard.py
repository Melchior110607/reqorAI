"""
Dashboard API - Enhanced views with priority sorting and calendar
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.database.config import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.services.request_status_service import RequestStatusService


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview")
def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard overview
    
    Returns requests organized by priority, with stats
    """
    status_service = RequestStatusService(db)
    
    # Get requests organized by priority
    requests_by_priority = status_service.get_requests_by_priority_and_date(
        user_id=current_user.id,
        include_completed=False
    )
    
    # Calculate stats
    from app.models.request import Request, RequestStatus, RequestType
    
    total_requests = db.query(Request).filter(
        Request.user_id == current_user.id
    ).count()
    
    pending_count = db.query(Request).filter(
        Request.user_id == current_user.id,
        Request.status == RequestStatus.PENDING
    ).count()
    
    completed_count = db.query(Request).filter(
        Request.user_id == current_user.id,
        Request.status == RequestStatus.COMPLETED
    ).count()
    
    overdue_count = requests_by_priority['overdue_count']
    
    incoming_count = db.query(Request).filter(
        Request.user_id == current_user.id,
        Request.type == RequestType.INCOMING,
        Request.status != RequestStatus.COMPLETED
    ).count()
    
    outgoing_count = db.query(Request).filter(
        Request.user_id == current_user.id,
        Request.type == RequestType.OUTGOING,
        Request.status != RequestStatus.COMPLETED
    ).count()
    
    # Get requests with follow-ups
    follow_up_count = db.query(Request).filter(
        Request.user_id == current_user.id,
        Request.follow_up_count > 0
    ).count()
    
    return {
        "stats": {
            "total": total_requests,
            "pending": pending_count,
            "completed": completed_count,
            "overdue": overdue_count,
            "incoming_active": incoming_count,
            "outgoing_active": outgoing_count,
            "with_follow_ups": follow_up_count
        },
        "requests_by_priority": requests_by_priority,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


@router.get("/calendar")
def get_calendar_view(
    start_date: Optional[str] = Query(None, description="ISO format: YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="ISO format: YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get calendar view of requests with due dates
    
    Default: current month if no dates provided
    """
    # Parse dates or use current month
    if start_date and end_date:
        try:
            start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
            end = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    else:
        # Default to current month
        now = datetime.now(timezone.utc)
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Last day of month
        if now.month == 12:
            end = start.replace(year=now.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = start.replace(month=now.month + 1, day=1) - timedelta(days=1)
        
        end = end.replace(hour=23, minute=59, second=59)
    
    status_service = RequestStatusService(db)
    calendar_data = status_service.get_calendar_view(
        user_id=current_user.id,
        start_date=start,
        end_date=end
    )
    
    return {
        **calendar_data,
        "start_date": start.isoformat(),
        "end_date": end.isoformat()
    }


@router.get("/upcoming")
def get_upcoming_requests(
    days: int = Query(7, ge=1, le=90, description="Number of days to look ahead"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get upcoming requests in the next N days
    
    Sorted by due date (soonest first)
    """
    from app.models.request import Request, RequestStatus
    from app.models.client import Client
    from sqlalchemy.orm import joinedload
    
    now = datetime.now(timezone.utc)
    end_date = now + timedelta(days=days)
    
    upcoming = db.query(Request).outerjoin(Client).filter(
        Request.user_id == current_user.id,
        Request.due_date.isnot(None),
        Request.due_date >= now,
        Request.due_date <= end_date,
        Request.status != RequestStatus.COMPLETED
    ).order_by(Request.due_date).all()
    
    today = now.date()
    
    requests_list = []
    for req in upcoming:
        req_date = req.due_date.date()
        
        # Get client name
        client_name = None
        if req.client_id:
            client = db.query(Client).filter(Client.id == req.client_id).first()
            if client:
                client_name = client.name
        
        req_data = {
            'id': req.id,
            'title': req.title,
            'due_date': req.due_date.isoformat(),
            'priority': req.priority.value,
            'type': req.type.value,
            'status': req.status.value,
            'client_id': req.client_id,
            'client_name': client_name,
            'days_until_due': (req_date - today).days,
            'is_overdue': req.is_overdue,
            'follow_up_count': req.follow_up_count or 0,
            'is_follow_up': req.is_follow_up or False,
            'created_at': req.created_at.isoformat()
        }
        
        requests_list.append(req_data)
    
    return {
        "requests": requests_list,
        "total": len(upcoming),
        "period_days": days
    }


@router.get("/overdue-count")
def get_overdue_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get count of overdue requests
    
    Computed dynamically from due_date
    """
    status_service = RequestStatusService(db)
    count = status_service.get_overdue_count(current_user.id)
    
    return {
        "overdue_count": count
    }

