from flask import Flask

class BaseRouter:
    def __init__(self, app: Flask):
        self.app = app
        self.setup_routes()

    def setup_routes(self):
        """
        Abstract method that should be implemented by child classes
        to setup their specific routes
        """
        pass 