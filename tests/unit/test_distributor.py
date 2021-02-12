from datetime import datetime
from unittest.mock import patch
from cw_alarm import CloudWatchAlarm
import distributor


@patch('distributor.requests.post')
def test_forward_events(mock_post):
    alarms = CloudWatchAlarm(
        new_state='ALARM',
        old_state='OK',
        reason='Something happened',
        timestamp=datetime.now().isoformat(),
        subject='An alarm',
        alarm_name='TheAlarm',
        account_id='1234567890123',
        region='us-east-1',
        trigger={},
    )
    distributor.forward_alarms([alarms])
    assert mock_post.called_once()
