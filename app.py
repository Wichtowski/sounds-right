from dotenv import load_dotenv
from flask import Blueprint, Flask

from container.config import get_config
from container.container import Container
from middleware.auth_middleware import setup_auth_middleware

load_dotenv(dotenv_path=".env")
app = Flask(__name__)

# Create Blueprint for API v1
api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")


def create_app():
    # Create and configure the container
    container = Container()
    container.config.from_dict(get_config())

    # Initialize all dependencies
    container.database()  # Initialize database connection
    artist_controller = container.artist_controller()
    transcribe_controller = container.transcription_controller()
    auth_controller = container.auth_controller()
    user_controller = container.user_controller()

    # Setup authentication middleware
    setup_auth_middleware(api_v1)

    # Initialize routers with injected controllers
    from router.auth_router import AuthRouter
    from router.router import Router

    # Create router instances with the blueprint
    Router(api_v1, artist_controller, transcribe_controller, user_controller)
    AuthRouter(api_v1, auth_controller)

    # Register the blueprint with the app
    app.register_blueprint(api_v1)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)
