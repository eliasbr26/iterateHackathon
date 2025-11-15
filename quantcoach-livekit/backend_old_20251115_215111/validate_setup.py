#!/usr/bin/env python3
"""
Installation and configuration validation script
"""

import sys
import os
from pathlib import Path


def print_header(text: str):
    """Print a section header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)


def print_check(name: str, status: bool, message: str = ""):
    """Print a check result"""
    icon = "✓" if status else "✗"
    status_text = "OK" if status else "FAIL"
    print(f"{icon} {name}: {status_text}")
    if message:
        print(f"  → {message}")


def check_python_version():
    """Check Python version >= 3.10"""
    version = sys.version_info
    is_ok = version >= (3, 10)
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    print_check(
        "Python version",
        is_ok,
        f"Version {version_str} {'✓' if is_ok else '(required >= 3.10)'}"
    )
    return is_ok


def check_dependencies():
    """Check if required packages are installed"""
    required = [
        "livekit",
        "websockets",
        "numpy",
        "dotenv",
        "aiohttp"
    ]

    all_ok = True
    for package in required:
        try:
            if package == "dotenv":
                __import__("dotenv")
            else:
                __import__(package)
            print_check(f"Package '{package}'", True)
        except ImportError:
            print_check(f"Package '{package}'", False, "Not installed")
            all_ok = False

    return all_ok


def check_audio_pipeline():
    """Check if audio_pipeline module can be imported"""
    try:
        from audio_pipeline import AudioPipeline, Transcript
        print_check("audio_pipeline module", True)
        return True
    except ImportError as e:
        print_check("audio_pipeline module", False, str(e))
        return False


def check_env_file():
    """Check if .env file exists and has required variables"""
    env_path = Path(".env")

    if not env_path.exists():
        print_check(".env file", False, "File not found. Copy .env.example to .env")
        return False

    print_check(".env file", True, "File exists")

    # Check required variables
    required_vars = [
        "LIVEKIT_URL",
        "LIVEKIT_ROOM",
        "LIVEKIT_TOKEN",
        "ELEVENLABS_API_KEY"
    ]

    from dotenv import load_dotenv
    load_dotenv()

    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask the value for security
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print_check(f"  {var}", True, masked)
        else:
            print_check(f"  {var}", False, "Not set")
            all_set = False

    return all_set


def check_project_structure():
    """Check if all required files exist"""
    required_files = [
        "audio_pipeline/__init__.py",
        "audio_pipeline/pipeline.py",
        "audio_pipeline/models.py",
        "audio_pipeline/livekit_handler.py",
        "audio_pipeline/elevenlabs_stt.py",
        "audio_pipeline/audio_converter.py",
        "requirements.txt",
        "example_usage.py"
    ]

    all_ok = True
    for filepath in required_files:
        exists = Path(filepath).exists()
        if not exists:
            print_check(f"File '{filepath}'", False, "Missing")
            all_ok = False

    if all_ok:
        print_check("Project structure", True, "All files present")

    return all_ok


def check_livekit_api_keys():
    """Check if LiveKit API keys are set (for token generation)"""
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if api_key and api_secret:
        print_check(
            "LiveKit API credentials",
            True,
            "Set (for token generation)"
        )
        return True
    else:
        print_check(
            "LiveKit API credentials",
            False,
            "Not set (optional - needed only for token generation)"
        )
        return False


def run_basic_imports():
    """Try to import all modules"""
    try:
        from audio_pipeline import (
            AudioPipeline,
            Transcript,
            AudioConverter,
            setup_logging
        )
        print_check("Module imports", True, "All imports successful")
        return True
    except Exception as e:
        print_check("Module imports", False, str(e))
        return False


def print_summary(checks: dict):
    """Print validation summary"""
    print_header("VALIDATION SUMMARY")

    total = len(checks)
    passed = sum(1 for v in checks.values() if v)
    failed = total - passed

    print(f"\nTotal checks: {total}")
    print(f"✓ Passed: {passed}")
    print(f"✗ Failed: {failed}")

    if failed == 0:
        print("\n🎉 All checks passed! You're ready to go!")
        print("\nNext steps:")
        print("  1. Run: python example_usage.py")
        print("  2. Or see: docs/QUICKSTART.md")
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  • Install dependencies: pip install -r requirements.txt")
        print("  • Create .env file: cp .env.example .env")
        print("  • Configure .env with your credentials")

    return failed == 0


def main():
    """Main validation function"""
    print_header("AUDIO PIPELINE - VALIDATION")
    print("Checking installation and configuration...\n")

    checks = {}

    print_header("1. Python Environment")
    checks["python_version"] = check_python_version()

    print_header("2. Dependencies")
    checks["dependencies"] = check_dependencies()

    print_header("3. Project Structure")
    checks["project_structure"] = check_project_structure()

    print_header("4. Module Imports")
    checks["audio_pipeline"] = check_audio_pipeline()
    checks["imports"] = run_basic_imports()

    print_header("5. Configuration")
    checks["env_file"] = check_env_file()
    checks["livekit_api"] = check_livekit_api_keys()  # Optional

    # Summary
    success = print_summary(checks)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
