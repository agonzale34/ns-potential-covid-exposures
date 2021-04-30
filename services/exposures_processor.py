import logging
import os
from typing import Optional

import pylev
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from models.exposure_location import load_exposure_data, KIND_FLIGHT, KIND_TRANSIT, KIND_PLACE, ExposureData, \
    ExposureLocation, save_exposure_data
from utils.date_utils import exposure_window_to_date_interval, normalize_datetime, current_datetime_string

LOGGER.setLevel(logging.ERROR)

TIMEOUT = 5
NS_HEALTH_URL = "https://www.nshealth.ca/covid-exposures/"
NS_HEALTH_READY = "Potential COVID Exposures"
EXPOSURES_FILEPATH = "0data/nova-scotia-history.json"
EXPOSURES_14DAYS_FILEPATH = "0data/nova-scotia-14Days.json"

G_MAPS_URL = "https://www.google.ca/maps/"
G_MAPS_READY = "Satellite"


class ExposuresProcessor:
    use_headless = True

    @classmethod
    def process_ns_health_data(cls):
        logging.info("Running NS health processor")
        exposures_data = load_exposure_data(EXPOSURES_FILEPATH)
        browser = cls.load_browser(NS_HEALTH_URL, NS_HEALTH_READY)

        has_next = cls.get_next_button(browser)

        while has_next is not None:
            logging.info("Processing new NS page")
            cls.process_current_page(exposures_data, browser)
            cls.click(browser, has_next.find_element_by_tag_name("a"))
            cls.wait_element_contains_text(browser, NS_HEALTH_READY)
            has_next = cls.get_next_button(browser)
            save_exposure_data(EXPOSURES_FILEPATH, exposures_data)

        # process last page
        cls.process_current_page(exposures_data, browser)

        exposures_data.last_updated = current_datetime_string()
        save_exposure_data(EXPOSURES_FILEPATH, exposures_data)
        browser.quit()

        # commit the change if the file has changes
        os.system("git add {}".format(EXPOSURES_FILEPATH))
        os.system('git commit -m "Updating the exposure file"')
        os.system("git push")
        logging.info("Records processed successfully!")

    @classmethod
    def get_next_button(cls, browser: WebDriver) -> Optional[WebElement]:
        try:
            return browser.find_element_by_class_name("pager__item--next")
        except NoSuchElementException:
            return None

    @classmethod
    def process_current_page(cls, exposures_data: ExposureData, browser: WebDriver):
        maps_browser = cls.load_browser(G_MAPS_URL, G_MAPS_READY)
        exposures_table = browser.find_element_by_class_name("view-content").find_element_by_tag_name("tbody")
        exposures_rows = exposures_table.find_elements_by_tag_name("tr")
        for exposure_row in exposures_rows:
            logging.info("processing exposure row")
            ex_row_data = exposure_row.find_elements_by_tag_name("td")
            ex_place = ex_row_data[0].text
            ex_windows = ex_row_data[1].text
            [ex_begin, ex_end] = exposure_window_to_date_interval(ex_windows)
            ex_address = ex_row_data[2].text
            ex_details = ex_row_data[3].find_element_by_tag_name("a").get_attribute("href")
            ex_advice = ex_row_data[4].text
            ex_zone = ex_row_data[5].text
            ex_last_updated = normalize_datetime(ex_row_data[6].text)

            # validate if exposure already exists
            previous_record = exposures_data.get_exposure(ex_place, ex_address, ex_begin)
            if previous_record is not None:
                if previous_record.last_updated != ex_last_updated:
                    previous_record.date_end = ex_end
                    previous_record.details = ex_details
                    previous_record.advice = ex_advice
                    previous_record.zone = ex_zone
                    previous_record.last_updated = ex_last_updated

            else:
                ex_g_address = ""
                if KIND_FLIGHT.lower() in ex_place.lower() or "air canada" in ex_place.lower():
                    ex_kind = KIND_FLIGHT
                elif KIND_TRANSIT.lower() in ex_place.lower():
                    ex_kind = KIND_TRANSIT
                else:
                    ex_kind = KIND_PLACE
                    # trying to get the google maps exact address for exposures PLACE kind
                    if ex_address != "":
                        ex_g_address = cls.find_g_address(maps_browser, ex_place, ex_address)

                new_exposure = ExposureLocation(
                    ex_kind, ex_place, ex_address, ex_g_address, ex_begin, ex_end,
                    ex_details, ex_advice, ex_zone, ex_last_updated
                )
                exposures_data.exposures.append(new_exposure)

        maps_browser.quit()

    @classmethod
    def find_g_address(cls, maps_browser: WebDriver, place, address) -> str:
        address_to_search = place + ", " + address
        search_form = maps_browser.find_element_by_tag_name("form")
        search_input = search_form.find_element_by_id("searchboxinput")
        search_input.send_keys(address_to_search)
        search_button = maps_browser.find_element_by_id("searchbox-searchbutton")
        cls.click(maps_browser, search_button)
        try:
            cls.wait_element_contains_text(maps_browser, "Suggest an edit")
            g_address = maps_browser.find_element_by_xpath("//button[@data-item-id='address']") \
                .get_attribute("aria-label").split(": ")[1]
        except:
            # identify partial match
            try:
                partial_result = maps_browser.find_element_by_xpath(
                    "//div[@aria-label='Results for {}']".format(address_to_search)
                )
                partial_options = partial_result.find_elements_by_class_name("place-result-container-place-link")
                if len(partial_options) == 0:
                    partial_options = partial_result.find_elements_by_xpath(
                        "//div[contains(@class, 'result-container-clickable')]"
                    )

                if len(partial_options) >= 1:
                    # check which option is the closer one
                    best_distance = 9999
                    best_option = None
                    for option in partial_options:
                        distance = pylev.levenshtein(place, option.get_attribute("aria-label"))
                        if distance < best_distance:
                            best_distance = distance
                            best_option = option

                    cls.click(maps_browser, best_option)
                    cls.wait_element_contains_text(maps_browser, "Suggest an edit")
                    g_address = maps_browser.find_element_by_xpath("//button[@data-item-id='address']") \
                        .get_attribute("aria-label").split(": ")[1]
                else:
                    g_address = ""
            except NoSuchElementException:
                g_address = ""
        clear_button = maps_browser.find_element_by_xpath("//a[@guidedhelpid='clear_search']")
        cls.click(maps_browser, clear_button)
        return g_address

    @classmethod
    def set_use_headless(cls, value: bool):
        cls.use_headless = value

    @classmethod
    def load_browser(cls, url: str, ready_value: str) -> WebDriver:
        if cls.use_headless:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            browser = webdriver.Chrome(options=chrome_options)
        else:
            browser = webdriver.Chrome()

        browser.get(url)
        cls.wait_element_contains_text(browser, ready_value)
        return browser

    @classmethod
    def click(cls, browser, element):
        browser.execute_script("arguments[0].click()", element)

    @classmethod
    def wait_element_by(cls, browser, by, value, timeout=TIMEOUT):
        return WebDriverWait(browser, timeout).until(ec.presence_of_element_located(
            (by, value)
        ))

    @classmethod
    def wait_element_contains_text(cls, browser, text, timeout=TIMEOUT):
        return cls.wait_element_by(browser, By.XPATH, "//*[contains(text(), '{}')]".format(text), timeout)
