"""
Lambda handler module invoked during stack create and update.
Adds monitoring and alarms for new/updated resouces
"""
import json

from aws_lambda_powertools import Logger

from cw_alarm import CloudWatchAlarm
from distributor import forward_alarms

LOG = Logger()


def sns_msg_to_alarm(sns_msg: dict, timestamp: str, subject: str) -> CloudWatchAlarm:
    """ Convert an Alarm represented in an SNS message to a CloudWatchAlarm """
    return CloudWatchAlarm(
        new_state=sns_msg['NewStateValue'],
        old_state=sns_msg['OldStateValue'],
        reason=sns_msg['NewStateReason'],
        timestamp=timestamp,
        subject=subject,
        alarm_name=sns_msg['AlarmName'],
        account_id=sns_msg['AWSAccountId'],
        region=sns_msg['Region'],
        region_id=sns_msg['AlarmArn'].split(':')[3],
        trigger=sns_msg['Trigger']
    )


@LOG.inject_lambda_context
def handle_event(event, _):
    """ Handle SNS messages sent via SQS """
    sqs_records = [json.loads(record['body']) for record in event['Records']]
    alarms = [sns_msg_to_alarm(
        json.loads(rec['Message']),
        rec['Timestamp'],
        rec['Subject'],
    ) for rec in sqs_records]

    forward_alarms(alarms)
