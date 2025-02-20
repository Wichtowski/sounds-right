from flask import Flask
from controller.artist import ArtistController
from controller.transcription import TranscriptionController
from router.artist_router import ArtistRouter
from router.transcription_router import TranscriptionRouter


class Router:
    def __init__(
        self,
        app: Flask,
        artist_controller: ArtistController,
        transcribe_controller: TranscriptionController,
    ):
        self.app = app
        # Initialize all route handlers
        self.artist_router = ArtistRouter(app, artist_controller)
        self.transcription_router = TranscriptionRouter(app, transcribe_controller)
