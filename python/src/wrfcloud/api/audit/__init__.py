"""
This module holds functions for audit log operations
"""

__all__ = ['AuditEntry', 'AuditDao', 'save_audit_log_entry']

from wrfcloud.api.audit.entry import AuditEntry
from wrfcloud.api.audit.audit_dao import AuditDao


def save_audit_log_entry(log_entry: AuditEntry) -> bool:
    """
    Save an audit log entry to the database
    :param: The audit log entry data to save
    :return: True if successfully saved, otherwise False
    """
    # get the data access object
    dao = AuditDao()

    # save the entry to the audit log
    return dao.save_entry(log_entry)
