from dependency_injector import containers, providers
from google.cloud import storage
import whisper
from database.connection import Database
from repository.storage_repository import StorageRepository
from transcriber.transcriber import Transcriber
from formatter.api_response_formatter import ApiResponseFormatter
from controller.artist import ArtistController
from controller.transcription import TranscriptionController
from controller.auth_controller import AuthController
from service.transcription_service import TranscriptionService


class Container(containers.DeclarativeContainer):
    # Configuration
    config = providers.Configuration()

    # Core Services
    database = providers.Singleton(Database)

    storage_client = providers.Singleton(storage.Client)

    # Repositories
    storage_repository = providers.Singleton(
        StorageRepository,
        storage_client=storage_client,
        review_bucket=config.storage.review_bucket,
        production_bucket=config.storage.production_bucket,
    )

    # Models and Core Components
    whisper_model = providers.Singleton(whisper.load_model, "base")

    transcriber = providers.Singleton(Transcriber, model=whisper_model)

    # Formatters
    api_response_formatter = providers.Singleton(ApiResponseFormatter)

    # Services
    transcription_service = providers.Singleton(
        TranscriptionService, db=database, storage_repository=storage_repository
    )

    # Controllers
    artist_controller = providers.Singleton(
        ArtistController, db=database, res_formatter=api_response_formatter
    )

    transcription_controller = providers.Singleton(
        TranscriptionController,
        db=database,
        transcription_service=transcription_service,
        res_formatter=api_response_formatter,
    )

    auth_controller = providers.Singleton(
        AuthController, db=database, res_formatter=api_response_formatter
    )
