"""
Complete token debugging script
Run: python app/debug_token.py
"""
import os
import jwt as pyjwt
from dotenv import load_dotenv
from livekit.api import AccessToken, VideoGrants

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

print("=" * 70)
print("LIVEKIT TOKEN DEBUGGER")
print("=" * 70)

print("\n1. ENVIRONMENT CHECK")
print("-" * 70)
print(f"URL: {LIVEKIT_URL}")
print(f"API Key: {LIVEKIT_API_KEY}")
print(f"API Secret: {LIVEKIT_API_SECRET[:20]}... (length: {len(LIVEKIT_API_SECRET)})")

# Test token generation
print("\n2. TOKEN GENERATION")
print("-" * 70)

room_name = "test-room-123"
identity = "test-caller-456"

try:
    token = AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    token.identity = identity
    token.name = "Test Caller"
    
    # Try setting video_grant
    token.video_grant = VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True
    )
    
    jwt_token = token.to_jwt()
    print(f"✓ Token generated successfully")
    print(f"  Length: {len(jwt_token)} characters")
    
    # Decode and inspect
    print("\n3. TOKEN CONTENTS")
    print("-" * 70)
    decoded = pyjwt.decode(jwt_token, options={"verify_signature": False})
    
    print("Full decoded token:")
    import json
    print(json.dumps(decoded, indent=2))
    
    # Check critical fields
    print("\n4. VALIDATION")
    print("-" * 70)
    
    issues = []
    
    # Check issuer (should match API key)
    if decoded.get('iss') != LIVEKIT_API_KEY:
        issues.append(f"❌ Issuer mismatch: {decoded.get('iss')} != {LIVEKIT_API_KEY}")
    else:
        print(f"✓ Issuer correct: {decoded.get('iss')}")
    
    # Check subject (identity)
    if decoded.get('sub') != identity:
        issues.append(f"❌ Subject mismatch: {decoded.get('sub')} != {identity}")
    else:
        print(f"✓ Subject (identity) correct: {decoded.get('sub')}")
    
    # Check video grants
    video = decoded.get('video', {})
    if not video:
        issues.append("❌ No video grants found in token!")
    else:
        print(f"✓ Video grants present")
        print(f"  - room: {video.get('room')}")
        print(f"  - roomJoin: {video.get('roomJoin')}")
        print(f"  - canPublish: {video.get('canPublish')}")
        print(f"  - canSubscribe: {video.get('canSubscribe')}")
        
        if video.get('room') != room_name:
            issues.append(f"❌ Room name mismatch: {video.get('room')} != {room_name}")
        
        if not video.get('roomJoin'):
            issues.append("❌ roomJoin permission not set!")
    
    # Check expiration
    exp = decoded.get('exp')
    nbf = decoded.get('nbf')
    import time
    current = int(time.time())
    
    if exp:
        print(f"✓ Expires: {exp} (in {exp - current} seconds)")
        if exp < current:
            issues.append("❌ Token already expired!")
    
    if nbf and nbf > current:
        issues.append(f"❌ Token not yet valid (nbf: {nbf}, current: {current})")
    
    print("\n5. SUMMARY")
    print("=" * 70)
    
    if issues:
        print("❌ ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("✅ TOKEN LOOKS VALID!")
        print("\nYou can test this token at:")
        print(f"  URL: {LIVEKIT_URL}")
        print(f"  Room: {room_name}")
        print(f"  Token: {jwt_token}")
        
        print("\n6. MANUAL TEST")
        print("-" * 70)
        print("Copy these values to test manually:")
        print(f"""
const url = "{LIVEKIT_URL}";
const token = "{jwt_token}";
const room = new LivekitClient.Room();
await room.connect(url, token);
        """)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()