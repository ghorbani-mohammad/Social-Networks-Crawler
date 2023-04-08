from logging import Handler

from network.models import Log


class DBHandler(Handler):
    """This is an error handler that stores error into db

    Args:
        Handler (_type_): _description_
        object (_type_): _description_
    """

    def __init__(self):
        super().__init__()

    def emit(self, record):
        try:
            log = Log(level=record.levelname, message=self.format(record))
            log.save()
        except Exception:  # pylint: disable=broad-except
            pass
