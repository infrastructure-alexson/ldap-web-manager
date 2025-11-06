#!/usr/bin/env python3
"""
Audit Log Viewing API endpoints

Provides read-only access to audit logs for compliance and troubleshooting.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from typing import Optional
from datetime import datetime, timedelta

from app.models.audit import (
    AuditLogResponse, AuditLogListResponse, AuditStatistics,
    AuditLogFilter, AuditExportRequest, AuditActionEnum
)
from app.db.base import get_session
from app.db.models import AuditLog, AuditAction
from app.auth.jwt import get_current_user, require_admin
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user_id: Optional[str] = None,
    action: Optional[AuditActionEnum] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    List audit logs with filtering and pagination
    
    Args:
        page: Page number (1-indexed)
        page_size: Items per page (max 200)
        user_id: Filter by user ID
        action: Filter by action type (CREATE, UPDATE, DELETE, READ, AUTHENTICATION)
        resource_type: Filter by resource type (User, Group, DNS, DHCP, IPAM, ServiceAccount)
        resource_id: Filter by resource ID
        status: Filter by status (success, failure, error)
        start_date: Filter logs after this date
        end_date: Filter logs before this date
        search: Search in details and error messages
        session: Database session
        current_user: Authenticated user
        
    Returns:
        Paginated list of audit logs
    """
    try:
        # Build filter conditions
        conditions = []
        
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        
        if action:
            conditions.append(AuditLog.action == action)
        
        if resource_type:
            conditions.append(AuditLog.resource_type == resource_type)
        
        if resource_id:
            conditions.append(AuditLog.resource_id == resource_id)
        
        if status:
            conditions.append(AuditLog.status == status)
        
        if start_date:
            conditions.append(AuditLog.timestamp >= start_date)
        
        if end_date:
            conditions.append(AuditLog.timestamp <= end_date)
        
        if search:
            # Search in details JSON and error messages
            search_filter = or_(
                AuditLog.details.ilike(f"%{search}%"),
                AuditLog.error_message.ilike(f"%{search}%")
            )
            conditions.append(search_filter)
        
        # Build query
        query = select(AuditLog)
        if conditions:
            query = query.where(and_(*conditions))
        
        # Count total
        count_query = select(func.count()).select_from(AuditLog)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results
        query = query.order_by(desc(AuditLog.timestamp))
        query = query.limit(page_size).offset((page - 1) * page_size)
        
        result = await session.execute(query)
        logs = result.scalars().all()
        
        # Convert to response models
        items = [
            AuditLogResponse(
                id=str(log.id),
                timestamp=log.timestamp,
                user_id=log.user_id,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                status=log.status,
                details=log.details,
                before_state=log.before_state,
                after_state=log.after_state,
                error_message=log.error_message,
                ip_address=getattr(log, 'ip_address', None),
                user_agent=getattr(log, 'user_agent', None)
            )
            for log in logs
        ]
        
        return AuditLogListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=items
        )
        
    except Exception as e:
        logger.error(f"Error listing audit logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list audit logs: {str(e)}"
        )


