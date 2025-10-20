"""
Request Status Service - Manage automatic status updates based on due dates
"""
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.models.request import Request, RequestStatus


class RequestStatusService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_overdue_count(self, user_id: int) -> int:
        """
        Count requests that are overdue
        
        Uses dynamic calculation based on due_date, no DB update needed.
        """
        now = datetime.now(timezone.utc)
        
        overdue_count = self.db.query(Request).filter(
            Request.user_id == user_id,
            Request.status == RequestStatus.PENDING,
            Request.due_date.isnot(None),
            Request.due_date < now
        ).count()
        
        return overdue_count
    
    def get_requests_by_priority_and_date(
        self, 
        user_id: int,
        include_completed: bool = False
    ) -> Dict[str, Any]:
        """
        Get requests organized by priority and sorted by due date
        
        Used for dashboard view.
        """
        from app.models.request import RequestPriority
        
        query = self.db.query(Request).filter(Request.user_id == user_id)
        
        if not include_completed:
            query = query.filter(Request.status != RequestStatus.COMPLETED)
        
        # Get all requests
        all_requests = query.all()
        
        # Organize by priority
        by_priority = {
            'urgent': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        for req in all_requests:
            priority_key = req.priority.value
            by_priority[priority_key].append({
                'id': req.id,
                'title': req.title,
                'status': req.status.value,
                'type': req.type.value,
                'due_date': req.due_date,
                'created_at': req.created_at,
                'client_id': req.client_id,
                'is_overdue': req.is_overdue,  # Use computed property
                'days_until_due': req.days_until_due,  # Use computed property
                'follow_up_count': req.follow_up_count,
                'is_follow_up': req.is_follow_up,
                'computed_status': req.computed_status.value  # Actual status with overdue check
            })
        
        # Sort each priority group by due date (soonest first)
        for priority in by_priority:
            by_priority[priority].sort(
                key=lambda x: x['due_date'] if x['due_date'] else datetime.max.replace(tzinfo=timezone.utc)
            )
        
        return {
            'urgent': by_priority['urgent'],
            'high': by_priority['high'],
            'medium': by_priority['medium'],
            'low': by_priority['low'],
            'total': len(all_requests),
            'overdue_count': len([r for r in all_requests if r.is_overdue])  # Use computed property
        }
    
    def get_calendar_view(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get requests for calendar view between start_date and end_date
        
        Groups by date for calendar display.
        """
        from app.models.client import Client
        
        requests = self.db.query(Request).filter(
            Request.user_id == user_id,
            Request.due_date.isnot(None),
            Request.due_date >= start_date,
            Request.due_date <= end_date,
            Request.status != RequestStatus.COMPLETED  # Exclude completed requests
        ).order_by(Request.due_date).all()
        
        # Group by date
        calendar_data = {}
        
        for req in requests:
            date_key = req.due_date.date().isoformat()
            
            if date_key not in calendar_data:
                calendar_data[date_key] = []
            
            # Get client name
            client_name = None
            if req.client_id:
                client = self.db.query(Client).filter(Client.id == req.client_id).first()
                if client:
                    client_name = client.name
            
            calendar_data[date_key].append({
                'id': req.id,
                'title': req.title,
                'status': req.status.value,
                'priority': req.priority.value,
                'type': req.type.value,
                'time': req.due_date.time().isoformat(),
                'is_overdue': req.is_overdue,  # Use computed property
                'computed_status': req.computed_status.value,
                'client_id': req.client_id,
                'client_name': client_name,
                'days_until_due': (req.due_date.date() - datetime.now(timezone.utc).date()).days,
                'follow_up_count': req.follow_up_count or 0,
                'is_follow_up': req.is_follow_up or False,
                'due_date': req.due_date.isoformat(),
                'created_at': req.created_at.isoformat()
            })
        
        return {
            'calendar': calendar_data,
            'total_requests': len(requests)
        }

