"""
Offline Synchronization Service for DMLogn8n Mobile
Handles conflict resolution, data synchronization, and offline queue management.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import hashlib
from collections import defaultdict
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enums
class ConflictResolutionStrategy(Enum):
    CLIENT_WINS = "client"
    SERVER_WINS = "server"
    MERGE = "merge"
    MANUAL = "manual"

class SyncStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"

class OperationType(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    MERGE = "merge"

@dataclass
class SyncOperation:
    """Represents a single sync operation"""
    id: str
    user_id: str
    resource_type: str
    resource_id: str
    operation: OperationType
    client_data: Dict[str, Any]
    server_data: Optional[Dict[str, Any]]
    client_timestamp: datetime
    server_timestamp: Optional[datetime]
    hash: str
    status: SyncStatus
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    conflict_resolution: Optional[ConflictResolutionStrategy] = None

@dataclass
class SyncSession:
    """Represents a sync session"""
    id: str
    user_id: str
    started_at: datetime
    completed_at: Optional[datetime]
    status: SyncStatus
    operations: List[SyncOperation]
    summary: Dict[str, int]

@dataclass
class Conflict:
    """Represents a sync conflict"""
    id: str
    session_id: str
    operation_id: str
    resource_type: str
    resource_id: str
    client_data: Dict[str, Any]
    server_data: Dict[str, Any]
    conflict_fields: List[str]
    detected_at: datetime
    resolution: Optional[ConflictResolutionStrategy] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

class OfflineSyncService:
    """Main offline synchronization service"""

    def __init__(self):
        self.pending_operations: Dict[str, List[SyncOperation]] = defaultdict(list)  # user_id -> operations
        self.active_sessions: Dict[str, SyncSession] = {}  # session_id -> session
        self.conflicts: Dict[str, List[Conflict]] = defaultdict(list)  # user_id -> conflicts
        self.sync_locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)  # user_id -> lock
        self.max_operations_per_session = 100
        self.sync_timeout = 300  # 5 minutes

    def add_operation(self, user_id: str, resource_type: str, resource_id: str,
                     operation: OperationType, data: Dict[str, Any]) -> str:
        """Add a new sync operation to the queue"""
        try:
            operation_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            data_hash = self._calculate_data_hash(data)

            sync_operation = SyncOperation(
                id=operation_id,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                operation=operation,
                client_data=data,
                server_data=None,
                client_timestamp=timestamp,
                server_timestamp=None,
                hash=data_hash,
                status=SyncStatus.PENDING
            )

            # Check if similar operation already exists
            existing_op = self._find_similar_operation(user_id, resource_type, resource_id, operation)
            if existing_op:
                # Update existing operation instead of creating new one
                existing_op.client_data = data
                existing_op.client_timestamp = timestamp
                existing_op.hash = data_hash
                logger.info(f"Updated existing operation {existing_op.id}")
                return existing_op.id

            self.pending_operations[user_id].append(sync_operation)
            logger.info(f"Added sync operation {operation_id} for user {user_id}")

            return operation_id

        except Exception as e:
            logger.error(f"Failed to add sync operation: {str(e)}")
            raise

    def start_sync_session(self, user_id: str) -> str:
        """Start a new sync session"""
        try:
            with self.sync_locks[user_id]:
                # Check if there's already an active session
                active_sessions = [s for s in self.active_sessions.values()
                                 if s.user_id == user_id and s.status == SyncStatus.IN_PROGRESS]
                if active_sessions:
                    raise Exception("Sync session already in progress")

                # Create new session
                session_id = str(uuid.uuid4())
                operations = self.pending_operations[user_id][:self.max_operations_per_session]

                session = SyncSession(
                    id=session_id,
                    user_id=user_id,
                    started_at=datetime.utcnow(),
                    completed_at=None,
                    status=SyncStatus.IN_PROGRESS,
                    operations=operations,
                    summary={
                        'total': len(operations),
                        'completed': 0,
                        'failed': 0,
                        'conflicts': 0
                    }
                )

                self.active_sessions[session_id] = session

                # Remove queued operations from pending list
                self.pending_operations[user_id] = self.pending_operations[user_id][len(operations):]

                logger.info(f"Started sync session {session_id} for user {user_id} with {len(operations)} operations")

                # Start sync process in background
                threading.Thread(target=self._process_sync_session, args=(session_id,)).start()

                return session_id

        except Exception as e:
            logger.error(f"Failed to start sync session: {str(e)}")
            raise

    def get_sync_status(self, user_id: str) -> Dict[str, Any]:
        """Get sync status for a user"""
        try:
            pending_count = len(self.pending_operations[user_id])
            active_session = None

            for session in self.active_sessions.values():
                if session.user_id == user_id and session.status == SyncStatus.IN_PROGRESS:
                    active_session = session
                    break

            conflicts_count = len(self.conflicts[user_id])

            return {
                'pending_operations': pending_count,
                'active_session': asdict(active_session) if active_session else None,
                'unresolved_conflicts': conflicts_count,
                'last_sync': self._get_last_sync_time(user_id)
            }

        except Exception as e:
            logger.error(f"Failed to get sync status: {str(e)}")
            return {}

    def resolve_conflict(self, user_id: str, conflict_id: str, resolution: ConflictResolutionStrategy,
                        resolved_data: Optional[Dict[str, Any]] = None) -> bool:
        """Resolve a sync conflict"""
        try:
            conflicts = self.conflicts[user_id]
            conflict = None

            for c in conflicts:
                if c.id == conflict_id:
                    conflict = c
                    break

            if not conflict:
                raise Exception("Conflict not found")

            conflict.resolution = resolution
            conflict.resolved_at = datetime.utcnow()

            # Apply resolution
            if resolution == ConflictResolutionStrategy.CLIENT_WINS:
                # Use client data
                self._apply_client_data(conflict)

            elif resolution == ConflictResolutionStrategy.SERVER_WINS:
                # Use server data
                self._apply_server_data(conflict)

            elif resolution == ConflictResolutionStrategy.MERGE:
                # Merge data
                if resolved_data:
                    self._apply_merged_data(conflict, resolved_data)
                else:
                    merged_data = self._auto_merge_data(conflict.client_data, conflict.server_data)
                    self._apply_merged_data(conflict, merged_data)

            elif resolution == ConflictResolutionStrategy.MANUAL:
                # Use manually provided data
                if resolved_data:
                    self._apply_merged_data(conflict, resolved_data)
                else:
                    raise Exception("Manual resolution requires resolved data")

            logger.info(f"Resolved conflict {conflict_id} with strategy {resolution.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to resolve conflict: {str(e)}")
            return False

    def _process_sync_session(self, session_id: str):
        """Process a sync session"""
        try:
            session = self.active_sessions[session_id]
            user_id = session.user_id

            for operation in session.operations:
                if session.status != SyncStatus.IN_PROGRESS:
                    break

                try:
                    success = self._process_operation(operation)
                    if success:
                        session.summary['completed'] += 1
                        operation.status = SyncStatus.COMPLETED
                    else:
                        session.summary['failed'] += 1
                        operation.status = SyncStatus.FAILED

                except Exception as e:
                    logger.error(f"Failed to process operation {operation.id}: {str(e)}")
                    session.summary['failed'] += 1
                    operation.status = SyncStatus.FAILED
                    operation.error_message = str(e)

            # Update session status
            session.completed_at = datetime.utcnow()
            session.status = SyncStatus.COMPLETED

            logger.info(f"Completed sync session {session_id} for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to process sync session {session_id}: {str(e)}")
            if session_id in self.active_sessions:
                self.active_sessions[session_id].status = SyncStatus.FAILED

    def _process_operation(self, operation: SyncOperation) -> bool:
        """Process a single sync operation"""
        try:
            # Simulate server interaction
            # In a real implementation, this would make API calls to the main server

            # Check for conflicts
            if operation.operation in [OperationType.UPDATE, OperationType.DELETE]:
                server_data = self._get_server_data(operation.resource_type, operation.resource_id)
                if server_data and self._has_conflict(operation, server_data):
                    conflict = self._create_conflict(operation, server_data)
                    self.conflicts[operation.user_id].append(conflict)
                    operation.status = SyncStatus.CONFLICT
                    self.active_sessions[self._get_active_session_id(operation.user_id)].summary['conflicts'] += 1
                    return False

            # Apply operation
            if operation.operation == OperationType.CREATE:
                success = self._create_resource(operation)
            elif operation.operation == OperationType.UPDATE:
                success = self._update_resource(operation)
            elif operation.operation == OperationType.DELETE:
                success = self._delete_resource(operation)
            else:
                success = False

            return success

        except Exception as e:
            logger.error(f"Failed to process operation {operation.id}: {str(e)}")
            return False

    def _create_resource(self, operation: SyncOperation) -> bool:
        """Create a new resource on the server"""
        try:
            # Simulate resource creation
            logger.info(f"Creating resource {operation.resource_id} of type {operation.resource_type}")

            # In a real implementation, this would make an API call
            # For now, we'll just simulate success
            time.sleep(0.1)

            return True

        except Exception as e:
            logger.error(f"Failed to create resource: {str(e)}")
            return False

    def _update_resource(self, operation: SyncOperation) -> bool:
        """Update a resource on the server"""
        try:
            # Simulate resource update
            logger.info(f"Updating resource {operation.resource_id} of type {operation.resource_type}")

            # In a real implementation, this would make an API call
            # For now, we'll just simulate success
            time.sleep(0.1)

            return True

        except Exception as e:
            logger.error(f"Failed to update resource: {str(e)}")
            return False

    def _delete_resource(self, operation: SyncOperation) -> bool:
        """Delete a resource on the server"""
        try:
            # Simulate resource deletion
            logger.info(f"Deleting resource {operation.resource_id} of type {operation.resource_type}")

            # In a real implementation, this would make an API call
            # For now, we'll just simulate success
            time.sleep(0.1)

            return True

        except Exception as e:
            logger.error(f"Failed to delete resource: {str(e)}")
            return False

    def _get_server_data(self, resource_type: str, resource_id: str) -> Optional[Dict[str, Any]]:
        """Get current server data for a resource"""
        try:
            # Simulate getting server data
            # In a real implementation, this would make an API call
            return {
                'id': resource_id,
                'type': resource_type,
                'name': 'Server Resource',
                'updated_at': datetime.utcnow().isoformat(),
                'version': 2
            }

        except Exception as e:
            logger.error(f"Failed to get server data: {str(e)}")
            return None

    def _has_conflict(self, operation: SyncOperation, server_data: Dict[str, Any]) -> bool:
        """Check if operation conflicts with server data"""
        try:
            # Simple conflict detection based on timestamps
            server_timestamp = datetime.fromisoformat(server_data.get('updated_at', '1970-01-01T00:00:00'))

            # If server data was updated after client operation, there's a potential conflict
            return server_timestamp > operation.client_timestamp

        except Exception as e:
            logger.error(f"Failed to check for conflicts: {str(e)}")
            return False

    def _create_conflict(self, operation: SyncOperation, server_data: Dict[str, Any]) -> Conflict:
        """Create a conflict record"""
        try:
            conflict_id = str(uuid.uuid4())
            session_id = self._get_active_session_id(operation.user_id)

            # Find conflicting fields
            conflict_fields = []
            for key in operation.client_data:
                if key in server_data and operation.client_data[key] != server_data[key]:
                    conflict_fields.append(key)

            conflict = Conflict(
                id=conflict_id,
                session_id=session_id,
                operation_id=operation.id,
                resource_type=operation.resource_type,
                resource_id=operation.resource_id,
                client_data=operation.client_data,
                server_data=server_data,
                conflict_fields=conflict_fields,
                detected_at=datetime.utcnow()
            )

            logger.info(f"Created conflict {conflict_id} for resource {operation.resource_id}")
            return conflict

        except Exception as e:
            logger.error(f"Failed to create conflict: {str(e)}")
            raise

    def _find_similar_operation(self, user_id: str, resource_type: str, resource_id: str,
                               operation: OperationType) -> Optional[SyncOperation]:
        """Find similar operation in pending queue"""
        try:
            for op in self.pending_operations[user_id]:
                if (op.resource_type == resource_type and
                    op.resource_id == resource_id and
                    op.operation == operation and
                    op.status == SyncStatus.PENDING):
                    return op

            return None

        except Exception as e:
            logger.error(f"Failed to find similar operation: {str(e)}")
            return None

    def _calculate_data_hash(self, data: Dict[str, Any]) -> str:
        """Calculate hash of data for conflict detection"""
        try:
            data_string = json.dumps(data, sort_keys=True)
            return hashlib.sha256(data_string.encode()).hexdigest()

        except Exception as e:
            logger.error(f"Failed to calculate data hash: {str(e)}")
            return str(uuid.uuid4())

    def _get_active_session_id(self, user_id: str) -> Optional[str]:
        """Get active session ID for user"""
        try:
            for session_id, session in self.active_sessions.items():
                if session.user_id == user_id and session.status == SyncStatus.IN_PROGRESS:
                    return session_id

            return None

        except Exception as e:
            logger.error(f"Failed to get active session ID: {str(e)}")
            return None

    def _get_last_sync_time(self, user_id: str) -> Optional[datetime]:
        """Get last successful sync time for user"""
        try:
            last_time = None
            for session in self.active_sessions.values():
                if (session.user_id == user_id and
                    session.status == SyncStatus.COMPLETED and
                    session.completed_at):
                    if not last_time or session.completed_at > last_time:
                        last_time = session.completed_at

            return last_time

        except Exception as e:
            logger.error(f"Failed to get last sync time: {str(e)}")
            return None

    def _apply_client_data(self, conflict: Conflict):
        """Apply client data to resolve conflict"""
        try:
            # In a real implementation, this would update the server with client data
            logger.info(f"Applying client data for conflict {conflict.id}")

        except Exception as e:
            logger.error(f"Failed to apply client data: {str(e)}")
            raise

    def _apply_server_data(self, conflict: Conflict):
        """Apply server data to resolve conflict"""
        try:
            # In a real implementation, this would update the client with server data
            logger.info(f"Applying server data for conflict {conflict.id}")

        except Exception as e:
            logger.error(f"Failed to apply server data: {str(e)}")
            raise

    def _apply_merged_data(self, conflict: Conflict, merged_data: Dict[str, Any]):
        """Apply merged data to resolve conflict"""
        try:
            # In a real implementation, this would update both client and server with merged data
            logger.info(f"Applying merged data for conflict {conflict.id}")

        except Exception as e:
            logger.error(f"Failed to apply merged data: {str(e)}")
            raise

    def _auto_merge_data(self, client_data: Dict[str, Any], server_data: Dict[str, Any]) -> Dict[str, Any]:
        """Automatically merge conflicting data"""
        try:
            merged = server_data.copy()

            # Simple merge strategy: prefer client data for all fields
            # In a real implementation, this would be more sophisticated
            for key, value in client_data.items():
                if key != 'updated_at' and key != 'version':  # Don't override metadata
                    merged[key] = value

            # Update metadata
            merged['updated_at'] = datetime.utcnow().isoformat()
            merged['version'] = server_data.get('version', 1) + 1

            return merged

        except Exception as e:
            logger.error(f"Failed to auto-merge data: {str(e)}")
            return server_data

    def cleanup_old_sessions(self, days: int = 7) -> int:
        """Clean up old sync sessions"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            removed_count = 0

            sessions_to_remove = []
            for session_id, session in self.active_sessions.items():
                if session.started_at < cutoff_date:
                    sessions_to_remove.append(session_id)

            for session_id in sessions_to_remove:
                del self.active_sessions[session_id]
                removed_count += 1

            logger.info(f"Cleaned up {removed_count} old sync sessions")
            return removed_count

        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {str(e)}")
            return 0

    def get_conflicts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all unresolved conflicts for a user"""
        try:
            conflicts = self.conflicts[user_id]
            return [asdict(conflict) for conflict in conflicts if not conflict.resolution]

        except Exception as e:
            logger.error(f"Failed to get conflicts: {str(e)}")
            return []

    def get_session_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get sync session history for a user"""
        try:
            user_sessions = [
                asdict(session) for session in self.active_sessions.values()
                if session.user_id == user_id
            ]

            # Sort by start time (most recent first)
            user_sessions.sort(key=lambda x: x['started_at'], reverse=True)

            return user_sessions[:limit]

        except Exception as e:
            logger.error(f"Failed to get session history: {str(e)}")
            return []

