"""
Validation API Endpoints for 10× Uplift Measurement
===================================================

FastAPI endpoints for running validation, monitoring progress, and exporting reports.
Integrates with the KPI validation framework and real-time dashboard.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

import uvicorn
from fastapi import APIRouter, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

# Import our validation framework
import sys
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.newsletter.validation.kpi_validator import create_kpi_validator, ValidationResult, KPIMetric

logger = logging.getLogger(__name__)

# API Models
class ValidationRequest(BaseModel):
    """Request model for validation"""
    validation_type: str = "full"  # "full" or "quick"
    include_trends: bool = True
    export_results: bool = False

class ValidationStatus(BaseModel):
    """Current validation status"""
    is_running: bool
    last_validation: Optional[datetime]
    last_result_summary: Optional[Dict[str, Any]]
    queue_length: int

class QuickValidationResult(BaseModel):
    """Quick validation result model"""
    overall_status: str
    metrics_tested: int
    metrics_passing: int
    average_improvement: str
    confidence_level: float
    metrics: List[Dict[str, Any]]
    timestamp: datetime

# Global validation state
validation_state = {
    "is_running": False,
    "current_validator": None,
    "last_result": None,
    "last_validation_time": None,
    "websocket_connections": set()
}

# Create router
validation_router = APIRouter(prefix="/api/newsletter/validation", tags=["validation"])

@validation_router.post("/run-full")
async def run_full_validation(
    request: ValidationRequest,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    """Run comprehensive 10× uplift validation"""
    
    if validation_state["is_running"]:
        raise HTTPException(
            status_code=409, 
            detail="Validation already in progress"
        )
    
    # Start validation in background
    background_tasks.add_task(
        _execute_full_validation,
        request.include_trends,
        request.export_results
    )
    
    return JSONResponse({
        "message": "Full validation started",
        "status": "running",
        "estimated_duration": "2-3 minutes"
    })

@validation_router.post("/run-quick")
async def run_quick_validation() -> QuickValidationResult:
    """Run quick validation check (subset of metrics)"""
    
    try:
        logger.info("Starting quick validation...")
        
        # Create validator instance
        validator = await create_kpi_validator()
        
        try:
            # Run subset of critical metrics
            engagement_metric = await validator.measure_user_engagement()
            ctr_metric = await validator.measure_click_through_rate()
            response_time_metric = await validator.measure_response_time()
            
            quick_metrics = [engagement_metric, ctr_metric, response_time_metric]
            
            # Calculate summary
            metrics_passing = sum(1 for m in quick_metrics if m.target_achieved)
            avg_improvement = sum(m.improvement_factor for m in quick_metrics) / len(quick_metrics)
            overall_status = "PASS" if metrics_passing >= 2 else "NEEDS_WORK"
            
            # Format results
            metrics_data = [
                {
                    "name": m.name,
                    "improvement": f"{m.improvement_factor:.2f}×",
                    "status": "PASS" if m.target_achieved else "FAIL",
                    "confidence": f"{m.confidence_level*100:.1f}%"
                }
                for m in quick_metrics
            ]
            
            result = QuickValidationResult(
                overall_status=overall_status,
                metrics_tested=len(quick_metrics),
                metrics_passing=metrics_passing,
                average_improvement=f"{avg_improvement:.2f}×",
                confidence_level=sum(m.confidence_level for m in quick_metrics) / len(quick_metrics),
                metrics=metrics_data,
                timestamp=datetime.now()
            )
            
            # Store for status endpoint
            validation_state["last_result"] = result.dict()
            validation_state["last_validation_time"] = datetime.now()
            
            # Notify WebSocket connections
            await _notify_websocket_connections({
                "type": "quick_validation_complete",
                "result": result.dict()
            })
            
            logger.info(f"Quick validation completed: {overall_status}")
            return result
            
        finally:
            await validator.cleanup()
            
    except Exception as e:
        logger.error(f"Quick validation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Quick validation failed: {str(e)}"
        )

@validation_router.get("/status")
async def get_validation_status() -> ValidationStatus:
    """Get current validation status"""
    
    return ValidationStatus(
        is_running=validation_state["is_running"],
        last_validation=validation_state["last_validation_time"],
        last_result_summary=validation_state["last_result"],
        queue_length=0  # Could implement a proper queue system
    )

@validation_router.get("/export-report")
async def export_validation_report() -> FileResponse:
    """Export the latest validation report"""
    
    if not validation_state["last_result"]:
        raise HTTPException(
            status_code=404,
            detail="No validation results available to export"
        )
    
    try:
        # Create reports directory if it doesn't exist
        reports_dir = Path("reports/validation")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate report filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = reports_dir / f"validation_report_{timestamp}.json"
        
        # Prepare comprehensive report data
        report_data = {
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "validation_timestamp": validation_state["last_validation_time"].isoformat() if validation_state["last_validation_time"] else None,
                "report_type": "10x_uplift_validation",
                "version": "1.0.0"
            },
            "validation_results": validation_state["last_result"],
            "system_info": {
                "platform": "GoodBooks Recommender Newsletter Platform",
                "validation_framework": "KPI Validator v1.0.0"
            }
        }
        
        # Write report to file
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        logger.info(f"Validation report exported: {report_file}")
        
        return FileResponse(
            path=str(report_file),
            filename=f"validation-report-{timestamp}.json",
            media_type="application/json"
        )
        
    except Exception as e:
        logger.error(f"Failed to export report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export report: {str(e)}"
        )

@validation_router.get("/metrics-history")
async def get_metrics_history(days: int = 7) -> Dict[str, Any]:
    """Get historical metrics data for trending analysis"""
    
    try:
        # In a production system, this would query a database
        # For now, return simulated historical data
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Generate sample historical data
        history_data = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "metrics_trend": [
                {
                    "date": (start_date + timedelta(days=i)).isoformat(),
                    "overall_improvement": 3.2 + (i * 0.8),  # Simulated improvement over time
                    "metrics_passing": min(10, 3 + i),  # Gradual improvement
                    "user_engagement": 0.15 * (1 + i * 0.3),  # Growing engagement
                    "click_through_rate": 0.08 * (1 + i * 0.4),  # Improving CTR
                    "conversion_rate": 0.03 * (1 + i * 0.5)  # Better conversions
                }
                for i in range(days)
            ],
            "insights": [
                "Steady improvement in engagement metrics over the period",
                "Click-through rates showing strong upward trend",
                "Conversion optimization yielding measurable results",
                "Overall 10× uplift target progress: accelerating"
            ]
        }
        
        return history_data
        
    except Exception as e:
        logger.error(f"Failed to get metrics history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve metrics history: {str(e)}"
        )

@validation_router.websocket("/ws/uplift-metrics")
async def websocket_uplift_metrics(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics updates"""
    
    await websocket.accept()
    validation_state["websocket_connections"].add(websocket)
    
    try:
        # Send initial status
        await websocket.send_json({
            "type": "connection_established",
            "message": "Connected to 10× uplift metrics stream",
            "timestamp": datetime.now().isoformat()
        })
        
        # Send last validation result if available
        if validation_state["last_result"]:
            await websocket.send_json({
                "type": "initial_data",
                "result": validation_state["last_result"],
                "timestamp": validation_state["last_validation_time"].isoformat() if validation_state["last_validation_time"] else None
            })
        
        # Keep connection alive and listen for client messages
        while True:
            try:
                # Wait for client message or timeout
                message = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
                
                # Handle client requests
                if message.get("type") == "request_status":
                    await websocket.send_json({
                        "type": "status_update",
                        "is_running": validation_state["is_running"],
                        "last_validation": validation_state["last_validation_time"].isoformat() if validation_state["last_validation_time"] else None
                    })
                    
            except asyncio.TimeoutError:
                # Send periodic heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        validation_state["websocket_connections"].discard(websocket)

