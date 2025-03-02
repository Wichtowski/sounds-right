from flask import Flask, request

from controller.user_controller import UserController
from router.base_router import BaseRouter


class UserRouter(BaseRouter):
    def __init__(self, app: Flask, user_controller: UserController):
        self.user_controller = user_controller
        super().__init__(app)

    def setup_routes(self):
        self.app.add_url_rule(
            "/user/role",
            "update_user_role",
            view_func=lambda: self.user_controller.update_user_role(request),
            methods=["PUT"],
        )

        self.app.add_url_rule(
            "/user/role/<user_id>",
            "get_user_role",
            view_func=lambda user_id: self.user_controller.get_user_role(user_id),
            methods=["GET"],
        )

        self.app.add_url_rule(
            "/user/roles",
            "get_all_roles",
            view_func=self.user_controller.get_all_roles,
            methods=["GET"],
        )
