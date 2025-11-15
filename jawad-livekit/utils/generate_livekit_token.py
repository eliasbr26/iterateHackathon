"""
Utility script to generate LiveKit JWT tokens
"""

import os
import sys
from datetime import timedelta
from dotenv import load_dotenv

try:
    from livekit import api
except ImportError:
    print("Error: livekit-api not installed")
    print("Install it with: pip install livekit-api")
    sys.exit(1)


def generate_token(
    api_key: str,
    api_secret: str,
    room_name: str,
    participant_identity: str,
    participant_name: str = None,
    ttl_hours: int = 24,
    can_publish: bool = False,
    can_subscribe: bool = True,
    can_publish_data: bool = False
) -> str:
    """
    Generate a LiveKit JWT token

    Args:
        api_key: LiveKit API key
        api_secret: LiveKit API secret
        room_name: Name of the room
        participant_identity: Unique identity for participant
        participant_name: Display name (optional)
        ttl_hours: Token validity in hours (default: 24)
        can_publish: Can publish audio/video (default: False for bot)
        can_subscribe: Can subscribe to tracks (default: True)
        can_publish_data: Can publish data messages (default: False)

    Returns:
        JWT token string
    """
    token = api.AccessToken(api_key, api_secret)
    token.with_identity(participant_identity)

    if participant_name:
        token.with_name(participant_name)

    # Set token validity
    token.with_ttl(timedelta(hours=ttl_hours))

    # Set permissions
    grants = api.VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=can_publish,
        can_subscribe=can_subscribe,
        can_publish_data=can_publish_data
    )

    token.with_grants(grants)

    return token.to_jwt()


def main():
    """Main function for CLI usage"""
    load_dotenv()

    # Get configuration
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    room_name = os.getenv("LIVEKIT_ROOM", "interview-room")

    if not api_key or not api_secret:
        print("Error: LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set")
        print("Add them to your .env file:")
        print("  LIVEKIT_API_KEY=your_key")
        print("  LIVEKIT_API_SECRET=your_secret")
        sys.exit(1)

    print("LiveKit Token Generator")
    print("=" * 60)

    # Generate token for bot
    print("\n🤖 Generating token for transcription bot...")
    bot_token = generate_token(
        api_key=api_key,
        api_secret=api_secret,
        room_name=room_name,
        participant_identity="transcription-bot",
        participant_name="Transcription Bot",
        ttl_hours=24,
        can_publish=False,
        can_subscribe=True
    )

    print(f"\nRoom: {room_name}")
    print(f"Bot Token (valid for 24h):")
    print(f"{bot_token}\n")

    # Generate tokens for participants
    print("\n👔 Generating token for interviewer...")
    interviewer_token = generate_token(
        api_key=api_key,
        api_secret=api_secret,
        room_name=room_name,
        participant_identity="interviewer",
        participant_name="Interviewer",
        ttl_hours=2,
        can_publish=True,
        can_subscribe=True
    )

    print(f"Interviewer Token (valid for 2h):")
    print(f"{interviewer_token}\n")

    print("\n👤 Generating token for candidate...")
    candidate_token = generate_token(
        api_key=api_key,
        api_secret=api_secret,
        room_name=room_name,
        participant_identity="candidate",
        participant_name="Candidate",
        ttl_hours=2,
        can_publish=True,
        can_subscribe=True
    )

    print(f"Candidate Token (valid for 2h):")
    print(f"{candidate_token}\n")

    print("=" * 60)
    print("\n💡 Usage:")
    print(f"  1. Add bot token to .env file:")
    print(f"     LIVEKIT_TOKEN={bot_token}")
    print(f"\n  2. Share participant tokens with interviewer and candidate")
    print(f"\n  3. Run: python example_usage.py")


if __name__ == "__main__":
    main()
