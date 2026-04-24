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
MedPharm ERP - Cloud API Application Factory
Creates a Flask application configured for cloud deployment,
serving the REST API for Android and other mobile clients.
"""

import logging
import os
from flask import Flask, jsonify, g
from flask_cors import CORS

from security import (
    load_security_config,
    require_production_secrets,
    security_headers,
)
from api.routes import api_bp
from api.fhir import fhir_bp


def create_cloud_app(db_manager):
    app = Flask(__name__)

    cfg = load_security_config()
    app.secret_key = cfg.flask_secret
    app.config["DB_MANAGER"] = db_manager
    app.config["SECURITY_CONFIG"] = cfg
    app.config["JSON_SORT_KEYS"] = False

    if cfg.is_production:
        for err in require_production_secrets(cfg):
            logging.getLogger("medpharm.security").error(err)

    origins = cfg.cors_origins or os.environ.get("MEDPHARM_CORS_ORIGINS", "*")
    CORS(app, resources={
        r"/api/*": {
            "origins": origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Authorization", "Content-Type", "X-CSRF-Token"],
        },
        r"/fhir/*": {
            "origins": origins,
            "methods": ["GET", "OPTIONS"],
            "allow_headers": ["Authorization", "Accept"],
        },
    })

    @app.before_request
    def inject_db():
        g.db_manager = app.config["DB_MANAGER"]
        g.security_config = app.config["SECURITY_CONFIG"]

    @app.after_request
    def add_security_headers(resp):
        for k, v in security_headers(cfg).items():
            resp.headers.setdefault(k, v)
        return resp

    app.register_blueprint(api_bp)
    app.register_blueprint(fhir_bp)

    @app.route("/")
    def root():
        return jsonify({
            "service": "MedPharm ERP Cloud API",
            "version": "1.7.5",
            "copyright": "\u00a9 2026 Enlightec Ltd.",
            "api_base": "/api/v1",
            "fhir_base": "/fhir",
            "endpoints": {
                "health": "/api/v1/health",
                "patient_login": "/api/v1/auth/login/patient",
                "staff_login": "/api/v1/auth/login/staff",
                "register": "/api/v1/auth/register",
                "fhir_capability": "/fhir/metadata",
            }
        })

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app
