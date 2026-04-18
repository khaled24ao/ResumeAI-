"""Simple test script to verify API works end-to-end."""

import sys

sys.path.insert(0, ".")

from io import BytesIO
from pypdf import PdfWriter, PageObject
import json
import requests


def create_test_pdf():
    """Create a simple PDF with text content."""
    from pypdf.generic import ArrayObject, FloatObject, NameObject, TextStringObject

    writer = PdfWriter()

    # Add a blank page
    page = writer.add_blank_page(width=612, height=792)

    # Add a simple text object using low-level API
    # This creates a basic PDF with some content
    content = b"BT /F1 12 Tf 50 700 Td (John Doe - Senior Software Engineer) Tj ET"

    # Add content stream
    page[NameObject("/Contents")] = ArrayObject([writer._io.from_bytes(content)])

    # Add font (simplified)
    page[NameObject("/Resources")] = {
        NameObject("/Font"): {
            NameObject("/F1"): {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        }
    }

    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def test_api():
    print("Creating test PDF...")
    pdf_bytes = create_test_pdf()
    print(f"PDF created: {len(pdf_bytes)} bytes")

    print("\nTesting API endpoint...")
    try:
        response = requests.post(
            "http://localhost:5000/api/v1/analyze",
            files={"file": ("test_resume.pdf", pdf_bytes, "application/pdf")},
            timeout=15,
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:300]}")

        if response.status_code == 200:
            data = response.json()
            if "result" in data:
                print("\n✅ API SUCCESS! Analysis received:")
                result = data["result"]
                print(f"   Score: {result.get('score', 'N/A')}/10")
                print(f"   Strengths: {len(result.get('strengths', []))} items")
                print(f"   Weaknesses: {len(result.get('weaknesses', []))} items")
                print(
                    f"   Keywords missing: {len(result.get('keywords_missing', []))} items"
                )
                return True
        else:
            print(f"\n❌ API returned error: {response.status_code}")
            return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_history_endpoint():
    print("\n" + "=" * 60)
    print("Testing history endpoint...")
    try:
        response = requests.get("http://localhost:5000/api/v1/history", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("ResumeAI API Test Suite")
    print("=" * 60)

    ok1 = test_api()
    ok2 = test_history_endpoint()

    print("\n" + "=" * 60)
    if ok1 and ok2:
        print("✅ ALL API TESTS PASSED!")
    else:
        print("⚠️  Some tests had issues - check above")
