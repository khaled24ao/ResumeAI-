from io import BytesIO

from flask import Flask

app = Flask(__name__)
app.config["TESTING"] = True
with app.test_request_context(
    "/test",
    method="POST",
    data={"file": (BytesIO(b"x" * 100), "test.pdf", "application/pdf")},
    content_type="multipart/form-data",
):
    from flask import request

    f = request.files["file"]
    print("Content length:", f.content_length)
    print("Filename:", f.filename)
