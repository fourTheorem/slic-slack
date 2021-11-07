"""
Lambda handler module invoked during stack create and update.
Adds monitoring and alarms for new/updated resouces
"""
import boto3
import base64
import json
import os
from uuid import uuid4

from aws_lambda_powertools import Logger

from cw_alarm import CloudWatchAlarm
from distributor import forward_alarms

LOG = Logger()
ALARM_IMAGE_BUCKET_NAME = os.environ['ALARM_IMAGE_BUCKET_NAME']
LOG.info(f'ALARM_IMAGE_BUCKET_NAME={ALARM_IMAGE_BUCKET_NAME}')
IMAGE_URL_EXPIRATION = 7 * 24 * 60 * 60

cw_client = boto3.client('cloudwatch')
s3_client = boto3.client('s3')


def get_alarm_image_url(msg):
    """ Create an image of the metric under alarm """
    try:
        region = msg['AlarmArn'].split(':')[3]
        trigger = msg['Trigger']
        stat = trigger['Statistic']
        stat = (stat[0].upper() + stat[1:].lower())  # 'MAXIMUM' -> 'Maximum'

        period = trigger['Period']
        dim = trigger['Dimensions'][0]

        graph = {
            'region': region,
            'metrics': [
                [ trigger['Namespace'], trigger['MetricName'], dim['name'], dim['value'], { 'stat': stat }]
            ],
            'view': 'timeSeries',
            'stacked': False,
            'period': period,
            'annotations': {
                'horizontal': [
                    {
                        'label': msg['AlarmDescription'],
                        'value': trigger['Threshold']
                    }
                ]
            },
            'title': msg['AlarmName'],
            'width': 800,
            'height': 400,
            'start': '-PT3H',
            'end': 'P0D'
        }
        image_bytes = cw_client.get_metric_widget_image(
            MetricWidget=json.dumps(graph), OutputFormat='png'
            )['MetricWidgetImage']
        key = f'{trigger["Namespace"]}/{trigger["MetricName"]}/{str(uuid4())}.png'
        s3_client.put_object(
            Bucket=ALARM_IMAGE_BUCKET_NAME,
            Key=key,
            Body=image_bytes,
            ContentType='image/png'
        )
        url = s3_client.generate_presigned_url('get_object', Params={
            'Bucket': ALARM_IMAGE_BUCKET_NAME,
            'Key': key
        }, ExpiresIn=IMAGE_URL_EXPIRATION)
        return url

    except Exception as e:
        LOG.error(f'Failed to create alarm image: {e}')
        return None


def sns_msg_to_alarm(sns_msg: dict, timestamp: str, subject: str) -> CloudWatchAlarm:
    """ Convert an Alarm represented in an SNS message to a CloudWatchAlarm """
    alarm_image_url = get_alarm_image_url(sns_msg)
    region = sns_msg['AlarmArn'].split(':')[3]
    return CloudWatchAlarm(
        new_state=sns_msg['NewStateValue'],
        old_state=sns_msg['OldStateValue'],
        reason=sns_msg['NewStateReason'],
        timestamp=timestamp,
        subject=subject,
        alarm_name=sns_msg['AlarmName'],
        account_id=sns_msg['AWSAccountId'],
        region=region,
        region_id=sns_msg['AlarmArn'].split(':')[3],
        trigger=sns_msg['Trigger'],
        image_url=alarm_image_url
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
