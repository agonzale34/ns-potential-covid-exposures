from typing import Optional, Awaitable

import tornado.web

from constants.app_constants import APP_TITLE


class MainHandler(tornado.web.RequestHandler):
    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    def get(self):
        self.write("{} is ready!".format(APP_TITLE))
