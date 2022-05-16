"""
The AuditEntry class is the data model used to represent an audit log entry
"""

from typing import Union
from wrfcloud.log import Logger


class AuditEntry:
    """
    Audit log entry data object
    """

    def __init__(self, data: Union[dict, None] = None):
        """
        Initialize the audit data object
        """
        self.log = Logger()

        self.ref_id: Union[str, None] = None
        self.action: Union[str, None] = None
        self.authenticated: Union[bool, None] = None
        self.username: Union[str, None] = None
        self.ip_address: Union[str, None] = None
        self.start_time: Union[float, None] = None
        self.end_time: Union[float, None] = None
        self.duration_ms: Union[int, None] = None
        self.action_success: Union[bool, None] = None

        # initialize from dictionary if provided
        if data is not None:
            self.data = data

    @property
    def data(self) -> dict:
        return {
            'ref_id': self.ref_id,
            'action': self.action,
            'authenticated': self.authenticated,
            'username': self.username,
            'ip_address': self.ip_address,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration_ms': self.duration_ms,
            'action_success': self.action_success
        }

    @data.setter
    def data(self, data: dict) -> None:
        self.ref_id = data['ref_id'] if 'ref_id' in data else None
        self.action = data['action'] if 'action' in data else None
        self.authenticated = data['authenticated'] if 'authenticated' in data else None
        self.username = data['username'] if 'username' in data else None
        self.ip_address = data['ip_address'] if 'ip_address' in data else None
        self.start_time = data['start_time'] if 'start_time' in data else None
        self.end_time = data['end_time'] if 'end_time' in data else None
        self.duration_ms = data['duration_ms'] if 'duration_ms' in data else None
        self.action_success = data['action_success'] if 'action_success' in data else None
