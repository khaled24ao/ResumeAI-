"""Quick test script to verify app functionality."""

import os
import sys

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))


def test_imports():
    """Test that all modules import correctly."""
    print("Testing imports...")
    try:
        from backend.app import create_app

        print("✅ create_app import OK")
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

    try:
        from backend.models import Analysis, Base

        print("✅ Models import OK")
    except Exception as e:
        print(f"❌ Models error: {e}")
        return False

    try:
        from backend.services.pdf_service import extract_text

        print("✅ PDF service import OK")
    except Exception as e:
        print(f"❌ PDF service error: {e}")
        return False

    try:
        from backend.schemas.analysis import AnalysisResult

        print("✅ Schemas import OK")
    except Exception as e:
        print(f"❌ Schemas error: {e}")
        return False

    return True


def test_app_creation():
    """Test app factory creates app."""
    print("\nTesting app creation...")
    try:
        from backend.app import create_app

        app = create_app()
        print("✅ App created successfully")

        # Check routes
        routes = [
            r.rule for r in app.url_map.iter_rules() if not r.rule.startswith("/static")
        ]
        print(f"✅ Registered routes: {len(routes)}")
        for route in routes:
            print(f"   {route}")

        # Check if /history is there
        if "/history" in routes:
            print("✅ /history redirect route registered")
        else:
            print("❌ /history route missing")
            return False

        if "/api/v1/history" in routes:
            print("✅ /api/v1/history API route registered")
        else:
            print("❌ /api/v1/history route missing")
            return False

        return True
    except Exception as e:
        print(f"❌ App creation error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_database():
    """Test database initialization."""
    print("\nTesting database...")
    try:
        from backend.services.database import init_db, get_db_context
        from backend.models import Analysis

        # Initialize DB
        init_db()
        print("✅ Database initialized")

        # Test creating a record
        with get_db_context() as db:
            count = db.query(Analysis).count()
            print(f"✅ Database query OK (count: {count})")

        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("ResumeAI - Quick Verification Test")
    print("=" * 60)

    results = []

    # Test 1: Imports
    results.append(("Imports", test_imports()))

    # Test 2: App creation
    results.append(("App Creation", test_app_creation()))

    # Test 3: Database
    results.append(("Database", test_database()))

    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    all_passed = all(passed for _, passed in results)
    print("=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! App is ready.")
        print("\nNext steps:")
        print("1. Run: python app.py")
        print("2. Open: http://localhost:5000")
        print("3. Upload a NON-ENCRYPTED PDF")
        print("4. Check: http://localhost:5000/api/v1/history")
    else:
        print("⚠️  Some tests failed. Check errors above.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
