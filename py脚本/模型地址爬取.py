import time
import json
import csv
import logging
# import threading # No longer needed for explicit locking by this script
# import concurrent.futures # No longer needed
# import os # No longer needed for os.cpu_count()
from typing import List, Dict, Optional, Any, Set

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as SeleniumOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- 通用配置 ---
BASE_API_URL = "https://makerworld.com/api/v1/search-service/select/design2"
API_PARAMS_BASE = {
    "orderBy": "likeCount",
    "entrance": "list",
    "limit": 100,
    "categories": "",
}
INITIAL_OFFSET = 0
MODEL_URL_PREFIX = "https://makerworld.com/zh/models/"
MAX_FETCH_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 5
POLITE_DELAY_SECONDS = 1.0
MAX_PAGES_PER_DCS_ITERATION = 100

# --- designCreateSince 迭代配置 ---
DCS_ITERATION_MAX_VALUE = 800  # 最大 designCreateSince 值
DCS_ITERATION_STEP = 30  # designCreateSince 的步长 (仅爬取30的倍数)

# --- 日志配置 ---
# %(threadName)s will show 'MainThread' now
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')

# --- Selenium 特定配置 ---
SELENIUM_OUTPUT_CSV_FILE = 'makerworld_all_unique_urls_selenium_dcs_sequential.csv'  # Updated output filename
SELENIUM_TIMEOUT_SECONDS = 25
SELENIUM_HEADLESS = True
SELENIUM_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# --- Periodic Writing Constant ---
WRITE_DATA_INTERVAL = 1000  # Write to CSV every 1000 new unique items


def setup_selenium_driver() -> webdriver.Chrome:
    logging.info("Setting up Chrome WebDriver...")
    options = SeleniumOptions()
    if SELENIUM_HEADLESS:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f'user-agent={SELENIUM_USER_AGENT}')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        if not SELENIUM_HEADLESS:
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })
        logging.info("WebDriver setup complete.")
        return driver
    except Exception as e:
        logging.error(f"WebDriver setup failed: {e}", exc_info=True)
        raise


def fetch_data_selenium(driver: webdriver.Chrome, offset: int, design_create_since: int) -> Optional[Dict[str, Any]]:
    current_params = API_PARAMS_BASE.copy()
    current_params["offset"] = offset
    current_params["designCreateSince"] = design_create_since

    query_string = "&".join([f"{k}={v}" for k, v in current_params.items()])
    url = f"{BASE_API_URL}?{query_string}"

    json_data_text = ""
    try:
        driver.get(url)
        wait = WebDriverWait(driver, SELENIUM_TIMEOUT_SECONDS)
        try:
            pre_tag = wait.until(EC.presence_of_element_located((By.TAG_NAME, "pre")))
            wait.until(lambda d: d.find_element(By.TAG_NAME, "pre").text.strip() != "")
            json_data_text = pre_tag.text
        except:  # Fallback if <pre> tag is not found or empty
            body_element = wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            json_data_text = body_element.text

        if not json_data_text or not json_data_text.strip():
            logging.warning(f"Empty content (dcs={design_create_since}, offset={offset}, url={url}).")
            return None
        json_data_text = json_data_text.strip()
        return json.loads(json_data_text)
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error (dcs={design_create_since}, offset={offset}, url={url}): {e}")
        logging.debug(f"Problematic JSON (first 500 chars): {json_data_text[:500]}")
        return None
    except Exception as e:
        logging.error(f"Selenium fetch error (dcs={design_create_since}, offset={offset}, url={url}): {e}",
                      exc_info=False)
        return None


