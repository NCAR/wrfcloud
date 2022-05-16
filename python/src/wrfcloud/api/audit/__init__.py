"""
This module holds functions for audit log operations
"""

__all__ = ['AuditEntry', 'AuditDao', 'save_audit_log_entry', 'get_audit_log_entry',
           'get_all_audit_logs']

from typing import Union, List
from wrfcloud.api.audit.entry import AuditEntry
from wrfcloud.api.audit.audit_dao import AuditDao


def save_audit_log_entry(log_entry: AuditEntry) -> bool:
    """
    Save an audit log entry to the database
    :param log_entry: The audit log entry data to save
    :return: True if successfully saved, otherwise False
    """
    # get the data access object
    dao = AuditDao()

    # save the entry to the audit log
    return dao.save_entry(log_entry)


def get_audit_log_entry(ref_id: str) -> Union[AuditEntry, None]:
    """
    Get an audit log entry by reference ID
    :param ref_id: Reference ID of the desired log
    :return: Requested audit log entry, or None if not found
    """
    # get the data access object
    dao = AuditDao()

    # find the log entry with the given ID
    return dao.read_entry(ref_id)


def get_all_audit_logs() -> List[AuditEntry]:
    """
    Get all available audit log entries
    :return: Requested audit log entry, or None if not found
    """
    # get the data access object
    dao = AuditDao()

    # get all the entries
    return dao.get_all_entries()
