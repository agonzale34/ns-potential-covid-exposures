import json
import logging
from typing import List

from utils.date_utils import current_datetime_string
from utils.objects_utils import obj_dict


class ExposureLocation:
    def __init__(
            self, kind: str, name: str, address: str,
            date: str, begin: str, end: str, details: str,
            advice: str, zone: str, last_updated: str
    ):
        self.kind = kind
        self.name = name
        self.address = address
        self.date = date
        self.begin = begin
        self.end = end
        self.details = details
        self.advice = advice
        self.zone = zone
        self.last_updated = last_updated


class ExposuresDay:
    def __init__(self, date: str, locations: List[ExposureLocation]):
        self.date = date
        self.locations = locations


class ExposureData:
    def __init__(self, province: str, timezone: str, last_updated: str, exposures: List[ExposuresDay]):
        self.province = province
        self.timezone = timezone
        self.last_updated = last_updated
        self.exposures = exposures


def load_exposure_data(filename) -> ExposureData:
    try:
        with open(filename) as file:
            return ExposureData(**json.load(file))
    except FileNotFoundError:
        logging.info("Creating initial exposure file")
        exposure_data = ExposureData("Nova Scotia", "America/Halifax", current_datetime_string(), [])
        save_exposure_data(filename, exposure_data)
        return exposure_data


def save_exposure_data(filename, exposure_data: ExposureData):
    with open(filename, 'w') as json_file:
        json.dump(exposure_data, json_file, default=obj_dict, indent=2)
