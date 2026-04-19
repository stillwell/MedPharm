# MedPharm ERP - Medical & Pharmaceutical Management System
# Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
# Author: Robert Andrew Stillwell
# Email: Andrew.Stillwell@enlightec.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
MedPharm ERP - Flask Web Application Factory
Patient portal for prescription viewing, bill pay, and record access.
"""

import logging
import os
from flask import Flask, redirect, url_for, session, g, render_template

from security import (
    load_security_config,
    require_production_secrets,
    apply_session_hardening,
    enforce_idle_timeout,
    generate_csrf_token,
)
from web.routes import portal_bp


def create_app(db_manager):
    app = Flask(__name__,
                template_folder=os.path.join(os.path.dirname(__file__), "templates"),
                static_folder=os.path.join(os.path.dirname(__file__), "static"))

    cfg = load_security_config()
    app.secret_key = cfg.flask_secret
    app.config["DB_MANAGER"] = db_manager
    app.config["SECURITY_CONFIG"] = cfg

    if cfg.is_production:
        errors = require_production_secrets(cfg)
        for err in errors:
            logging.getLogger("medpharm.security").error(err)

    apply_session_hardening(app, cfg)
    app.before_request(enforce_idle_timeout(cfg))

    @app.before_request
    def load_user():
        g.db_manager = app.config["DB_MANAGER"]
        g.security_config = app.config["SECURITY_CONFIG"]
        g.user_id = session.get("user_id")
        g.patient_id = session.get("patient_id")
        g.username = session.get("username")
        g.patient_name = session.get("patient_name")

    @app.context_processor
    def inject_globals():
        return {
            "current_year": 2026,
            "user_logged_in": "user_id" in session,
            "patient_name": session.get("patient_name", ""),
            "csrf_token": generate_csrf_token,
        }

    app.register_blueprint(portal_bp)

    @app.route("/")
    def index():
        if "user_id" in session:
            return redirect(url_for("portal.dashboard"))
        return redirect(url_for("portal.login"))

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app
