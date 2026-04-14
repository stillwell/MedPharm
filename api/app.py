# MedPharm ERP - Medical & Pharmaceutical Management System
# Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
# Author: Robert Andrew Stillwell
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

import os
import secrets
from flask import Flask, jsonify, g
from flask_cors import CORS

from api.routes import api_bp


def create_cloud_app(db_manager):
    app = Flask(__name__)

    app.secret_key = os.environ.get("MEDPHARM_SECRET_KEY", secrets.token_hex(32))
    app.config["DB_MANAGER"] = db_manager
    app.config["JSON_SORT_KEYS"] = False

    # Enable CORS for mobile clients
    CORS(app, resources={
        r"/api/*": {
            "origins": os.environ.get("MEDPHARM_CORS_ORIGINS", "*"),
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Authorization", "Content-Type"],
        }
    })

    @app.before_request
    def inject_db():
        g.db_manager = app.config["DB_MANAGER"]

    app.register_blueprint(api_bp)

    @app.route("/")
    def root():
        return jsonify({
            "service": "MedPharm ERP Cloud API",
            "version": "1.1.0",
            "api_base": "/api/v1",
            "endpoints": {
                "health": "/api/v1/health",
                "patient_login": "/api/v1/auth/login/patient",
                "staff_login": "/api/v1/auth/login/staff",
                "register": "/api/v1/auth/register",
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
