"""
Alert Webhook Service for Testing and Monitoring
Receives alert notifications from Alertmanager for testing and logging purposes.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn
import aiofiles

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="GoodBooks Alert Webhook", version="1.0.0")

# Store alerts in memory for testing (in production, use proper storage)
alert_history: List[Dict[str, Any]] = []
webhook_stats = {
    "total_alerts": 0,
    "firing_alerts": 0,
    "resolved_alerts": 0,
    "last_alert": None
}

async def save_alert_to_file(alert_data: Dict[str, Any]):
    """Save alert to log file for persistence."""
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "alert_data": alert_data
    }
    
    os.makedirs("logs", exist_ok=True)
    async with aiofiles.open("logs/alerts.log", "a") as f:
        await f.write(json.dumps(log_entry) + "\n")

def process_alert_notification(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process incoming alert notification and extract relevant information."""
    status = alert_data.get("status", "unknown")
    alerts = alert_data.get("alerts", [])
    
    processed_alerts = []
    for alert in alerts:
        processed_alert = {
            "status": status,
            "alertname": alert.get("labels", {}).get("alertname", "unknown"),
            "service": alert.get("labels", {}).get("service", "unknown"),
            "severity": alert.get("labels", {}).get("severity", "unknown"),
            "instance": alert.get("labels", {}).get("instance", "unknown"),
            "description": alert.get("annotations", {}).get("description", ""),
            "summary": alert.get("annotations", {}).get("summary", ""),
            "starts_at": alert.get("startsAt", ""),
            "ends_at": alert.get("endsAt", ""),
            "labels": alert.get("labels", {}),
            "annotations": alert.get("annotations", {})
        }
        processed_alerts.append(processed_alert)
    
    return {
        "status": status,
        "receiver": alert_data.get("receiver", "unknown"),
        "group_key": alert_data.get("groupKey", ""),
        "group_labels": alert_data.get("groupLabels", {}),
        "common_labels": alert_data.get("commonLabels", {}),
        "common_annotations": alert_data.get("commonAnnotations", {}),
        "external_url": alert_data.get("externalURL", ""),
        "alerts": processed_alerts,
        "received_at": datetime.now().isoformat()
    }

@app.post("/alerts")
async def receive_alerts(request: Request, background_tasks: BackgroundTasks):
    """Receive alert notifications from Alertmanager."""
    try:
        alert_data = await request.json()
        logger.info(f"Received alert notification: {alert_data}")
        
        # Process alert data
        processed_alert = process_alert_notification(alert_data)
        
        # Update statistics
        webhook_stats["total_alerts"] += 1
        webhook_stats["last_alert"] = datetime.now().isoformat()
        
        status = processed_alert["status"]
        if status == "firing":
            webhook_stats["firing_alerts"] += 1
        elif status == "resolved":
            webhook_stats["resolved_alerts"] += 1
        
        # Store in memory (limit to last 100 alerts)
        alert_history.append(processed_alert)
        if len(alert_history) > 100:
            alert_history.pop(0)
        
        # Save to file in background
        background_tasks.add_task(save_alert_to_file, processed_alert)
        
        # Log critical alerts immediately
        for alert in processed_alert["alerts"]:
            if alert["severity"] == "critical":
                logger.critical(
                    f"CRITICAL ALERT: {alert['alertname']} - {alert['description']} "
                    f"(Service: {alert['service']}, Instance: {alert['instance']})"
                )
            elif alert["severity"] == "high":
                logger.error(
                    f"HIGH ALERT: {alert['alertname']} - {alert['description']} "
                    f"(Service: {alert['service']}, Instance: {alert['instance']})"
                )
            elif alert["severity"] == "warning":
                logger.warning(
                    f"WARNING: {alert['alertname']} - {alert['description']} "
                    f"(Service: {alert['service']}, Instance: {alert['instance']})"
                )
        
        return JSONResponse(
            content={"status": "received", "alert_count": len(processed_alert["alerts"])},
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Error processing alert: {str(e)}")
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=500
        )

@app.post("/test-alerts")
async def receive_test_alerts(request: Request):
    """Receive test alert notifications."""
    try:
        alert_data = await request.json()
        logger.info(f"Received TEST alert: {alert_data}")
        
        # Log test alert details
        for alert in alert_data.get("alerts", []):
            logger.info(
                f"TEST ALERT: {alert.get('labels', {}).get('alertname', 'unknown')} - "
                f"{alert.get('annotations', {}).get('description', 'No description')}"
            )
        
        return JSONResponse(
            content={"status": "test_received", "message": "Test alert received successfully"},
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Error processing test alert: {str(e)}")
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=500
        )

@app.get("/alerts/history")
async def get_alert_history():
    """Get alert history for monitoring and debugging."""
    return JSONResponse(content={
        "stats": webhook_stats,
        "recent_alerts": alert_history[-10:],  # Last 10 alerts
        "total_stored": len(alert_history)
    })

@app.get("/alerts/stats")
async def get_alert_stats():
    """Get alert statistics."""
    return JSONResponse(content=webhook_stats)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(content={
        "status": "healthy",
        "service": "alert-webhook",
        "uptime": webhook_stats.get("last_alert", "No alerts received yet")
    })

@app.post("/simulate-alert")
async def simulate_alert(alert_type: str = "test"):
    """Simulate an alert for testing purposes."""
    test_alert = {
        "receiver": "test-alerts",
        "status": "firing",
        "alerts": [{
            "status": "firing",
            "labels": {
                "alertname": "TestAlert",
                "service": "goodbooks-api",
                "severity": "warning",
                "instance": "localhost:8000"
            },
            "annotations": {
                "description": f"This is a simulated {alert_type} alert for testing notification channels",
                "summary": f"Simulated {alert_type} alert"
            },
            "startsAt": datetime.now().isoformat(),
            "endsAt": "",
            "generatorURL": "http://prometheus:9090/graph"
        }],
        "groupLabels": {
            "alertname": "TestAlert"
        },
        "commonLabels": {
            "service": "goodbooks-api"
        },
        "commonAnnotations": {},
        "externalURL": "http://alertmanager:9093",
        "version": "4",
        "groupKey": "test-group"
    }
    
    # Process the simulated alert
    processed_alert = process_alert_notification(test_alert)
    alert_history.append(processed_alert)
    
    logger.info(f"Simulated {alert_type} alert created")
    
    return JSONResponse(content={
        "status": "simulated",
        "alert_type": alert_type,
        "alert": test_alert
    })

if __name__ == "__main__":
    uvicorn.run(
        "alert_webhook:app",
        host="0.0.0.0",
        port=5001,
        log_level="info",
        reload=False
    )
