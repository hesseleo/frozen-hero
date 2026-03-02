"""Flask application factory for frozen-hero."""

import logging
from datetime import datetime

from flask import Flask, abort, jsonify, render_template, request, send_from_directory

from frozen_hero import config, db, label

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Create and configure the Flask application."""
    db.init_db()

    app = Flask(
        __name__,
        template_folder=str(config.TEMPLATES_DIR),
        static_folder=str(config.STATIC_DIR),
    )

    # ------------------------------------------------------------------
    # Static assets
    # ------------------------------------------------------------------

    @app.route("/favicon.png")
    def favicon() -> object:
        return send_from_directory(config.STATIC_DIR, "favicon.png", mimetype="image/png")

    @app.route("/apple-touch-icon.png")
    def touchicon() -> object:
        return send_from_directory(config.STATIC_DIR, "apple-touch-icon.png", mimetype="image/png")

    # ------------------------------------------------------------------
    # Main UI
    # ------------------------------------------------------------------

    @app.route("/")
    def index() -> str:
        return render_template("index.html")

    # ------------------------------------------------------------------
    # API routes
    # ------------------------------------------------------------------

    @app.route("/getData", methods=["GET"])
    def get_data() -> object:
        try:
            entries = db.get_all_entries()
        except Exception:
            logger.exception("Failed to read database")
            abort(500)
        return jsonify(entries), 200

    @app.route("/add2freezer", methods=["POST"])
    def add_to_freezer() -> object:
        if not request.json:
            abort(400)

        body = request.json
        row1 = body.get("row1", "")
        row2 = body.get("row2", "")
        category = body.get("category", "")
        date = body.get("date", "")

        if not row1 or not date:
            abort(400)

        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            abort(400)

        try:
            entry_id = db.add_entry(row1, row2, category, date)
        except Exception:
            logger.exception("Failed to insert entry")
            abort(500)

        try:
            label.print_label(row1, row2, date, entry_id)
        except Exception:
            # Label printing is non-fatal — the item is already in the DB.
            logger.exception("Label printing failed for entry %d", entry_id)

        return (
            jsonify(
                {
                    "result": {
                        "id": entry_id,
                        "dec1": row1,
                        "dec2": row2,
                        "category": category,
                        "date": date,
                    }
                }
            ),
            201,
        )

    @app.route("/delEntry", methods=["POST"])
    def del_entry() -> object:
        if not request.json:
            abort(400)

        raw_id = request.json.get("id")
        try:
            entry_id = int(raw_id)
        except (TypeError, ValueError):
            abort(400)

        try:
            removed = db.delete_entry(entry_id)
        except Exception:
            logger.exception("Failed to delete entry %d", entry_id)
            abort(500)

        if not removed:
            abort(404)

        return jsonify(success=True), 200

    return app
