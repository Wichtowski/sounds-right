from flask import Flask, request, jsonify
import jwt
import os
import whisper
import json
from dotenv import load_dotenv
from database.connection import Database
from controller.artist import ArtistController
from controller.transcription import TranscriptionController
from formatter.api_response_formatter import ApiResponseFormatter
from transcriber.transcriber import Transcriber
from router.router import Router


load_dotenv(dotenv_path=".env")
app = Flask(__name__)
app.config["APPLICATION_ROOT"] = "/api/v1/sounds-right"


class App:
    def __init__(
        self, db, data_formatter, artist_controller, transcribe_controller, transcriber
    ):
        self.db = db
        self.data_formatter = data_formatter
        self.artist_controller = artist_controller
        self.transcribe_controller = transcribe_controller
        self.transcriber = transcriber
        self.app = app
        self.router = Router(app, artist_controller, transcribe_controller)


@app.before_request
def before_request_func():
    if "Authorization" not in request.headers:
        return jsonify({"error": "Unauthorized"}), 403
    if jwt.decode(
        request.headers["Authorization"], os.getenv("JWT_SECRET"), algorithms=["HS256"]
    )["secret"] != os.getenv("APP_SECRET"):
        return jsonify({"error": "Unauthorized"}), 403


if __name__ == "__main__":
    model = whisper.load_model("base")
    transcriber = Transcriber(model)

    db = Database()
    data_formatter = ApiResponseFormatter()

    artist_controller = ArtistController(db, data_formatter)
    transcribe_controller = TranscriptionController(db, data_formatter, transcriber)

    app_instance = App(
        db, data_formatter, artist_controller, transcribe_controller, transcriber
    )
    app_instance.app.run(debug=True, port=5001)
