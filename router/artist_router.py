from flask import Flask, request
from controller.artist import ArtistController
from router.base_router import BaseRouter

class ArtistRouter(BaseRouter):
    def __init__(self, app: Flask, artist_controller: ArtistController):
        self.artist_controller = artist_controller
        super().__init__(app)

    def setup_routes(self):
        self.app.add_url_rule(
            "/artist",
            "create_artist",
            view_func=lambda: self.artist_controller.create_artist(request),
            methods=["POST"]
        )

        self.app.add_url_rule(
            "/artist",
            "get_all_artists",
            view_func=self.artist_controller.get_all_artists,
            methods=["GET"]
        )

        self.app.add_url_rule(
            "/artist/<pseudonym>",
            "get_artist",
            view_func=lambda pseudonym: self.artist_controller.get_artist(pseudonym),
            methods=["GET"]
        )

        self.app.add_url_rule(
            "/artist/<pseudonym>",
            "update_artist",
            view_func=lambda pseudonym: self.artist_controller.update_artist(pseudonym, request),
            methods=["PUT"]
        )

        self.app.add_url_rule(
            "/artist/<pseudonym>",
            "delete_artist",
            view_func=lambda pseudonym: self.artist_controller.delete_artist(pseudonym),
            methods=["DELETE"]
        )

        self.app.add_url_rule(
            "/artist/all",
            "force_delete_all_artists",
            view_func=self.artist_controller.force_delete_all_artists,
            methods=["DELETE"]
        ) 