from dependency_injector import containers, providers
from google.cloud import storage
import whisper
from database.connection import Database
from repository.storage_repository import StorageRepository
from transcriber.transcriber import Transcriber
from formatter.api_response_formatter import ApiResponseFormatter
from controller.artist_controller import ArtistController
from controller.transcription import TranscriptionController
from controller.auth_controller import AuthController
from service.transcription_service import TranscriptionService
from controller.user_controller import UserController
from service.user_service import UserService


class Container(containers.DeclarativeContainer):
    """Dependency Injection Container.

    This container manages all application dependencies and their lifecycle.
    It follows a hierarchical structure where higher-level components
    (like controllers) depend on lower-level ones (like services and repositories).
    """

    # Configuration provider - loads settings from config.py
    config = providers.Configuration()

    # Core Services
    # These are fundamental services that other components depend on
    database = providers.Singleton(Database, mongo_uri=config.database.mongo_uri)
    storage_client = providers.Singleton(storage.Client)

    # Repositories
    # Data access layer - handles storage operations
    storage_repository = providers.Singleton(
        StorageRepository,
        storage_client=storage_client,
        review_bucket=config.storage.review_bucket,
        production_bucket=config.storage.production_bucket,
    )

    # Models and Core Components
    whisper_model = providers.Singleton(
        whisper.load_model, "base"
    )  # Speech recognition model
    transcriber = providers.Singleton(
        Transcriber, model=whisper_model
    )  # Audio transcription component

    # Formatters
    api_response_formatter = providers.Factory(ApiResponseFormatter)

    # Services
    transcription_service = providers.Singleton(
        TranscriptionService,
        db=database,
        storage_repository=storage_repository,
    )

    # Controllers
    artist_controller = providers.Singleton(
        ArtistController,
        db=database,
        res_formatter=api_response_formatter,
    )

    transcription_controller = providers.Singleton(
        TranscriptionController,
        db=database,
        transcription_service=transcription_service,
        res_formatter=api_response_formatter,
    )

    auth_controller = providers.Singleton(
        AuthController,
        db=database,
        res_formatter=api_response_formatter,
        jwt_secret=config.jwt.secret,
        token_expiry=config.jwt.expiry_hours,
    )

    # Add these new providers
    user_service = providers.Singleton(UserService, database=database)

    user_controller = providers.Singleton(UserController, user_service=user_service)
