"""Simple API test without emoji."""

import sys

sys.path.insert(0, ".")

import urllib.request
import json


def test_health():
    print("Testing health endpoint...")
    try:
        response = urllib.request.urlopen("http://localhost:5000/health", timeout=5)
        data = json.loads(response.read().decode())
        print(f"  [OK] Health: {data}")
        return True
    except Exception as e:
        print(f"  [FAIL] Health check: {e}")
        return False


def test_history():
    print("\nTesting history endpoint...")
    try:
        response = urllib.request.urlopen(
            "http://localhost:5000/api/v1/history", timeout=5
        )
        data = json.loads(response.read().decode())
        print(f"  [OK] History returned {len(data.get('analyses', []))} items")
        return True
    except Exception as e:
        print(f"  [FAIL] History: {e}")
        return False


def main():
    print("=" * 50)
    print("ResumeAI API Quick Test")
    print("=" * 50)

    results = []
    results.append(test_health())
    results.append(test_history())

    print("\n" + "=" * 50)
    if all(results):
        print("SUCCESS: API is working!")
        print("\nFrontend should connect correctly.")
        print("Just make sure to upload a non-encrypted PDF.")
    else:
        print("Some tests failed - check if server is running")
    print("=" * 50)


if __name__ == "__main__":
    main()