def process_data_sequentially() -> Set[str]:
    all_unique_ids_main: Set[str] = set()
    num_ids_at_last_write = 0

    dcs_values_to_process = [i for i in range(0, DCS_ITERATION_MAX_VALUE + 1, DCS_ITERATION_STEP)]

    total_dcs_values_to_process = len(dcs_values_to_process)
    if total_dcs_values_to_process == 0:
        logging.warning(
            "No designCreateSince values to process based on current settings (DCS_ITERATION_MAX_VALUE, DCS_ITERATION_STEP). Exiting processing.")
        return set()

    logging.info(
        f"Starting sequential processing for {total_dcs_values_to_process} dcs values (0 to {DCS_ITERATION_MAX_VALUE}, step {DCS_ITERATION_STEP}).")
    logging.info(f"Specific dcs values to be processed: {dcs_values_to_process}")

    driver = None
    try:
        driver = setup_selenium_driver()  # Setup driver once for the whole sequential process

        for dcs_idx, dcs_value in enumerate(dcs_values_to_process):
            logging.info(f"--- Processing DCS value: {dcs_value} ({dcs_idx + 1}/{total_dcs_values_to_process}) ---")
            offset = INITIAL_OFFSET
            pages_fetched_for_this_dcs = 0

            while pages_fetched_for_this_dcs < MAX_PAGES_PER_DCS_ITERATION:
                data = None
                for attempt in range(MAX_FETCH_ATTEMPTS):
                    data = fetch_data_selenium(driver, offset, dcs_value)
                    if data:
                        break
                    logging.warning(
                        f"Attempt {attempt + 1}/{MAX_FETCH_ATTEMPTS} failed (dcs={dcs_value}, offset={offset}). Retrying in {RETRY_DELAY_SECONDS}s...")
                    time.sleep(RETRY_DELAY_SECONDS)

                if not data:
                    logging.error(
                        f"Failed to fetch data after {MAX_FETCH_ATTEMPTS} attempts (dcs={dcs_value}, offset={offset}). Skipping this offset for dcs={dcs_value}.")
                    # Depending on desired behavior, you might want to 'break' to stop processing this dcs_value
                    # or 'continue' the while loop to the next offset (though that's unlikely if fetch failed)
                    # For now, we'll break from paging for this dcs_value.
                    break

                items_list = data.get('list') or data.get('hits')

                if items_list is None:
                    logging.warning(
                        f"No 'list' or 'hits' array in data (dcs={dcs_value}, offset={offset}). Data: {str(data)[:200]}")
                    break  # Stop processing this dcs_value if data structure is unexpected

                if not items_list:
                    logging.info(
                        f"No more items found (dcs={dcs_value}, offset={offset}, page {pages_fetched_for_this_dcs + 1}). End of pages for this dcs.")
                    break  # Stop paging for this dcs_value

                new_ids_on_this_page = 0
                for item in items_list:
                    item_id_val = None
                    if isinstance(item, dict):
                        item_id_val = item.get('id') or item.get('objId') or item.get('designId')

                    if item_id_val is not None:
                        item_id_str = str(item_id_val)
                        if item_id_str not in all_unique_ids_main:
                            all_unique_ids_main.add(item_id_str)
                            new_ids_on_this_page += 1
                    else:
                        logging.debug(
                            f"Skipping item, no valid ID (dcs={dcs_value}, offset={offset}): {str(item)[:100]}")

                if new_ids_on_this_page > 0:
                    logging.info(
                        f"DCS {dcs_value}, Page {pages_fetched_for_this_dcs + 1}: Added {new_ids_on_this_page} new IDs. Total unique: {len(all_unique_ids_main)}")

                # Check for periodic writing after processing each page's items
                current_total_ids = len(all_unique_ids_main)
                if (
                        current_total_ids - num_ids_at_last_write) >= WRITE_DATA_INTERVAL and current_total_ids > num_ids_at_last_write:
                    logging.info(
                        f"Threshold ({WRITE_DATA_INTERVAL} new items) reached. Writing {current_total_ids} unique URLs to disk...")
                    urls_to_write = {f"{MODEL_URL_PREFIX}{id_}" for id_ in all_unique_ids_main}
                    write_urls_to_csv(urls_to_write, SELENIUM_OUTPUT_CSV_FILE)
                    num_ids_at_last_write = current_total_ids
                    logging.info(f"Periodic save complete. {num_ids_at_last_write} URLs written.")

                pages_fetched_for_this_dcs += 1
                if len(items_list) < API_PARAMS_BASE['limit']:
                    logging.info(
                        f"Fetched {len(items_list)} items, less than limit {API_PARAMS_BASE['limit']} (dcs={dcs_value}, offset={offset}, page {pages_fetched_for_this_dcs}). Assuming last page for this dcs.")
                    break  # Stop paging for this dcs_value

                offset += API_PARAMS_BASE['limit']
                time.sleep(POLITE_DELAY_SECONDS)

            logging.info(
                f"Finished processing pages for dcs={dcs_value}. Total unique IDs so far: {len(all_unique_ids_main)}")
            # Optional: Add a longer delay between processing different dcs_values if needed
            # time.sleep(LONGER_DELAY_BETWEEN_DCS_VALUES)

    except Exception as e:
        logging.critical(f"An error occurred during sequential data processing: {e}", exc_info=True)
    finally:
        if driver:
            logging.info("Quitting WebDriver.")
            driver.quit()

    logging.info(f"All specified DCS values processed. Total unique IDs collected: {len(all_unique_ids_main)}.")

    if len(all_unique_ids_main) > num_ids_at_last_write and len(all_unique_ids_main) > 0:
        logging.info(f"Performing final write of all collected URLs...")
        urls_to_write = {f"{MODEL_URL_PREFIX}{id_}" for id_ in all_unique_ids_main}
        write_urls_to_csv(urls_to_write, SELENIUM_OUTPUT_CSV_FILE)
        logging.info(f"Final save complete. {len(all_unique_ids_main)} URLs written to {SELENIUM_OUTPUT_CSV_FILE}.")
    elif not all_unique_ids_main and total_dcs_values_to_process > 0:
        logging.info(
            "No unique IDs collected despite processing. CSV file not (re)written unless during periodic saves.")
    elif total_dcs_values_to_process == 0:
        logging.info("No DCS values were set for processing. CSV file not written.")
    else:
        logging.info(
            "No new IDs since last periodic save, or no IDs collected. Final data (if any) should already be on disk from periodic saves.")

    all_unique_urls = {f"{MODEL_URL_PREFIX}{id_}" for id_ in all_unique_ids_main}
    return all_unique_urls


