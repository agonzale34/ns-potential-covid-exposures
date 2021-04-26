import datetime

from constants.app_constants import DATETIME_FORMAT, NS_DATETIME_FORMAT


def datetime_to_string(date) -> str:
    return date.strftime(DATETIME_FORMAT)


def current_datetime_string() -> str:
    return datetime_to_string(datetime.datetime.now())


def normalize_datetime(date: str) -> str:
    return datetime_to_string(datetime.datetime.strptime(date, NS_DATETIME_FORMAT))


def exposure_window_to_date_interval(window: str) -> [str, str]:
    [begin, end] = window.split(" to ")
    begin_str = begin.split(", ")[1]
    date_begin = datetime.datetime.strptime(begin_str, NS_DATETIME_FORMAT)

    if "-" in end:
        end_str = end.split(", ")[1]
    else:
        end_str = begin_str.split(" - ")[0] + " - " + end

    date_end = datetime.datetime.strptime(end_str, NS_DATETIME_FORMAT)

    return [datetime_to_string(date_begin), datetime_to_string(date_end)]
