"""
Final verification that token generation works correctly
"""
import os
import jwt as pyjwt
import json
from dotenv import load_dotenv
from livekit.api import AccessToken, VideoGrants

load_dotenv()

LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

print("=" * 70)
print("FINAL TOKEN VERIFICATION")
print("=" * 70)

room_name = "test-room-final"
identity = "test-caller-final"
role = "caller"

try:
    # Create grants
    grants = VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True
    )
    
    # Create token with method chaining
    token = (
        AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_name(f"{role}_{identity}")
        .with_grants(grants)
        .with_metadata(json.dumps({"role": role}))
    )
    
    jwt_token = token.to_jwt()
    
    print(f"\n✓ Token generated: {len(jwt_token)} characters")
    
    # Decode and verify
    decoded = pyjwt.decode(jwt_token, options={"verify_signature": False})
    
    print("\nDecoded token contents:")
    print(json.dumps(decoded, indent=2))
    
    # Validate
    print("\n" + "=" * 70)
    print("VALIDATION")
    print("=" * 70)
    
    checks = []
    checks.append(("Issuer (API Key)", decoded.get("iss") == LIVEKIT_API_KEY))
    checks.append(("Identity", decoded.get("sub") == identity))
    checks.append(("Has video grants", "video" in decoded))
    
    if "video" in decoded:
        video = decoded["video"]
        checks.append(("Room name", video.get("room") == room_name))
        checks.append(("Can join room", video.get("roomJoin") == True))
        checks.append(("Can publish", video.get("canPublish") == True))
        checks.append(("Can subscribe", video.get("canSubscribe") == True))
    
    all_passed = True
    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL CHECKS PASSED! Token is valid and ready to use.")
        print("=" * 70)
        print(f"\nTest this token:")
        print(f"URL: {os.getenv('LIVEKIT_URL')}")
        print(f"Room: {room_name}")
        print(f"Token: {jwt_token}")
    else:
        print("❌ SOME CHECKS FAILED!")
        print("=" * 70)
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()