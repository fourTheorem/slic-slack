"""
Lambda handler module invoked during stack create and update.
Adds monitoring and alarms for new/updated resources
"""
import json

from aws_lambda_powertools import Logger

from cw_alarm import CloudWatchAlarm
from codepipeline import CodePipelineNotification
from distributor import forward_alarms, forward_pipeline_notifications

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


def sns_msg_to_codepipeline_notification(sns_msg: dict, timestamp: str) -> CodePipelineNotification:
    """ Convert an Alarm represented in an SNS message to a CodePipeline notification"""
    """
    {"failedActionCount": 1,
                                 "failedActions": [{"action": "CdkSynth",
                                                    "additionalInformation": "Build terminated with state: FAILED"}],
                                 "failedStage": "CdkSynth"}
    """
    additional_attrs = sns_msg.get('additionalAttributes', {})
    failed_stage = additional_attrs.get('failedStage')
    failed_actions = additional_attrs.get('failedActions')

    return CodePipelineNotification(
        timestamp=timestamp,
        pipeline_arn=sns_msg['resources'][0],
        state=sns_msg['detail']['state'],
        pipeline_name=sns_msg['detail']['pipeline'],
        execution_id=sns_msg['detail']['execution-id'],
        failed_stage=failed_stage,
        failed_actions=failed_actions,
    )


@LOG.inject_lambda_context
def handle_event(event, _):
    """ Handle SNS messages sent via SQS """
    sqs_records = [json.loads(record['body']) for record in event['Records']]
    alarms = []
    pipeline_notifications = []

    for rec in sqs_records:
        message = json.loads(rec['Message'])
        if 'AlarmName' in message:
            alarms.append(sns_msg_to_alarm(
                message,
                rec['Timestamp'],
                rec['Subject'],
            ))
        elif message.get('source') == 'aws.codepipeline':
            pipeline_notifications.append(sns_msg_to_codepipeline_notification(
                message,
                rec['Timestamp']
            ))

        forward_alarms(alarms)
        forward_pipeline_notifications(pipeline_notifications)
