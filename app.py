from flask import Flask
from dotenv import load_dotenv
from container.container import Container
from container.config import get_config
from middleware.auth_middleware import setup_auth_middleware


load_dotenv(dotenv_path=".env")
app = Flask(__name__)
app.config["APPLICATION_ROOT"] = "/api/v1/sounds-right"


def create_app():
    # Create and configure the container
    container = Container()
    container.config.from_dict(get_config())

    # Initialize all dependencies
    container.database()  # Initialize database connection
    artist_controller = container.artist_controller()
    transcribe_controller = container.transcription_controller()
    auth_controller = container.auth_controller()

    # Setup authentication middleware
    setup_auth_middleware(app)

    # Initialize routers with injected controllers
    from router.router import Router
    from router.auth_router import AuthRouter

    Router(app, artist_controller, transcribe_controller)
    AuthRouter(app, auth_controller)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)
