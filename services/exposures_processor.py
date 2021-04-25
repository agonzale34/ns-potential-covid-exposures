import logging

from models.exposure_location import load_exposure_data

NS_HEALTH_PAGE = "https://www.nshealth.ca/covid-exposures/"
EXPOSURES_FILEPATH = "0data/nova-scotia.json"


class ExposuresProcessor:

    @classmethod
    def process_ns_health_data(cls):
        logging.info("Running NS health processor")
        exposures = load_exposure_data(EXPOSURES_FILEPATH)
        logging.info(exposures)
