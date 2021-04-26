import json
import logging
from typing import List, Optional

from utils.date_utils import current_datetime_string
from utils.objects_utils import obj_dict


KIND_PLACE = "Place"
KIND_FLIGHT = "Flight"
KIND_TRANSIT = "Halifax Transit"


class ExposureLocation:
    def __init__(
            self, kind: str, name: str, address: str, g_maps_address: str,
            date_begin: str, date_end: str, details: str,
            advice: str, zone: str, last_updated: str
    ):
        self.kind = kind
        self.name = name
        self.address = address
        self.g_maps_address = g_maps_address
        self.date_begin = date_begin
        self.date_end = date_end
        self.details = details
        self.advice = advice
        self.zone = zone
        self.last_updated = last_updated


class ExposureData:
    def __init__(self, province: str, timezone: str, last_updated: str, exposures: List[ExposureLocation]):
        self.province = province
        self.timezone = timezone
        self.last_updated = last_updated
        self.exposures = exposures

    def get_exposure(self, name: str, address: str, date_begin) -> Optional[ExposureLocation]:
        for exposure in self.exposures:
            if exposure.name == name and exposure.address == address and exposure.date_begin == date_begin:
                return exposure
        return None


def load_exposure_data(filename) -> ExposureData:
    try:
        with open(filename, encoding="utf-8") as file:
            json_object = json.load(file)
            exposure_data = ExposureData(**json_object)
            exposure_data.exposures = []
            for json_exposure in json_object['exposures']:
                exposure_data.exposures.append(ExposureLocation(**json_exposure))
            logging.info("Exposure file loaded successfully!")
            return exposure_data
    except FileNotFoundError:
        logging.info("Creating initial exposure file")
        exposure_data = ExposureData("Nova Scotia", "America/Halifax", current_datetime_string(), [])
        save_exposure_data(filename, exposure_data)
        return exposure_data


def save_exposure_data(filename, exposure_data: ExposureData):
    with open(filename, 'w', encoding="utf-8") as json_file:
        json.dump(exposure_data, json_file, default=obj_dict, indent=2, ensure_ascii=False)
