class PublicationNotFoundError(Exception):
    pass


class PublicationAlreadyExistsError(Exception):
    pass


class VersionNotFoundError(Exception):
    pass


class VersionNotApprovedError(Exception):
    pass


class VersionNotPublishedError(Exception):
    pass


class PublicArtifactMissingError(Exception):
    pass


class PublicArtifactStorageError(Exception):
    pass


class ForbiddenPublishActionError(Exception):
    pass
