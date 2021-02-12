from dataclasses import dataclass

@dataclass
class CloudWatchAlarm:
    """ Class representing a triggered CloudWatch Alarm """

    new_state: str
    old_state: str
    reason: str
    timestamp: str
    subject: str
    alarm_name: str
    account_id: str
    region: str  # e.g., EU (Ireland)
    region_id: str  # e.g., eu-west-1
    trigger: dict
