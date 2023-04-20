"""
Test the wrfcloud.api.audit module
"""


from datetime import datetime
from random import random
from wrfcloud.system import init_environment
from wrfcloud.api.audit import AuditEntry
from wrfcloud.api.audit import save_audit_log_entry
from wrfcloud.api.audit import get_audit_log_entry
from wrfcloud.api.audit import get_all_audit_logs
from wrfcloud.api.handler import create_reference_id
from helper import _test_setup, _test_teardown


init_environment(env='test')


def test_audit_entry() -> None:
    """
    Test the audit entry class
    :return: None
    """
    # create a sample audit log entry
    a1 = AuditEntry()
    a1.ref_id = create_reference_id()
    a1.authenticated = True
    a1.username = 'user@example.com'
    a1.ip_address = '10.0.0.151'
    a1.start_time = datetime.timestamp(datetime.utcnow())
    a1.end_time = a1.start_time + 3.34
    a1.duration_ms = 1000 * (a1.end_time - a1.start_time)
    a1.action_success = True

    # create a new audit log entry and copy the sample data into it
    a2 = AuditEntry()
    a2.data = a1.data

    # make sure all values were copied correctly
    count = 0
    for key in a1.data:
        assert a1.data[key] == a2.data[key]
        count += 1
    assert count == 9


def test_audit_dao_read_entry() -> None:
    """
    Test the audit entry class
    :return: None
    """
    # set up the test
    assert _test_setup()

    # create some sample data
    entries = []
    sample_size = 7500
    for _ in range(sample_size):
        # create a sample audit log entry
        audit = AuditEntry()
        audit.ref_id = create_reference_id()
        audit.action = ['Login', 'ChangePassword'][int(random() * 20) % 2]
        audit.authenticated = random() > 0.5
        audit.username = 'user@example.com'
        audit.ip_address = '10.0.0.' + str(int(random() * 199) + 1)
        audit.start_time = datetime.timestamp(datetime.utcnow())
        audit.end_time = audit.start_time + 3.34
        audit.duration_ms = 1000 * (audit.end_time - audit.start_time)
        audit.action_success = random() < 0.5
        entries.append(audit)

    # write the data to the database
    for entry in entries:
        assert save_audit_log_entry(entry)

    # read and compare random entries
    for _ in range(50):
        index = int(random() * len(entries))
        entry = entries[index]
        entry_ = get_audit_log_entry(entry.ref_id)

        assert entry.ref_id == entry_.ref_id
        assert entry.action == entry_.action
        assert entry.authenticated == entry_.authenticated
        assert entry.username == entry_.username
        assert entry.ip_address == entry_.ip_address
        assert entry.start_time == entry_.start_time
        assert entry.end_time == entry_.end_time
        assert entry.duration_ms == entry_.duration_ms
        assert entry.action_success == entry_.action_success

    # get all audit log entries
    all_entries = get_all_audit_logs()
    assert len(all_entries) == sample_size

    # try to get an entry that does not exist
    assert get_audit_log_entry(create_reference_id()) is None

    # teardown the test resources
    assert _test_teardown()
