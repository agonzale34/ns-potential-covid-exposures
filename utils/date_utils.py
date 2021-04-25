import datetime

from constants.app_constants import DATETIME_FORMAT


def current_datetime_string() -> str:
    return datetime.datetime.now().strftime(DATETIME_FORMAT)
