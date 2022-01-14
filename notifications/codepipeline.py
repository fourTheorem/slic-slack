from dataclasses import dataclass
from typing import List, Dict


@dataclass
class CodePipelineNotification:
    """ Class representing a CodePipeline notification """
    pipeline_arn: str
    pipeline_name: str
    state: str
    execution_id: str
    timestamp: str
    failed_actions: List[Dict]
    failed_stage: str
