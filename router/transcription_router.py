from flask import Flask, request

from controller.transcription import TranscriptionController
from router.base_router import BaseRouter


class TranscriptionRouter(BaseRouter):
    def __init__(self, app: Flask, transcribe_controller: TranscriptionController):
        self.transcribe_controller = transcribe_controller
        super().__init__(app)

    def setup_routes(self):
        self.app.add_url_rule(
            "/transcription",
            "transcribe",
            view_func=lambda: self.transcribe_controller.validate_transcription_data(
                request
            ),
            methods=["POST"],
        )

        self.app.add_url_rule(
            "/transcription/<job_id>",
            "get_transcription_status",
            view_func=lambda job_id: self.transcribe_controller.get_transcription_status(
                job_id
            ),
            methods=["GET"],
        )
        self.app.add_url_rule(
            "/transcription/approve/<job_id>",
            "approve_transcription",
            view_func=lambda job_id: self.transcribe_controller.approve_transcription(
                job_id
            ),
            methods=["POST"],
        )
