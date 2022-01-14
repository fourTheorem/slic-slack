import json
import pytest
from notifications import topic_handler


@pytest.fixture()
def sns_msg():
    return {
        "account": "1234567890123",
        "detailType": "CodePipeline Pipeline Execution State Change",
        "region": "eu-west-1",
        "source": "aws.codepipeline",
        "time": "2022-01-14T14:30:52Z",
        "notificationRuleArn": "arn:aws:codestar-notifications:eu-west-1:1234567890123:notificationrule/3866bf6f924beae736cbb06bc8ac8e1f33d735be",
        "detail": {"pipeline": "slic-starter-dev",
                   "execution-id": "03d35bba-7d0d-44bb-9619-15686abb757e",
                   "state": "SUCCEEDED",
                   "version": 8.0},
        "resources": ["arn:aws:codepipeline:eu-west-1:1234567890123:slic-starter-dev"],
        "additionalAttributes": {}
    }


@pytest.fixture()
def sns_body(sns_msg):
    return {
        'Type': 'Notification',
        'MessageId': '5c11fdcd-2096-5ab4-8d58-a796abc9130d',
        'TopicArn': 'arn:aws:sns:eu-west-1:1234567890123:devPipelineNotifications',
        'Message': sns_msg,
        'Timestamp': '2022-01-14T14:30:55.771Z',
        'SignatureVersion': '1',
        'Signature': 'jAY1Asnxn8t857YHE49eQ5MTbXa4gANCeLhmiME5kj5Nn6Vj57NOZGLsOy+wlgP+IWLtzn2l0Knz5azLER7mIWRWeG/Is3QsWzZOi7jHpS8T1AO+nCypjd7nKszp6/Wp7krS47+f5y32uMCC0TFDT/1Bq3ll8KI54Sh8SLHd8ohXC5YqjBt3Lsl/wPSOUq7AlAU2FLAZUMtgwi56HAmZ/C22k6khNvjOtEo3XHsJXYHaLq5mz3b9PaEj4E18KmLpvT1bLzDmReu/2CQQi3PT0hu34XgmB9O5VGhP6hi0zKOs1/eheNtO1P94Zl30wKfNhkgi32GVH8NHRiFYZhSZDA==',
        'SigningCertURL': 'https://sns.eu-west-1.amazonaws.com/SimpleNotificationService-7ff5318490ec183fbaddaa2a969abfda.pem',
        'UnsubscribeURL': 'https://sns.eu-west-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:eu-west-1:1234567890123:devPipelineNotifications:77f602f6-ecb8-4cd8-b0df-e28afbed8862'
    }

@pytest.fixture()
def event(sns_body):
    return {
        "Records": [
            {
                "messageId": "6c06e2d9-b9e8-4e2b-ad82-b50fae200d0d",
                "receiptHandle": "AQEBG52IksgqEVMqIk5Qi0w/o2CSFJLjB7Et/FURZw3pfig2cQYgv9FIrurGx11nh8oDcr0w/MG6Q4Gpwp54ZjTW+/x9Ma2CQBQGjLZeyAb+HCDvbgKyXUB76i+0NF4Zq/Eddyvgq73h7x6GW0noLdhjnyw5xG2jY5JBEzP6nKlUK4fmOwNxdJWzuiblJSkWv0bEqGIgIWg5RGnpISqjtM+pQ7a0cipqC020ntDo/FFdiSY0yBmAbypb9T3WPOqoQDteF9ylQbe+19Z335IaL7Q4iiWlWI2WirR6QJdewwHVbYCI8ZScIjPkWKGJAswdVVmfGzWqhNd+rMlG3RxPv7J3QGTi1ZJsSMyWYhbXBfevt5Y5kCOAUMF1v67iUsjVycDjyoh8/XMRRIDKLJfjToIjJdKowSEZ/YNUHRM9bQfHuw/wZYfVwgQ/DQ/ze/GMWrdI0XD6pqDmWph5M/iBOPmx+Q==",
                "body": json.dumps(sns_body),
                "attributes": {
                    "ApproximateReceiveCount": "12",
                    "SentTimestamp": "1642170655813",
                    "SenderId": "AIDAISMY7JYY5F7RTT6AO",
                    "ApproximateFirstReceiveTimestamp": "1642170655813"
                },
                "messageAttributes": {},
                "md5OfBody": "6cb3bb4111b22b116f02aa43ab591910",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:eu-west-1:1234567890123:slic-slack-dev-deploys-AlarmNotificationProcessorSNSEventQueue-MY53WLPPCGDP",
                "awsRegion": "eu-west-1"
            }
        ]
    }


@pytest.fixture()
def timestamp():
    return "2020-01-01T00:00:00.000Z"


def test_codepipeline_sns_msg(sns_msg, timestamp):
    pipeline_notification = topic_handler.sns_msg_to_codepipeline_notification(sns_msg, timestamp)
    assert pipeline_notification.pipeline_name == "slic-starter-dev"


def test_failed_codepipeline_sns_msg(timestamp):
    failed_sns_msg = {
        "account": "1234567890123",
        "detailType": "CodePipeline Pipeline Execution State Change",
        "region": "eu-west-1",
        "source": "aws.codepipeline",
        "time": "2022-01-14T14:57:55Z",
        "notificationRuleArn": "arn:aws:codestar-notifications:eu-west-1:1234567890123:notificationrule/3866bf6f924beae736cbb06bc8ac8e1f33d735be",
        "detail": {"pipeline": "slic-starter-dev",
                   "execution-id": "cb6b0959-47c4-4f0a-b72d-b67e7161e038",
                   "state": "FAILED",
                   "version": 8.0},
        "resources": ["arn:aws:codepipeline:eu-west-1:1234567890123:slic-starter-dev"],
        "additionalAttributes": {"failedActionCount": 1,
                                 "failedActions": [{"action": "CdkSynth",
                                                    "additionalInformation": "Build terminated with state: FAILED"}],
                                 "failedStage": "CdkSynth"}
    }
    notification = topic_handler.sns_msg_to_codepipeline_notification(failed_sns_msg, timestamp)
    assert notification.failed_actions == [{"action": "CdkSynth",
                                           "additionalInformation": "Build terminated with state: FAILED"}]
    assert notification.failed_stage == "CdkSynth"