# Global sync service instance
sync_service = OfflineSyncService()

# Flask API endpoints
from flask import Flask, Blueprint, request, jsonify

sync_bp = Blueprint('sync', __name__, url_prefix='/api/sync')

@sync_bp.route('/status', methods=['GET'])
def get_sync_status():
    """Get sync status for user"""
    try:
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User ID required'
            }), 400

        status = sync_service.get_sync_status(user_id)
        return jsonify({
            'success': True,
            'data': status
        })

    except Exception as e:
        logger.error(f"Get sync status error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@sync_bp.route('/start', methods=['POST'])
def start_sync():
    """Start a sync session"""
    try:
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User ID required'
            }), 400

        session_id = sync_service.start_sync_session(user_id)

        return jsonify({
            'success': True,
            'data': {
                'session_id': session_id
            },
            'message': 'Sync session started'
        })

    except Exception as e:
        logger.error(f"Start sync error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sync_bp.route('/conflicts', methods=['GET'])
def get_conflicts():
    """Get unresolved conflicts"""
    try:
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User ID required'
            }), 400

        conflicts = sync_service.get_conflicts(user_id)

        return jsonify({
            'success': True,
            'data': conflicts
        })

    except Exception as e:
        logger.error(f"Get conflicts error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@sync_bp.route('/conflicts/<conflict_id>/resolve', methods=['POST'])
def resolve_conflict(conflict_id):
    """Resolve a conflict"""
    try:
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User ID required'
            }), 400

        data = request.get_json()
        resolution = ConflictResolutionStrategy(data.get('resolution'))
        resolved_data = data.get('resolved_data')

        success = sync_service.resolve_conflict(user_id, conflict_id, resolution, resolved_data)

        if success:
            return jsonify({
                'success': True,
                'message': 'Conflict resolved successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to resolve conflict'
            }), 500

    except Exception as e:
        logger.error(f"Resolve conflict error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@sync_bp.route('/history', methods=['GET'])
def get_session_history():
    """Get sync session history"""
    try:
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User ID required'
            }), 400

        limit = request.args.get('limit', 10, type=int)

        history = sync_service.get_session_history(user_id, limit)

        return jsonify({
            'success': True,
            'data': history
        })

    except Exception as e:
        logger.error(f"Get history error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

if __name__ == '__main__':
    # Create Flask app for testing
    app = Flask(__name__)
    app.register_blueprint(sync_bp)

    # Add some test data
    app.run(host='0.0.0.0', port=3003, debug=True)