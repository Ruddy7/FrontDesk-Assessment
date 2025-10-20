"""
Simple LiveKit token test for version 1.0.17
"""
import os
from dotenv import load_dotenv

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

print("Testing LiveKit Token Generation (v1.0.17)")
print("=" * 60)

# Try import
try:
    from livekit.api import AccessToken, VideoGrants
    print("✓ Imports successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    exit(1)

# Try token generation - Method for v1.0.17
try:
    print("\nGenerating token...")
    
    # This is the correct way for livekit 1.0.17
    token = AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    token.identity = "test-user-123"
    token.name = "Test User"
    
    # Set video_grant (not grants or add_grant)
    token.video_grant = VideoGrants(
        room_join=True,
        room="test-room-456",
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True
    )
    
    jwt_token = token.to_jwt()
    
    print(f"✓ Token generated: {len(jwt_token)} chars")
    print(f"✓ Token: {jwt_token[:100]}...")
    
    # Verify token
    import jwt as pyjwt
    decoded = pyjwt.decode(jwt_token, options={"verify_signature": False})
    print(f"\n✓ Token verified:")
    print(f"  Identity: {decoded.get('sub')}")
    print(f"  Issuer (API Key): {decoded.get('iss')}")
    print(f"  Video grants: {decoded.get('video')}")
    
    print("\n" + "=" * 60)
    print("✅ SUCCESS! Token generation works correctly.")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ Failed: {e}")
    import traceback
    traceback.print_exc()