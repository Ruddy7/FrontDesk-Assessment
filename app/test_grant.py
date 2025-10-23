"""
Test different methods to add video grants
"""
import os
import jwt as pyjwt
import json
from dotenv import load_dotenv
from livekit.api import AccessToken, VideoGrants

load_dotenv()

LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

print("Testing different grant methods...\n")

# Create grants object
grants = VideoGrants(
    room_join=True,
    room="test-room",
    can_publish=True,
    can_subscribe=True
)

print("Method 1: token.video_grant = grants")
print("-" * 50)
try:
    token = AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    token.identity = "test-user"
    token.video_grant = grants
    jwt_token = token.to_jwt()
    decoded = pyjwt.decode(jwt_token, options={"verify_signature": False})
    print("Result:", "video" in decoded)
    if "video" in decoded:
        print("✓ SUCCESS! Video grants:", decoded["video"])
    else:
        print("✗ FAILED - no video grants")
except Exception as e:
    print(f"✗ ERROR: {e}")

print("\nMethod 2: token.grants.video = grants")
print("-" * 50)
try:
    token = AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    token.identity = "test-user"
    token.grants.video = grants
    jwt_token = token.to_jwt()
    decoded = pyjwt.decode(jwt_token, options={"verify_signature": False})
    print("Result:", "video" in decoded)
    if "video" in decoded:
        print("✓ SUCCESS! Video grants:", decoded["video"])
    else:
        print("✗ FAILED - no video grants")
except Exception as e:
    print(f"✗ ERROR: {e}")

print("\nMethod 3: Inspect AccessToken object")
print("-" * 50)
token = AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
print("Token attributes:", [x for x in dir(token) if not x.startswith('_')])
print("\nLooking for grant-related attributes:")
for attr in dir(token):
    if 'grant' in attr.lower() or 'video' in attr.lower():
        print(f"  - {attr}: {type(getattr(token, attr, None))}")

print("\nMethod 4: Check VideoGrants object")
print("-" * 50)
print("VideoGrants attributes:", [x for x in dir(grants) if not x.startswith('_')])
print("\nVideoGrants values:")
for attr in ['room_join', 'room', 'can_publish', 'can_subscribe']:
    if hasattr(grants, attr):
        print(f"  - {attr}: {getattr(grants, attr)}")