async def _execute_full_validation(include_trends: bool = True, export_results: bool = False):
    """Execute full validation in background"""
    
    validation_state["is_running"] = True
    validator = None
    
    try:
        logger.info("Starting full 10× uplift validation...")
        
        # Notify WebSocket connections
        await _notify_websocket_connections({
            "type": "validation_started",
            "message": "Full validation in progress...",
            "timestamp": datetime.now().isoformat()
        })
        
        # Create and initialize validator
        validator = await create_kpi_validator()
        
        # Run comprehensive validation
        result = await validator.run_comprehensive_validation()
        
        # Generate comprehensive report
        report = await validator.generate_validation_report()
        
        # Store results
        validation_state["last_result"] = {
            "overall_uplift_achieved": result.overall_uplift_achieved,
            "average_improvement_factor": result.average_improvement_factor,
            "metrics_passing": result.metrics_passing,
            "total_metrics": result.total_metrics,
            "confidence_score": result.confidence_score,
            "metrics": [
                {
                    "name": m.name,
                    "current_value": m.current_value,
                    "baseline_value": m.baseline_value,
                    "target_value": m.target_value,
                    "improvement_factor": m.improvement_factor,
                    "target_achieved": m.target_achieved,
                    "confidence_level": m.confidence_level,
                    "unit": m.unit
                }
                for m in result.metrics
            ],
            "recommendations": result.recommendations,
            "validation_timestamp": result.validation_timestamp.isoformat()
        }
        
        validation_state["last_validation_time"] = datetime.now()
        
        # Export results if requested
        if export_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = f"reports/validation/validation_data_{timestamp}.json"
            await validator.export_validation_data(export_path)
            logger.info(f"Validation data exported to {export_path}")
        
        # Notify WebSocket connections of completion
        await _notify_websocket_connections({
            "type": "validation_complete",
            "result": validation_state["last_result"],
            "timestamp": datetime.now().isoformat()
        })
        
        success_emoji = "🎉" if result.overall_uplift_achieved else "📈"
        logger.info(f"{success_emoji} Full validation completed: {result.metrics_passing}/{result.total_metrics} metrics passing")
        
    except Exception as e:
        logger.error(f"Full validation failed: {e}")
        
        # Notify WebSocket connections of error
        await _notify_websocket_connections({
            "type": "validation_error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
        
    finally:
        validation_state["is_running"] = False
        if validator:
            await validator.cleanup()

async def _notify_websocket_connections(message: Dict[str, Any]):
    """Notify all WebSocket connections of an update"""
    
    if not validation_state["websocket_connections"]:
        return
    
    # Send to all connected clients
    disconnected = set()
    for websocket in validation_state["websocket_connections"]:
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send WebSocket message: {e}")
            disconnected.add(websocket)
    
    # Remove disconnected clients
    validation_state["websocket_connections"] -= disconnected

# Health check endpoint for the validation system
@validation_router.get("/health")
async def validation_health_check():
    """Health check for validation system"""
    
    try:
        # Basic health check - create validator instance
        validator = await create_kpi_validator()
        await validator.cleanup()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "validation_framework": "operational",
            "last_validation": validation_state["last_validation_time"].isoformat() if validation_state["last_validation_time"] else None
        }
        
    except Exception as e:
        logger.error(f"Validation health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Validation system unhealthy: {str(e)}"
        )

# Cleanup function for graceful shutdown
async def cleanup_validation_system():
    """Cleanup validation system resources"""
    
    try:
        # Close all WebSocket connections
        for websocket in validation_state["websocket_connections"]:
            try:
                await websocket.close()
            except:
                pass
        
        validation_state["websocket_connections"].clear()
        
        # Cleanup current validator if running
        if validation_state["current_validator"]:
            await validation_state["current_validator"].cleanup()
        
        logger.info("Validation system cleanup completed")
        
    except Exception as e:
        logger.error(f"Validation cleanup error: {e}")

# Register cleanup handler (would be called during app shutdown)
def register_cleanup_handler(app):
    """Register cleanup handler with FastAPI app"""
    
    @app.on_event("shutdown")
    async def shutdown_event():
        await cleanup_validation_system()
