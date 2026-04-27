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


from backend.config import flask_config, rate_limit_config, db_config, monitoring_config

def create_app(config_object=None) -> Flask:
    """Application factory pattern."""
    app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))

    # Load configuration
    if config_object:
        app.config.from_object(config_object)
    else:
        app.config["DEBUG"] = flask_config.debug
        app.config["ENV"] = flask_config.env
        app.config["TESTING"] = flask_config.testing
        app.config["SECRET_KEY"] = flask_config.secret_key


    # Configure rate limiter storage
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # In development, use memory storage (no Redis needed)
    # In production, try Redis first, fall back to memory if unavailable
    use_redis = False
    if app.config.get("ENV") != "development" and not app.config.get("TESTING"):
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
        logger.info(f"Using { 'TESTING' if app.config.get('TESTING') else 'development' } mode: using in-memory rate limit storage")

    app.config["RATELIMIT_STORAGE_URL"] = redis_url if use_redis else "memory://"
    app.config["RATELIMIT_STRATEGY"] = rate_limit_config.strategy

    # Initialize rate limiter
    limiter.init_app(app)
    if app.config.get("ENV") == "development":
        limiter.default_limits = [rate_limit_config.dev_limit]
    else:
        limiter.default_limits = [
            f"{rate_limit_config.default_per_day} per day",
            f"{rate_limit_config.default_per_hour} per hour"
        ]

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
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #00f2fe;
            --secondary: #4facfe;
            --accent: #00d4aa;
            --bg: #050505;
            --card-bg: rgba(255, 255, 255, 0.03);
            --card-border: rgba(255, 255, 255, 0.1);
            --text: #e0e0e0;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Outfit', sans-serif; background: var(--bg); color: var(--text); padding: 4rem 2rem; }
        .container { max-width: 1000px; margin: 0 auto; }
        h1 { font-size: 2.5rem; font-weight: 700; background: linear-gradient(to right, var(--primary), var(--secondary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 3rem; }
        .back-link { color: #888; text-decoration: none; margin-bottom: 2rem; display: inline-block; transition: color 0.3s; }
        .back-link:hover { color: var(--primary); }
        .table-container { background: var(--card-bg); backdrop-filter: blur(20px); border: 1px solid var(--card-border); border-radius: 24px; overflow: hidden; }
        .table { width: 100%; border-collapse: collapse; }
        .table th, .table td { padding: 1.5rem; text-align: left; border-bottom: 1px solid var(--card-border); }
        .table th { color: #888; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
        .score { color: var(--accent); font-weight: 600; font-size: 1.1rem; }
        .empty { color: #666; text-align: center; padding: 4rem; font-weight: 300; }
        .date { color: #666; font-size: 0.9rem; }
        tr:hover { background: rgba(255, 255, 255, 0.02); }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← Back to Analyzer</a>
        <h1>Analysis History</h1>
        <div class="table-container">
"""
        if not history_data:
            html += (
                '<p class="empty">No analyses yet. Upload a resume to get started!</p>'
            )
        else:
            html += """<table class="table">
                <thead>
                    <tr><th>ID</th><th>Filename</th><th>Score</th><th>Date</th><th>Time</th></tr>
                </thead>
                <tbody>
"""
            for a in history_data:
                html += f"""<tr>
                    <td>#{a["id"]}</td>
                    <td style="font-weight: 500;">{a["filename"]}</td>
                    <td class="score">{a["score"]}/10</td>
                    <td class="date">{a["created_at"]}</td>
                    <td class="date">{a["processing_time_ms"]}ms</td>
                </tr>
"""
            html += """</tbody></table>"""

        html += """
        </div>
    </div>
</body>
</html>"""

        return html

    logger.info(f"Application initialized in {app.config.get('ENV', 'unknown')} mode")
    return app


# Note: The app instance is created by the root app.py
# This module only exports create_app to avoid double initialization
