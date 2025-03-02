from flask import request
import jwt
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from database.connection import Database
from database.model.user import User
from formatter.api_response_formatter import ApiResponseFormatter


class AuthController:
    def __init__(
        self,
        db: Database,
        res_formatter: ApiResponseFormatter,
        jwt_secret: str,
        token_expiry: int,
    ):
        self.db = db
        self.res_formatter = res_formatter
        self.jwt_secret = jwt_secret
        self.token_expiry = token_expiry

    def _generate_token(self, user: User) -> str:
        payload = {
            "user_id": str(user._id),
            "username": user.username,
            "is_admin": user.is_admin,
            "exp": datetime.now(ZoneInfo("UTC")) + timedelta(hours=self.token_expiry),
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def register(self):
        try:
            if not request.is_json:
                return (
                    self.res_formatter.with_errors("Request must be JSON")
                    .with_status(400)
                    .response()
                )

            data = request.json
            required_fields = ["username", "email", "password"]
            for field in required_fields:
                if field not in data:
                    return (
                        self.res_formatter.with_errors(f"Missing {field}")
                        .with_status(400)
                        .response()
                    )

            user_by_username = User.get_by_username(self.db, data["username"])
            if user_by_username is not None:
                return (
                    self.res_formatter.with_errors("Username already exists")
                    .with_status(400)
                    .response()
                )
            if User.get_by_email(self.db, data["email"]):
                return (
                    self.res_formatter.with_errors("Email already exists")
                    .with_status(400)
                    .response()
                )

            # Create new user
            user = User(
                db=self.db,
                username=data["username"],
                email=data["email"],
                password=data["password"],
            )
            user.save()

            # Generate token
            token = self._generate_token(user)

            return (
                self.res_formatter.with_data(
                    {
                        "token": token,
                        "user": user.to_dict(),
                    }
                )
                .with_message("User registered successfully")
                .with_status(201)
                .response()
            )

        except Exception as e:
            return self.res_formatter.with_exception(e).response()

    def login(self):
        try:
            if not request.is_json:
                return (
                    self.res_formatter.with_errors("Request must be JSON")
                    .with_status(400)
                    .response()
                )

            data = request.json
            if "username" not in data or "password" not in data:
                return (
                    self.res_formatter.with_errors("Missing username or password")
                    .with_status(400)
                    .response()
                )

            # Find user
            user = User.get_by_username(self.db, data["username"])
            if not user or not user.check_password(data["password"]):
                return (
                    self.res_formatter.with_errors("Invalid username or password")
                    .with_status(401)
                    .response()
                )

            if not user.is_active:
                return (
                    self.res_formatter.with_errors("Account is inactive")
                    .with_status(401)
                    .response()
                )

            # Generate token
            token = self._generate_token(user)

            return (
                self.res_formatter.with_data(
                    {
                        "token": token,
                        "user": user.to_dict(),
                    }
                )
                .with_message("Login successful")
                .response()
            )

        except Exception as e:
            return self.res_formatter.with_exception(e).response()

    def verify_token(self):
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return (
                    self.res_formatter.with_errors("No authorization header")
                    .with_status(401)
                    .response()
                )

            try:
                payload = jwt.decode(auth_header, self.jwt_secret, algorithms=["HS256"])
                user = User.get_by_username(self.db, payload["username"])
                if not user:
                    raise jwt.InvalidTokenError()

                return self.res_formatter.with_data(
                    {
                        "valid": True,
                        "user": user.to_dict(),
                    }
                ).response()

            except jwt.ExpiredSignatureError:
                return (
                    self.res_formatter.with_errors("Token has expired")
                    .with_status(401)
                    .response()
                )
            except jwt.InvalidTokenError:
                return (
                    self.res_formatter.with_errors("Invalid token")
                    .with_status(401)
                    .response()
                )

        except Exception as e:
            return self.res_formatter.with_exception(e).response()
