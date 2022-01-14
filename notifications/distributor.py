from collections import defaultdict
from typing import Iterable
import json
import os

import requests
from aws_lambda_powertools import Logger

from cw_alarm import CloudWatchAlarm
from codepipeline import CodePipelineNotification

COLOR_WHITE = '#eeeeee'
COLOR_RED = '#a6364f'
COLOR_GREEN = '#36a64f'

SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
LOG = Logger()

LOG.info(f'SLACK_WEBHOOK_URL is {SLACK_WEBHOOK_URL}')


pipeline_state_emojis = defaultdict(lambda: '❓', {
    'FAILED': '‼️',
    'STARTED': '▶️',
    'CANCELED': '✋',
    'RESUMED': '⏯',
    'STOPPED': '⏹',
    'SUCCEEDED': '✅',
})

pipeline_colors = defaultdict(lambda: COLOR_WHITE, {
    'FAILED': COLOR_RED,
    'SUCCEEDED': COLOR_GREEN,
})

def forward_pipeline_notifications(notifications: Iterable[CodePipelineNotification]):
    if SLACK_WEBHOOK_URL is not None:
        for notification in notifications:
            region, account_id = notification.pipeline_arn.split(':')[3:5]
            fields = [{
                'title': 'Pipeline',
                'value': notification.pipeline_name,
                'short': True,
            }, {
                'title': 'State',
                'value': notification.state,
                'short': True,
            }, {
                'title': 'Region/Account',
                'value': f'{region}/{account_id}',
                'short': True,
            }, {
                'title': 'Execution',
                'value': notification.execution_id,
                'short': True,
            }, {
                'title': 'Time',
                'value': notification.timestamp,
                'short': True,
            }]
            console_url = f'https://{region}.console.aws.amazon.com/codesuite/codepipeline/pipelines/{notification.pipeline_name}/executions/{notification.execution_id}/visualization?region={region}'

            emoji = pipeline_state_emojis.get(notification.state)
            color = pipeline_colors.get(notification.state)
            text = f'Pipeline {notification.pipeline_name} is {notification.state}'
            body = {
                'text': text,
                'attachments': [{
                    'mrkdwn_in': ['text'],
                    'color': color,
                    'pretext': text,
                    'title': f'{emoji} {notification.pipeline_name} is {notification.state}',
                    'title_link': console_url,
                    'text': 'A CodePipeline execution has changed state',
                    'fields': fields
                }]
            }

            LOG.info('Sending message to Slack', extra={'body': body})
            requests.post(SLACK_WEBHOOK_URL, json.dumps(body))


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
                    'fields': fields
                }]
            }

            LOG.info('Sending message to Slack', extra={'body': body})
            requests.post(SLACK_WEBHOOK_URL, json.dumps(body))
