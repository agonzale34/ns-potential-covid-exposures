import logging

import tornado.ioloop
import tornado.web

from constants.app_constants import APP_TITLE
from controllers.main_handler import MainHandler
from services.tasks_scheduler import TasksScheduler

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.DEBUG)


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(9001)
    logging.info("{} up and running!".format(APP_TITLE))
    scheduler = TasksScheduler()
    scheduler.start_tasks_scheduler()
    tornado.ioloop.IOLoop.current().start()
