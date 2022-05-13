from datetime import datetime
from wrfcloud.api.audit import AuditEntry


def test_audit_entry() -> None:
    """
    Test the audit entry class
    :return: None
    """
    # create a sample audit log entry
    a1 = AuditEntry()
    a1.ref_id = 'ASDF'
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
    assert count == 8
