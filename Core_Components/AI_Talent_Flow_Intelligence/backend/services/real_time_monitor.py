"""
Real-time monitoring service for AI Talent Flow Intelligence.
Provides continuous tracking of talent movements, market impacts, and system health.
"""

import asyncio
import logging
import websockets
import json
from typing import Dict, List, Set, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import httpx

logger = logging.getLogger(__name__)


class MonitoringLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class MonitoringEvent:
    """Real-time monitoring event"""
    event_type: str
    level: MonitoringLevel
    message: str
    timestamp: datetime
    data: Dict[str, Any]
    source: str


class RealTimeMonitor:
    """Real-time monitoring and alerting system"""
    
    def __init__(self):
        self.active_monitors: Set[str] = set()
        self.event_buffer: List[MonitoringEvent] = []
        self.max_buffer_size = 1000
        self.websocket_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.monitoring_enabled = True
        
        # Monitoring thresholds
        self.thresholds = {
            "high_confidence_movement": 0.85,
            "critical_talent_impact": 0.8,
            "unusual_activity_spike": 5,  # movements per hour
            "api_response_time": 2.0,  # seconds
            "prediction_confidence_drop": 0.3
        }
        
        # Statistics tracking
        self.stats = {
            "total_movements_detected": 0,
            "signals_generated": 0,
            "predictions_made": 0,
            "avg_confidence": 0.0,
            "system_uptime": datetime.now(),
            "last_activity": datetime.now()
        }
    
    async def start_monitoring(self):
        """Start all monitoring processes"""
        logger.info("Starting real-time monitoring system")
        
        monitoring_tasks = [
            self.monitor_talent_movements(),
            self.monitor_api_health(),
            self.monitor_prediction_quality(),
            self.monitor_system_performance(),
            self.cleanup_old_events()
        ]
        
        await asyncio.gather(*monitoring_tasks)
    
    async def monitor_talent_movements(self):
        """Monitor for new talent movements in real-time"""
        logger.info("Starting talent movement monitoring")
        
        while self.monitoring_enabled:
            try:
                # Check for new movements (in production, this would connect to real data sources)
                await self._check_github_activity()
                await self._check_linkedin_updates()
                await self._check_news_sources()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in talent movement monitoring: {e}")
                await self._emit_event(MonitoringEvent(
                    event_type="monitoring_error",
                    level=MonitoringLevel.WARNING,
                    message=f"Talent movement monitoring error: {str(e)}",
                    timestamp=datetime.now(),
                    data={"error": str(e)},
                    source="movement_monitor"
                ))
                await asyncio.sleep(60)  # Back off on error
    
    async def _check_github_activity(self):
        """Check for GitHub activity patterns indicating potential movements"""
        # Simulate GitHub activity monitoring
        activity_detected = False  # Would be real API call
        
        if activity_detected:
            await self._emit_event(MonitoringEvent(
                event_type="github_activity_spike",
                level=MonitoringLevel.INFO,
                message="Unusual GitHub activity pattern detected",
                timestamp=datetime.now(),
                data={
                    "source": "github",
                    "activity_type": "commit_pattern_change",
                    "confidence": 0.7
                },
                source="github_monitor"
            ))
    
    async def _check_linkedin_updates(self):
        """Monitor LinkedIn for job change announcements"""
        # Simulate LinkedIn monitoring
        updates_found = False  # Would be real monitoring
        
        if updates_found:
            await self._emit_event(MonitoringEvent(
                event_type="linkedin_job_announcement",
                level=MonitoringLevel.INFO,
                message="New job announcement detected",
                timestamp=datetime.now(),
                data={
                    "source": "linkedin",
                    "announcement_type": "job_change",
                    "confidence": 0.85
                },
                source="linkedin_monitor"
            ))
    
    async def _check_news_sources(self):
        """Monitor news sources for talent movement announcements"""
        # Simulate news monitoring
        news_detected = False  # Would be real news API
        
        if news_detected:
            await self._emit_event(MonitoringEvent(
                event_type="news_talent_announcement",
                level=MonitoringLevel.WARNING,
                message="Talent movement announced in tech news",
                timestamp=datetime.now(),
                data={
                    "source": "tech_news",
                    "article_confidence": 0.9,
                    "impact_level": "high"
                },
                source="news_monitor"
            ))
    
    async def monitor_api_health(self):
        """Monitor API health and performance"""
        logger.info("Starting API health monitoring")
        
        while self.monitoring_enabled:
            try:
                # Health check main API
                start_time = datetime.now()
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:8004/health", timeout=5.0)
                    response_time = (datetime.now() - start_time).total_seconds()
                    
                    if response.status_code == 200:
                        if response_time > self.thresholds["api_response_time"]:
                            await self._emit_event(MonitoringEvent(
                                event_type="slow_api_response",
                                level=MonitoringLevel.WARNING,
                                message=f"API response time: {response_time:.2f}s (threshold: {self.thresholds['api_response_time']}s)",
                                timestamp=datetime.now(),
                                data={"response_time": response_time, "endpoint": "/health"},
                                source="api_monitor"
                            ))
                    else:
                        await self._emit_event(MonitoringEvent(
                            event_type="api_health_failure",
                            level=MonitoringLevel.CRITICAL,
                            message=f"API health check failed: {response.status_code}",
                            timestamp=datetime.now(),
                            data={"status_code": response.status_code},
                            source="api_monitor"
                        ))
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                await self._emit_event(MonitoringEvent(
                    event_type="api_connection_failure",
                    level=MonitoringLevel.CRITICAL,
                    message=f"Failed to connect to API: {str(e)}",
                    timestamp=datetime.now(),
                    data={"error": str(e)},
                    source="api_monitor"
                ))
                await asyncio.sleep(120)  # Back off on failure
    
    async def monitor_prediction_quality(self):
        """Monitor prediction quality and accuracy"""
        logger.info("Starting prediction quality monitoring")
        
        while self.monitoring_enabled:
            try:
                # Check recent predictions (would analyze actual prediction data)
                recent_predictions = await self._get_recent_predictions()
                
                if recent_predictions:
                    avg_confidence = sum(p.get("confidence", 0) for p in recent_predictions) / len(recent_predictions)
                    
                    if avg_confidence < self.thresholds["prediction_confidence_drop"]:
                        await self._emit_event(MonitoringEvent(
                            event_type="low_prediction_confidence",
                            level=MonitoringLevel.WARNING,
                            message=f"Average prediction confidence dropped to {avg_confidence:.2f}",
                            timestamp=datetime.now(),
                            data={
                                "avg_confidence": avg_confidence,
                                "prediction_count": len(recent_predictions),
                                "threshold": self.thresholds["prediction_confidence_drop"]
                            },
                            source="prediction_monitor"
                        ))
                    
                    self.stats["avg_confidence"] = avg_confidence
                    self.stats["predictions_made"] += len(recent_predictions)
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in prediction quality monitoring: {e}")
                await asyncio.sleep(300)
    
    async def _get_recent_predictions(self) -> List[Dict[str, Any]]:
        """Get recent predictions for quality analysis"""
        # Simulate getting recent predictions
        return [
            {"confidence": 0.85, "impact": 0.7},
            {"confidence": 0.72, "impact": 0.5},
            {"confidence": 0.91, "impact": 0.8}
        ]
    
    async def monitor_system_performance(self):
        """Monitor overall system performance"""
        logger.info("Starting system performance monitoring")
        
        while self.monitoring_enabled:
            try:
                # Update system stats
                self.stats["last_activity"] = datetime.now()
                uptime = datetime.now() - self.stats["system_uptime"]
                
                # Check for unusual activity patterns
                movements_last_hour = await self._count_recent_movements(hours=1)
                if movements_last_hour >= self.thresholds["unusual_activity_spike"]:
                    await self._emit_event(MonitoringEvent(
                        event_type="unusual_activity_spike",
                        level=MonitoringLevel.WARNING,
                        message=f"High activity: {movements_last_hour} movements in last hour",
                        timestamp=datetime.now(),
                        data={
                            "movements_count": movements_last_hour,
                            "threshold": self.thresholds["unusual_activity_spike"],
                            "time_window": "1 hour"
                        },
                        source="performance_monitor"
                    ))
                
                # Emit periodic health update
                await self._emit_event(MonitoringEvent(
                    event_type="system_health_update",
                    level=MonitoringLevel.INFO,
                    message=f"System running normally. Uptime: {uptime}",
                    timestamp=datetime.now(),
                    data={
                        "uptime_seconds": uptime.total_seconds(),
                        "stats": self.stats,
                        "active_monitors": list(self.active_monitors)
                    },
                    source="system_monitor"
                ))
                
                await asyncio.sleep(600)  # Every 10 minutes
                
            except Exception as e:
                logger.error(f"Error in system performance monitoring: {e}")
                await asyncio.sleep(600)
    
    async def _count_recent_movements(self, hours: int = 1) -> int:
        """Count recent talent movements"""
        # Simulate counting recent movements
        return 2  # Would query actual database
    
    async def _emit_event(self, event: MonitoringEvent):
        """Emit monitoring event to all connected clients"""
        self.event_buffer.append(event)
        
        # Keep buffer size manageable
        if len(self.event_buffer) > self.max_buffer_size:
            self.event_buffer = self.event_buffer[-self.max_buffer_size:]
        
        # Broadcast to WebSocket clients
        if self.websocket_clients:
            event_data = {
                "event_type": event.event_type,
                "level": event.level.value,
                "message": event.message,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data,
                "source": event.source
            }
            
            disconnected_clients = set()
            for client in self.websocket_clients:
                try:
                    await client.send(json.dumps(event_data))
                except websockets.exceptions.ConnectionClosed:
                    disconnected_clients.add(client)
                except Exception as e:
                    logger.warning(f"Failed to send event to client: {e}")
                    disconnected_clients.add(client)
            
            # Clean up disconnected clients
            self.websocket_clients -= disconnected_clients
        
        # Log critical events
        if event.level == MonitoringLevel.CRITICAL:
            logger.critical(f"CRITICAL: {event.message}")
        elif event.level == MonitoringLevel.WARNING:
            logger.warning(f"WARNING: {event.message}")
        else:
            logger.info(f"INFO: {event.message}")
    
    async def cleanup_old_events(self):
        """Clean up old events from buffer"""
        while self.monitoring_enabled:
            try:
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.event_buffer = [
                    event for event in self.event_buffer 
                    if event.timestamp > cutoff_time
                ]
                
                await asyncio.sleep(3600)  # Clean up every hour
                
            except Exception as e:
                logger.error(f"Error in event cleanup: {e}")
                await asyncio.sleep(3600)
    
    async def handle_websocket_client(self, websocket, path):
        """Handle WebSocket client connections"""
        self.websocket_clients.add(websocket)
        logger.info(f"New monitoring client connected: {websocket.remote_address}")
        
        try:
            # Send recent events to new client
            recent_events = self.event_buffer[-10:]  # Last 10 events
            for event in recent_events:
                event_data = {
                    "event_type": event.event_type,
                    "level": event.level.value,
                    "message": event.message,
                    "timestamp": event.timestamp.isoformat(),
                    "data": event.data,
                    "source": event.source
                }
                await websocket.send(json.dumps(event_data))
            
            # Keep connection alive
            async for message in websocket:
                # Handle client messages (e.g., subscription preferences)
                try:
                    data = json.loads(message)
                    if data.get("type") == "ping":
                        await websocket.send(json.dumps({"type": "pong"}))
                except json.JSONDecodeError:
                    logger.warning(f"Invalid message from client: {message}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Monitoring client disconnected: {websocket.remote_address}")
        finally:
            self.websocket_clients.discard(websocket)
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Get current monitoring statistics"""
        uptime = datetime.now() - self.stats["system_uptime"]
        
        return {
            **self.stats,
            "uptime_seconds": uptime.total_seconds(),
            "uptime_formatted": str(uptime),
            "active_clients": len(self.websocket_clients),
            "event_buffer_size": len(self.event_buffer),
            "monitoring_enabled": self.monitoring_enabled,
            "thresholds": self.thresholds
        }
    
    def get_recent_events(self, count: int = 50) -> List[Dict[str, Any]]:
        """Get recent monitoring events"""
        recent_events = self.event_buffer[-count:]
        return [
            {
                "event_type": event.event_type,
                "level": event.level.value,
                "message": event.message,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data,
                "source": event.source
            }
            for event in recent_events
        ]
    
    async def stop_monitoring(self):
        """Stop all monitoring processes"""
        logger.info("Stopping real-time monitoring system")
        self.monitoring_enabled = False
        
        # Close all WebSocket connections
        for client in self.websocket_clients:
            try:
                await client.close()
            except:
                pass
        self.websocket_clients.clear()


# Global monitor instance
real_time_monitor = RealTimeMonitor()


async def start_monitoring_server():
    """Start the real-time monitoring server"""
    # Start monitoring processes
    monitor_task = asyncio.create_task(real_time_monitor.start_monitoring())
    
    # Start WebSocket server
    websocket_server = await websockets.serve(
        real_time_monitor.handle_websocket_client,
        "localhost",
        8005,  # WebSocket port
        ping_interval=30,
        ping_timeout=10
    )
    
    logger.info("Real-time monitoring server started on ws://localhost:8005")
    
    # Keep servers running
    await asyncio.gather(
        monitor_task,
        websocket_server.wait_closed()
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_monitoring_server())