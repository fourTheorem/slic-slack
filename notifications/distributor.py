from typing import Iterable
import json
import os

import requests
from aws_lambda_powertools import Logger

from cw_alarm import CloudWatchAlarm

COLOR_RED = '#a6364f'
COLOR_GREEN = '#36a64f'

SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
LOG = Logger()

LOG.info(f'SLACK_WEBHOOK_URL is {SLACK_WEBHOOK_URL}')


def forward_alarms(alarms: Iterable[CloudWatchAlarm]):
    """ Forward alarms to configured destinations """
    if SLACK_WEBHOOK_URL is not None:
        for alarm in alarms:
            fields = [{
                'title': 'Metric',
                'value': alarm.trigger['MetricName'],
                'short': True,
            }, {
                'title': 'Namespace',
                'value': alarm.trigger['Namespace'],
                'short': True,
            }] if 'MetricName' in alarm.trigger else []

            fields.extend([
                {
                    'title': 'Time',
                    'value': alarm.timestamp,
                    'short': True,
                },
                {
                    'title': 'Alarm',
                    'value': alarm.alarm_name,
                    'short': True,
                },
                {
                    'title': 'Account',
                    'value': alarm.account_id,
                    'short': True,
                },
                {
                    'title': 'Region',
                    'value': alarm.region,
                    'short': True,
                }
            ])
            console_url = f'https://{alarm.region_id}.console.aws.amazon.com/cloudwatch/home?alarm.region={alarm.region_id}#alarmsV2:alarm/{alarm.alarm_name}'
            emoji = '⚠️' if alarm.new_state == 'ALARM' else '🆗'
            body = {
                'text': alarm.subject,
                'attachments': [{
                    'mrkdwn_in': ['text'],
                    'color': COLOR_RED if alarm.new_state == 'ALARM' else COLOR_GREEN,
                    'pretext': f'{alarm.new_state} (was {alarm.old_state})',
                    'title': f'{emoji} {alarm.new_state} {alarm.alarm_name}',
                    'title_link': console_url,
                    'text': alarm.reason,
                    'fields': fields,
                    'image_url': alarm.image_url
                }]
            }

            LOG.info('Sending message to Slack', extra={'body': body})
            response = requests.post(SLACK_WEBHOOK_URL, json.dumps(body))
            LOG.info('Slack response', extra={
                'text': response.text,
                'status_code': response.status_code,
                'headers': response.headers,
            })
