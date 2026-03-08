"""Flask application factory for frozen-hero."""

import logging
from datetime import datetime

from flask import Flask, abort, current_app, jsonify, render_template, request

from frozen_hero import config, db, label

logger = logging.getLogger(__name__)


def create_app(template_mode: bool = False) -> Flask:
    """Create and configure the Flask application."""
    db.init_db()

    app = Flask(
        __name__,
        template_folder=str(config.TEMPLATES_DIR),
        static_folder=str(config.STATIC_DIR),
    )
    app.config["TEMPLATE_MODE"] = template_mode
    if template_mode:
        logger.info("Template mode enabled — DB and printer will be skipped")

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
        lang = body.get("lang", "de")

        if not row1 or not date:
            abort(400)

        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            abort(400)

        if current_app.config["TEMPLATE_MODE"]:
            try:
                preview_path = label.generate_label(row1, row2, date, 0, lang=lang)
                logger.info("Template mode: label preview written to %s", preview_path)
            except Exception:
                logger.exception("Label preview generation failed")
                abort(500)
            return (
                jsonify(
                    {
                        "result": {
                            "id": 0,
                            "dec1": row1,
                            "dec2": row2,
                            "category": category,
                            "date": date,
                        }
                    }
                ),
                201,
            )

        try:
            entry_id = db.add_entry(row1, row2, category, date)
        except Exception:
            logger.exception("Failed to insert entry")
            abort(500)

        try:
            label_path = label.generate_label(row1, row2, date, entry_id, lang=lang)
            label.print_label(label_path)
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