def write_urls_to_csv(urls: Set[str], filename: str) -> None:
    try:
        sorted_urls = sorted(list(urls))
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['URL'])
            for url_entry in sorted_urls:
                writer.writerow([url_entry])
    except IOError as e:
        logging.error(f"IOError writing CSV '{filename}': {e}")
    except Exception as e:
        logging.error(f"Unexpected error writing CSV '{filename}': {e}", exc_info=True)


def main_selenium_dcs_iteration_sequential():
    logging.info("----- Running Selenium Version (Sequential, Iterating designCreateSince by multiples) -----")
    start_time = time.time()
    try:
        unique_model_urls = process_data_sequentially()
        # Final write is handled within process_data_sequentially
        if not unique_model_urls and DCS_ITERATION_MAX_VALUE >= 0 and DCS_ITERATION_STEP > 0:
            logging.info("No URLs were collected based on the specified dcs criteria.")
        elif not (DCS_ITERATION_MAX_VALUE >= 0 and DCS_ITERATION_STEP > 0):
            logging.warning("DCS iteration settings might prevent any tasks from running (e.g. step=0 or max_value<0).")

    except Exception as e:
        logging.critical(f"Main execution error in sequential process: {e}", exc_info=True)
    finally:
        end_time = time.time()
        logging.info(f"Total execution time: {end_time - start_time:.2f} seconds.")
        logging.info("Script finished.")


if __name__ == "__main__":
    main_selenium_dcs_iteration_sequential()