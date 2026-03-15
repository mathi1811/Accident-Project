import os
import sys
import types
import json

# Use sample credentials (do not send SMS for real)
os.environ['TWILIO_ACCOUNT_SID'] = 'ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
os.environ['TWILIO_AUTH_TOKEN'] = 'sample_auth_token'
os.environ['TWILIO_FROM_NUMBER'] = '+15550000000'
os.environ['TWILIO_TO_NUMBER'] = '+15551111111'

# Build a sample payload
sample_payload = {
    'plate': 'ABC1234',
    'confidence': 0.95,
    'image_path': None,
    'extra': {'location': 'Test Location'}
}

# Create a fake twilio.rest module with a Client that doesn't send SMS
fake_rest = types.ModuleType('twilio.rest')
class FakeMessage:
    def __init__(self, sid):
        self.sid = sid

class FakeMessages:
    def create(self, body, from_, to):
        print('FakeMessages.create called:')
        print('  body:', body)
        print('  from:', from_)
        print('  to:', to)
        return FakeMessage('SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')

class FakeClient:
    def __init__(self, sid, token):
        print(f'FakeClient initialized with sid={sid}, token={token}')
        self.messages = FakeMessages()

fake_rest.Client = FakeClient

# Ensure top-level 'twilio' package exists in sys.modules and points to a module whose 'rest' attribute is our fake_rest
if 'twilio' not in sys.modules:
    fake_twilio = types.ModuleType('twilio')
    fake_twilio.rest = fake_rest
    sys.modules['twilio'] = fake_twilio
else:
    # override rest submodule
    tw = sys.modules['twilio']
    tw.rest = fake_rest
    sys.modules['twilio.rest'] = fake_rest

# Also set sys.modules entry for 'twilio.rest'
sys.modules['twilio.rest'] = fake_rest

# Now import the app's send_report and run it
from app import send_report

print('\nCalling send_report with sample payload (dry-run)...')
result = send_report(sample_payload)
print('Result:', json.dumps(result, indent=2))

# Clean up fake modules (optional)
# Note: Not strictly necessary in a short script
