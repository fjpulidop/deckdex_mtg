"""
WebSocket handler for real-time progress updates
"""
import asyncio
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from loguru import logger
from datetime import datetime

router = APIRouter()

# Store active WebSocket connections per job_id
_connections: Dict[str, Set[WebSocket]] = {}

class ConnectionManager:
    """
    Manages WebSocket connections for progress updates
    
    Supports multiple clients connecting to the same job_id
    """
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, job_id: str):
        """
        Accept a new WebSocket connection for a job
        
        Args:
            websocket: WebSocket connection
            job_id: Job ID to subscribe to
        """
        await websocket.accept()
        
        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()
        
        self.active_connections[job_id].add(websocket)
        logger.info(f"WebSocket connected: job_id={job_id}, total_connections={len(self.active_connections[job_id])}")
    
    def disconnect(self, websocket: WebSocket, job_id: str):
        """
        Remove a WebSocket connection
        
        Args:
            websocket: WebSocket connection
            job_id: Job ID
        """
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
            
            logger.info(f"WebSocket disconnected: job_id={job_id}")
    
    async def broadcast(self, job_id: str, message: dict):
        """
        Broadcast message to all connections for a job
        
        Args:
            job_id: Job ID
            message: Message dict to send (will be JSON serialized)
        """
        if job_id not in self.active_connections:
            logger.debug(f"No active connections for job_id={job_id}")
            return
        
        # Add timestamp to all messages
        message['timestamp'] = datetime.now().isoformat()
        
        # Broadcast to all connected clients
        disconnected = set()
        for connection in self.active_connections[job_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection, job_id)
    
    async def send_progress(self, job_id: str, current: int, total: int, percentage: float, **kwargs):
        """
        Send progress update event
        
        Args:
            job_id: Job ID
            current: Current progress count
            total: Total items
            percentage: Completion percentage
            **kwargs: Additional data to include
        """
        await self.broadcast(job_id, {
            'type': 'progress',
            'current': current,
            'total': total,
            'percentage': round(percentage, 2),
            **kwargs
        })
    
    async def send_error(self, job_id: str, card_name: str, error_type: str, message: str):
        """
        Send error event
        
        Args:
            job_id: Job ID
            card_name: Name of card that failed
            error_type: Type of error (e.g., 'not_found', 'api_error')
            message: Error message
        """
        await self.broadcast(job_id, {
            'type': 'error',
            'card_name': card_name,
            'error_type': error_type,
            'message': message
        })
    
    async def send_complete(self, job_id: str, status: str, summary: dict):
        """
        Send completion event
        
        Args:
            job_id: Job ID
            status: Final status ('success', 'error', 'cancelled')
            summary: Summary data
        """
        await self.broadcast(job_id, {
            'type': 'complete',
            'status': status,
            'summary': summary
        })
    
    def get_connection_count(self, job_id: str) -> int:
        """
        Get number of active connections for a job
        
        Args:
            job_id: Job ID
        
        Returns:
            Number of active connections
        """
        return len(self.active_connections.get(job_id, set()))

# Global connection manager instance
manager = ConnectionManager()

@router.websocket("/ws/progress/{job_id}")
async def websocket_progress(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time progress updates.

    Authentication: JWT is read from the ``access_token`` HTTP-only cookie
    (sent automatically by the browser).

    Clients receive progress events:
    - progress: { type, current, total, percentage, timestamp }
    - error: { type, card_name, error_type, message, timestamp }
    - complete: { type, status, summary, timestamp }
    """
    # --- Authenticate WebSocket via cookie only ---
    from ..dependencies import decode_jwt_token
    jwt_token = websocket.cookies.get("access_token")
    if not jwt_token:
        logger.warning(f"WebSocket rejected: no auth token for job_id={job_id}")
        await websocket.close(code=4001, reason="Authentication required")
        return
    try:
        decode_jwt_token(jwt_token)
    except Exception:
        logger.warning(f"WebSocket rejected: invalid token for job_id={job_id}")
        await websocket.close(code=4001, reason="Invalid or expired token")
        return

    # Validate job exists (check active jobs)
    from ..routes.process import _active_jobs, _job_results

    if job_id not in _active_jobs and job_id not in _job_results:
        logger.warning(f"WebSocket connection rejected: job_id={job_id} not found")
        await websocket.close(code=4004, reason="Job not found")
        return

    # Accept connection
    await manager.connect(websocket, job_id)
    
    try:
        # Send initial acknowledgment with current progress snapshot
        initial_progress = {'current': 0, 'total': 0, 'percentage': 0.0}
        job_status = 'unknown'
        
        if job_id in _active_jobs:
            service = _active_jobs[job_id]
            initial_progress = service.progress_data.copy()
            job_status = service.status
        elif job_id in _job_results:
            job_status = _job_results[job_id].get('status', 'complete')
        
        await websocket.send_json({
            'type': 'connected',
            'job_id': job_id,
            'job_status': job_status,
            'timestamp': datetime.now().isoformat()
        })
        
        # Immediately send current progress so reconnecting clients catch up
        if job_status == 'running' and (initial_progress.get('total', 0) > 0):
            await websocket.send_json({
                'type': 'progress',
                'current': initial_progress.get('current', 0),
                'total': initial_progress.get('total', 0),
                'percentage': initial_progress.get('percentage', 0.0),
                'timestamp': datetime.now().isoformat()
            })
        elif job_status in ('complete', 'error'):
            # Job already finished - send complete event
            result = _job_results.get(job_id, {})
            await websocket.send_json({
                'type': 'complete',
                'status': job_status,
                'summary': result,
                'timestamp': datetime.now().isoformat()
            })
        
        # Keep connection alive and handle heartbeat
        while True:
            try:
                # Wait for messages from client (or timeout for heartbeat)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                
                # Handle ping/pong if client sends messages
                if data == 'ping':
                    await websocket.send_json({
                        'type': 'pong',
                        'timestamp': datetime.now().isoformat()
                    })
                
            except asyncio.TimeoutError:
                # Send heartbeat ping
                try:
                    await websocket.send_json({
                        'type': 'ping',
                        'timestamp': datetime.now().isoformat()
                    })
                except Exception as e:
                    logger.error(f"Failed to send heartbeat: {e}")
                    break
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: job_id={job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for job_id={job_id}: {e}")
    finally:
        manager.disconnect(websocket, job_id)
        logger.info(f"WebSocket connection closed: job_id={job_id}")

# Export manager for use in processor service
__all__ = ['manager', 'router']
