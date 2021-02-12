# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.10.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %%
import os, sys, json
from pathlib import Path

# %%
os.environ['SLACK_WEBHOOK_URL'] = 'https://hooks.slack.com/services/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'

# %%
slic_slack_root = Path(os.environ['PWD']) / 'slic-slack'
sys.path.append(str(slic_slack_root))
sys.path.append(str(slic_slack_root / 'notifications'))

# %%
from notifications import distributor, cw_alarm, topic_handler

# %%
with open('/tmp/whatever.json') as f:
    o = json.load(f)

# %%
o['message']


# %%
class DummyContext:
    def __init__(self):
        self.function_name = 'fn'
        self.memory_limit_in_mb = 3008
        self.invoked_function_arn = 'aws:whatevs'
        self.aws_request_id = 'whatevers'


# %%
json.loads(json.loads(o['message']['Records'][0]['body'])['Message'])

# %%
topic_handler.handle_event(o['message'], DummyContext())
