from flask import request, jsonify
import jwt
import os


def setup_auth_middleware(app):
    @app.before_request
    def before_request_func():
        if request.path.startswith("/api/v1/sounds-right/auth/"):
            return None

        if "Authorization" not in request.headers:
            return jsonify({"error": "Unauthorized"}), 401

        try:
            jwt.decode(
                request.headers["Authorization"],
                os.getenv("JWT_SECRET"),
                algorithms=["HS256"],
            )
        except (jwt.InvalidTokenError, jwt.ExpiredSignatureError) as e:
            error_message = (
                "Token has expired"
                if isinstance(e, jwt.ExpiredSignatureError)
                else "Invalid token"
            )
            return jsonify({"error": error_message}), 401
