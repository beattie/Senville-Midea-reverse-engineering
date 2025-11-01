#!/usr/bin/env python3
"""Check available fan/deflector controls"""

import os
from midea_beautiful import appliance_state

# Load environment variables from .env file
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env()

# Get credentials from environment
ip = os.getenv('SENVILLE_IP')
token = os.getenv('SENVILLE_TOKEN')
key = os.getenv('SENVILLE_KEY')

if not all([ip, token, key]):
    print("ERROR: Missing credentials in .env file")
    print("Required: SENVILLE_IP, SENVILLE_TOKEN, SENVILLE_KEY")
    exit(1)

device = appliance_state(
    address=ip,
    token=token,
    key=key
)

state = device.state

print('Fan/Swing/Deflector attributes:')
print('='*50)

# Check all attributes that might relate to fan direction
attrs = [a for a in dir(state) if 'swing' in a.lower() or 'fan' in a.lower() or
         'straight' in a.lower() or 'avoid' in a.lower() or 'deflect' in a.lower()]

for attr in attrs:
    if not attr.startswith('_') and not callable(getattr(state, attr)):
        try:
            value = getattr(state, attr)
            print(f'  {attr:25} = {value}')
        except:
            pass

print('\nCapabilities related to fan:')
print('='*50)
caps = state.capabilities
for key, val in caps.items():
    if 'fan' in key.lower() or 'swing' in key.lower():
        print(f'  {key:25} = {val}')
