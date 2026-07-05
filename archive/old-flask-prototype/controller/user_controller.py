from flask import Request, jsonify


class UserController:
    def __init__(self, user_service):
        self.user_service = user_service

    def update_user_role(self, request: Request):
        # Implementation will go here
        pass

    def get_user_role(self, user_id: str):
        # Implementation will go here
        pass

    def get_all_roles(self):
        # Implementation will go here
        pass