@router.get("/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific audit log entry
    
    Args:
        log_id: Audit log ID
        session: Database session
        current_user: Authenticated user
        
    Returns:
        Audit log entry details
    """
    try:
        result = await session.execute(
            select(AuditLog).where(AuditLog.id == log_id)
        )
        log = result.scalar_one_or_none()
        
        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audit log not found: {log_id}"
            )
        
        return AuditLogResponse(
            id=str(log.id),
            timestamp=log.timestamp,
            user_id=log.user_id,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            status=log.status,
            details=log.details,
            before_state=log.before_state,
            after_state=log.after_state,
            error_message=log.error_message,
            ip_address=getattr(log, 'ip_address', None),
            user_agent=getattr(log, 'user_agent', None)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit log: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit log: {str(e)}"
        )


@router.get("/stats/overview", response_model=AuditStatistics)
async def get_audit_statistics(
    days: int = Query(7, ge=1, le=365, description="Number of days to include"),
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    """
    Get audit log statistics for the past N days
    
    Args:
        days: Number of days to include in statistics
        session: Database session
        current_user: Authenticated admin user
        
    Returns:
        Audit statistics
    """
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get total count
        total_result = await session.execute(
            select(func.count()).select_from(AuditLog).where(AuditLog.timestamp >= start_date)
        )
        total_logs = total_result.scalar() or 0
        
        # Get counts by action
        actions_query = await session.execute(
            select(AuditLog.action, func.count(AuditLog.id).label('count'))
            .where(AuditLog.timestamp >= start_date)
            .group_by(AuditLog.action)
        )
        actions_breakdown = {row[0]: row[1] for row in actions_query.all()}
        
        # Get counts by resource type
        resources_query = await session.execute(
            select(AuditLog.resource_type, func.count(AuditLog.id).label('count'))
            .where(AuditLog.timestamp >= start_date)
            .group_by(AuditLog.resource_type)
        )
        resource_types_breakdown = {row[0]: row[1] for row in resources_query.all()}
        
        # Get unique users count
        users_result = await session.execute(
            select(func.count(func.distinct(AuditLog.user_id)))
            .select_from(AuditLog)
            .where(AuditLog.timestamp >= start_date)
        )
        users_count = users_result.scalar() or 0
        
        # Get success/failure counts
        success_result = await session.execute(
            select(func.count(AuditLog.id))
            .select_from(AuditLog)
            .where(
                and_(
                    AuditLog.timestamp >= start_date,
                    AuditLog.status == 'success'
                )
            )
        )
        success_count = success_result.scalar() or 0
        
        failure_result = await session.execute(
            select(func.count(AuditLog.id))
            .select_from(AuditLog)
            .where(
                and_(
                    AuditLog.timestamp >= start_date,
                    AuditLog.status == 'failure'
                )
            )
        )
        failure_count = failure_result.scalar() or 0
        
        error_result = await session.execute(
            select(func.count(AuditLog.id))
            .select_from(AuditLog)
            .where(
                and_(
                    AuditLog.timestamp >= start_date,
                    AuditLog.status == 'error'
                )
            )
        )
        error_count = error_result.scalar() or 0
        
        success_rate = (success_count / total_logs * 100) if total_logs > 0 else 0
        
        end_date = datetime.utcnow()
        date_range = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        
        return AuditStatistics(
            total_logs=total_logs,
            date_range=date_range,
            actions_breakdown=actions_breakdown,
            resource_types_breakdown=resource_types_breakdown,
            users_count=users_count,
            success_rate=round(success_rate, 2),
            failure_count=failure_count,
            error_count=error_count
        )
        
    except Exception as e:
        logger.error(f"Error getting audit statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit statistics: {str(e)}"
        )


@router.post("/export")
async def export_audit_logs(
    export_request: AuditExportRequest,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    """
    Export audit logs in the specified format
    
    Args:
        export_request: Export format and filters
        session: Database session
        current_user: Authenticated admin user
        
    Returns:
        CSV, JSON, or Excel file
    """
    try:
        # Build query with filters
        conditions = []
        
        if export_request.filters:
            if export_request.filters.user_id:
                conditions.append(AuditLog.user_id == export_request.filters.user_id)
            
            if export_request.filters.action:
                conditions.append(AuditLog.action == export_request.filters.action)
            
            if export_request.filters.resource_type:
                conditions.append(AuditLog.resource_type == export_request.filters.resource_type)
            
            if export_request.filters.start_date:
                conditions.append(AuditLog.timestamp >= export_request.filters.start_date)
            
            if export_request.filters.end_date:
                conditions.append(AuditLog.timestamp <= export_request.filters.end_date)
        
        query = select(AuditLog)
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(desc(AuditLog.timestamp))
        
        result = await session.execute(query)
        logs = result.scalars().all()
        
        # Format based on requested format
        if export_request.format == 'json':
            import json
            data = [
                {
                    'id': str(log.id),
                    'timestamp': log.timestamp.isoformat(),
                    'user_id': log.user_id,
                    'action': log.action,
                    'resource_type': log.resource_type,
                    'resource_id': log.resource_id,
                    'status': log.status,
                    'details': log.details if export_request.include_details else None,
                    'error_message': log.error_message
                }
                for log in logs
            ]
            
            from fastapi.responses import StreamingResponse
            import io
            
            output = io.StringIO()
            json.dump(data, output, indent=2, default=str)
            output.seek(0)
            
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="application/json",
                headers={"Content-Disposition": "attachment; filename=audit_logs.json"}
            )
        
        elif export_request.format == 'csv':
            import csv
            from fastapi.responses import StreamingResponse
            import io
            
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=['id', 'timestamp', 'user_id', 'action', 'resource_type', 
                           'resource_id', 'status', 'error_message']
            )
            writer.writeheader()
            
            for log in logs:
                writer.writerow({
                    'id': str(log.id),
                    'timestamp': log.timestamp.isoformat(),
                    'user_id': log.user_id,
                    'action': log.action,
                    'resource_type': log.resource_type,
                    'resource_id': log.resource_id or '',
                    'status': log.status,
                    'error_message': log.error_message or ''
                })
            
            output.seek(0)
            
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=audit_logs.csv"}
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported export format: {export_request.format}. Supported: json, csv"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting audit logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export audit logs: {str(e)}"
        )

