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
        schedule.every(6).hours.do(ExposuresProcessor.process_ns_health_data)
        cls.callback.start()
        logging.info("Tasks Scheduler started")
        schedule.run_all()
