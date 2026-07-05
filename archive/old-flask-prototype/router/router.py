from flask import Flask, Blueprint
from typing import Union

from controller.artist_controller import ArtistController
from controller.transcription import TranscriptionController
from controller.user_controller import UserController
from router.artist_router import ArtistRouter
from router.transcription_router import TranscriptionRouter
from router.user_router import UserRouter


class Router:
    def __init__(
        self,
        app: Flask,
        artist_controller: ArtistController,
        transcribe_controller: TranscriptionController,
        user_controller: UserController,
    ):
        self.app = app
        # Initialize all route handlers
        self.artist_router = ArtistRouter(app, artist_controller)
        self.transcription_router = TranscriptionRouter(app, transcribe_controller)
        self.user_router = UserRouter(app, user_controller)
