from logging import Handler

from network.models import Log


class DBHandler(Handler, object):
    def __init__(self):
        super(DBHandler, self).__init__()

    def emit(self, record):
        try:
            log = Log(level=record.levelname, message=self.format(record))
            log.save()
        except:
            pass
