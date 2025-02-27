from flask import Flask

from controller.auth_controller import AuthController
from router.base_router import BaseRouter


class AuthRouter(BaseRouter):
    def __init__(self, app: Flask, auth_controller: AuthController):
        self.auth_controller = auth_controller
        super().__init__(app)

    def setup_routes(self):
        self.app.add_url_rule(
            "/auth/register",
            "register",
            view_func=self.auth_controller.register,
            methods=["POST"],
        )

        self.app.add_url_rule(
            "/auth/login",
            "login",
            view_func=self.auth_controller.login,
            methods=["POST"],
        )

        self.app.add_url_rule(
            "/auth/verify",
            "verify_token",
            view_func=self.auth_controller.verify_token,
            methods=["GET"],
        )
