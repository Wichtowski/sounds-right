from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from sounds_right_api.models import domain as _domain_models  # noqa: E402, F401
