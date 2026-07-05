from sounds_right_api.models import User

from .errors import ForbiddenPublishActionError


def ensure_admin(user: User) -> None:
    if user.role != "admin":
        raise ForbiddenPublishActionError
