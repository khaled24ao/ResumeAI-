import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from flask import Flask, render_template, jsonify, request, Response, g
from backend.routes.analyze import analyze_bp
from backend.routes.history import history_bp
from backend.utils.logger import get_logger
from backend.services.database import init_db
from backend.middleware.rate_limit import limiter
from backend.utils.metrics import track_requests, get_metrics_endpoint

logger = get_logger(__name__)


def create_app(config_object=None) -> Flask:
    """Application factory pattern."""
    app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))

    # Load configuration
    if config_object:
        app.config.from_object(config_object)
    else:
        env = os.getenv("FLASK_ENV", "production")
        if env == "development":
            app.config["DEBUG"] = True
            app.config["ENV"] = "development"
        else:
            app.config["DEBUG"] = False
            app.config["ENV"] = "production"

    # Configure rate limiter storage
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # In development, use memory storage (no Redis needed)
    # In production, try Redis first, fall back to memory if unavailable
    use_redis = False
    if app.config.get("ENV") != "development":
        try:
            import redis

            test_redis = redis.from_url(redis_url, socket_connect_timeout=2)
            test_redis.ping()
            test_redis.close()
            use_redis = True
            logger.info(f"Redis available at {redis_url}")
        except Exception as e:
            logger.warning(f"Redis not available ({e}), using in-memory storage")
    else:
        logger.info("Development mode: using in-memory rate limit storage")

    app.config["RATELIMIT_STORAGE_URL"] = redis_url if use_redis else "memory://"
    app.config["RATELIMIT_STRATEGY"] = "fixed-window"

    # Initialize rate limiter
    limiter.init_app(app)
    if app.config.get("ENV") == "development":
        limiter.default_limits = ["1000 per hour"]
    else:
        limiter.default_limits = ["100 per day", "20 per hour"]

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    # Register request tracking middleware
    track_requests(app)

    # Register blueprints
    app.register_blueprint(analyze_bp)
    app.register_blueprint(history_bp)

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        logger.warning(f"404 error: {request.path}")
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 error: {error}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(400)
    def bad_request(error):
        logger.warning(f"400 error: {error}")
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """Custom response for rate limit exceeded."""
        logger.warning(f"Rate limit exceeded: {request.remote_addr}")
        return jsonify(
            {
                "error": "Rate limit exceeded",
                "details": "Too many requests. Please try again later.",
            }
        ), 429

    # Routes
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/health")
    def health():
        return {"status": "ok"}

    @app.route("/ready")
    def readiness():
        """Kubernetes readiness probe endpoint."""
        return {"status": "ready"}

    @app.route("/metrics")
    def metrics():
        """Prometheus metrics endpoint."""
        return Response(get_metrics_endpoint(), mimetype="text/plain")

    @app.route("/rate-limit-status")
    def rate_limit_status():
        """Get current rate limit status."""
        from backend.middleware.rate_limit import get_rate_limit_info

        limits = get_rate_limit_info()
        return jsonify(limits)

    @app.route("/history")
    def history_redirect():
        """Redirect to API history endpoint."""
        from flask import redirect

        return redirect("/api/v1/history", code=301)

    @app.route("/history-view")
    def history_view():
        """Show history as HTML page."""
        from backend.services.database import get_db_context
        from backend.models import Analysis

        with get_db_context() as db:
            analyses = (
                db.query(Analysis).order_by(Analysis.created_at.desc()).limit(20).all()
            )
            history_data = []
            for a in analyses:
                history_data.append(
                    {
                        "id": a.id,
                        "filename": a.filename,
                        "score": a.score,
                        "created_at": a.created_at.strftime("%Y-%m-%d %H:%M")
                        if a.created_at
                        else "-",
                        "processing_time_ms": a.processing_time_ms,
                    }
                )

        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analysis History - ResumeAI</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f0f0f; color: #e0e0e0; padding: 2rem; }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { color: #00d4aa; margin-bottom: 2rem; }
        .back-link { color: #00d4aa; text-decoration: none; margin-bottom: 1rem; display: inline-block; }
        .table { width: 100%; border-collapse: collapse; }
        .table th, .table td { padding: 1rem; text-align: left; border-bottom: 1px solid #333; }
        .table th { color: #888; font-weight: 500; }
        .score { color: #00d4aa; font-weight: 600; }
        .empty { color: #666; text-align: center; padding: 2rem; }
        .date { color: #666; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← Back to Home</a>
        <h1>Analysis History</h1>
"""
        if not history_data:
            html += (
                '<p class="empty">No analyses yet. Upload a resume to get started!</p>'
            )
        else:
            html += """<table class="table">
                <thead>
                    <tr><th>ID</th><th>Filename</th><th>Score</th><th>Date</th><th>Time (ms)</th></tr>
                </thead>
                <tbody>
"""
            for a in history_data:
                html += f"""<tr>
                    <td>{a["id"]}</td>
                    <td>{a["filename"]}</td>
                    <td class="score">{a["score"]}/10</td>
                    <td class="date">{a["created_at"]}</td>
                    <td class="date">{a["processing_time_ms"] or "-"}</td>
                </tr>
"""
            html += """</tbody></table>"""

        html += """
    </div>
</body>
</html>"""
        return html

    logger.info(f"Application initialized in {app.config.get('ENV', 'unknown')} mode")
    return app


# Note: The app instance is created by the root app.py
# This module only exports create_app to avoid double initialization
