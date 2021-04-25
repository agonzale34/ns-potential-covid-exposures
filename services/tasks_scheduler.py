import logging

import schedule
from tornado import gen
from tornado.ioloop import PeriodicCallback

from services.exposures_processor import ExposuresProcessor


class TasksScheduler:
    callback = PeriodicCallback(schedule.run_pending, callback_time=10000)

    @classmethod
    @gen.coroutine
    def start_tasks_scheduler(cls):
        schedule.every().hour.do(ExposuresProcessor.process_ns_health_data)
        schedule.run_all()
        cls.callback.start()
        logging.info("Tasks Scheduler started")
