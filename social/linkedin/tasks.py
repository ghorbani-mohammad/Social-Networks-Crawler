import time
import sys
import pickle
import traceback
import redis
from typing import Tuple, Optional

from django.conf import settings
from django.utils import timezone
from django.utils.html import strip_tags
from celery import shared_task
from celery.utils.log import get_task_logger
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from urllib3.exceptions import MaxRetryError
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    SessionNotCreatedException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from linkedin import models as lin_models
from reusable.models import get_network_model
from reusable.other import only_one_concurrency
from reusable.browser import scroll
from notification import tasks as not_tasks
from notification.utils import telegram_text_purify

logger = get_task_logger(__name__)
MINUTE = 60
TASKS_TIMEOUT = 1 * MINUTE
DUPLICATE_CHECKER = redis.StrictRedis(host="social_redis", port=6379, db=5)
LINKEDIN_URL = "https://www.linkedin.com/"


def get_config():
    config_model = get_network_model("Config")
    config = config_model.objects.last()
    if config is None:
        config = config_model(crawl_linkedin_feed=False)
    return config


def get_driver():
    """This function creates a browser driver and returns it

    Returns:
        Webdriver: webdriver browser
    """
    try:
        return webdriver.Remote(
            "http://social_firefox:4444/wd/hub",
            DesiredCapabilities.FIREFOX,
            options=webdriver.FirefoxOptions(),
        )
    except SessionNotCreatedException as error:
        logger.info("Error: %s\n\n%s", error, traceback.format_exc())
    except MaxRetryError as error:
        logger.info("Error: %s\n\n%s", error, traceback.format_exc())
    # Should do appropriate action instead of exit (for example restarting docker)
    sys.exit()


def initialize_linkedin_driver():
    """This function head the browser to the LinkedIn website.

    Returns:
        Webdriver: webdriver browser
    """
    driver = get_driver()

    cookies = None
    with open("/app/social/linkedin_cookies.pkl", "rb") as linkedin_cookie:
        cookies = pickle.load(linkedin_cookie)

    driver.get(LINKEDIN_URL)
    for cookie in cookies:
        driver.add_cookie(cookie)
    return driver


def driver_exit(driver):
    """This function properly exit a web driver.
    It ensures that we wait for some seconds before exiting the browser.

    Args:
        driver (Webdriver): webdriver browser
    """
    time.sleep(2)
    driver.quit()


@shared_task
def login():
    """This function login into LinkedIn and store credential info into /app/social/cookies.pkl .
    It read username and password from environment variables as follow:
    LINKEDIN_EMAIL -> username
    LINKEDIN_PASSWORD -> password
    """
    driver = get_driver()
    driver.get(f"{LINKEDIN_URL}login")
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        email_elem = driver.find_element("id", "username")
        email_elem.send_keys(settings.LINKEDIN_EMAIL)
        password_elem = driver.find_element("id", "password")
        password_elem.send_keys(settings.LINKEDIN_PASSWORD)
        password_elem.submit()
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "global-nav-search"))
        )

        with open("/app/social/linkedin_cookies.pkl", "wb") as linkedin_cookie:
            pickle.dump(driver.get_cookies(), linkedin_cookie)

    except NoSuchElementException:
        logger.error(traceback.format_exc())
    finally:
        driver_exit(driver)


@shared_task
def store_posts(channel_id, post_id, body, meta_data):
    """This function store a post into database. It will create or update a post.
    If a post with post-id exists, It will update it. Otherwise it will create a new post.

    Args:
        channel_id (int): id of channel
        post_id (int): id of post
        body (str): body of the post
        reaction_count (int): reactions count
        comment_count (int): comments count
        share_count (int): shares count
    """
    post_model = get_network_model("Post")
    exists = post_model.objects.filter(
        network_id=post_id, channel_id=channel_id
    ).exists()
    share_count = meta_data.get("share_count", 0)
    comment_count = meta_data.get("comment_count", 0)
    reaction_count = meta_data.get("reaction_count", 0)
    if not exists:
        post_model.objects.create(
            channel_id=channel_id,
            network_id=post_id,
            body=body,
            data=meta_data,
            share_count=share_count,
            views_count=reaction_count + comment_count + share_count,
        )
    else:
        post = post_model.objects.get(network_id=post_id)
        post.share_count = share_count
        post.views_count = reaction_count + comment_count + share_count
        post.data = meta_data
        post.save()


def get_post_statistics(reaction_element):
    statistics = {
        "reaction_count": 0,
        "comment_count": 0,
        "share_counter": 0,
    }
    socials = reaction_element.find_elements(By.XPATH, ".//li")
    for social in socials:
        temp = social.get_attribute("aria-label")
        if not temp:
            temp = social.find_elements(By.XPATH, ".//button")
            temp = temp[0].get_attribute("aria-label")
        temp = temp.split()[:2]
        value, elem = int(temp[0].replace(",", "")), temp[1]
        if elem == "reactions":
            statistics["reaction_count"] = value
        elif elem == "comments":
            statistics["comment_count"] = value
        elif elem == "shares":
            statistics["share_count"] = value
    return statistics


@shared_task(name="get_linkedin_posts")
@only_one_concurrency(key="browser1", timeout=TASKS_TIMEOUT)
def get_linkedin_posts(channel_id):
    channel_model = get_network_model("Channel")
    channel = channel_model.objects.get(pk=channel_id)
    channel_url = channel.username
    driver = initialize_linkedin_driver()
    driver.get(channel_url)
    scroll(driver, 1)
    time.sleep(5)
    try:
        articles = driver.find_elements(By.CLASS_NAME, "feed-shared-update-v2")
        for article in articles:
            try:
                post_id = article.get_attribute("data-urn")
                body = article.find_element(By.CLASS_NAME, "break-words").text
                reaction = article.find_elements(
                    By.XPATH,
                    './/ul[contains(@class, "social-details-social-counts")]',
                )[0]
                statistics = get_post_statistics(reaction)
                store_posts.delay(channel_id, post_id, body, statistics)
            except NoSuchElementException:
                logger.error(traceback.format_exc())
    except NoSuchElementException:
        logger.error(traceback.format_exc())
    finally:
        driver_exit(driver)
        channel.last_crawl = timezone.localtime()
        channel.save()


def sort_by_recent(driver):
    sort = driver.find_element(
        "xpath",
        "//button[@class='display-flex full-width \
            artdeco-dropdown__trigger artdeco-dropdown__trigger--placement-bottom ember-view']",
    )
    if "recent" not in sort.text:
        sort.click()
        time.sleep(5)
        sort_button = driver.find_element(
            "xpath",
            "//button[@class='display-flex \
                full-width artdeco-dropdown__trigger artdeco-dropdown__trigger--placement-bottom \
                    ember-view']/following-sibling::div",
        )
        sort_button = sort_button.find_elements("tag name", "li")[1]
        sort_button.click()
        time.sleep(5)
    return driver


@shared_task
def get_linkedin_feed():
    config_model = get_network_model("Config")
    config = config_model.objects.last()
    if config is None or not config.crawl_linkedin_feed:
        return
    driver = initialize_linkedin_driver()
    driver.get(f"{LINKEDIN_URL}feed/")
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "global-nav-search"))
    )
    driver = sort_by_recent(driver)
    scroll(driver, 5)
    time.sleep(5)
    articles = driver.find_elements(
        By.XPATH,
        './/div[starts-with(@data-id, "urn:li:activity:")]',
    )
    for article in articles:
        try:
            driver.execute_script("arguments[0].scrollIntoView();", article)
            time.sleep(2)
            feed_id = article.get_attribute("data-id")
            body = article.find_element(
                By.CLASS_NAME, "feed-shared-update-v2__commentary"
            ).text
            if DUPLICATE_CHECKER.exists(feed_id):
                continue
            DUPLICATE_CHECKER.set(feed_id, "", ex=86400 * 30)
            link = f"{LINKEDIN_URL}feed/update/{feed_id}/"
            body = telegram_text_purify(body)
            message = f"{body}\n\n{link}"
            not_tasks.send_telegram_message(strip_tags(message))
            time.sleep(3)
        except NoSuchElementException:
            logger.error(traceback.format_exc())
    driver_exit(driver)


@shared_task
def check_job_pages():
    pages = lin_models.JobSearch.objects.filter(enable=True).order_by("-priority")
    for page in pages:
        now = timezone.localtime()
        print(f"{now} start crawling linkedin page {page.name}")
        get_job_page_posts(page.pk)


def remove_redis_keys():
    redis_keys = DUPLICATE_CHECKER.keys("*")
    counter = DUPLICATE_CHECKER.delete(*redis_keys)
    return counter


def sort_by_most_recent(driver):
    filter_button = driver.find_elements(
        By.XPATH,
        './/button[contains(@class, "search-reusables__filter-pill-button")]',
    )
    filter_button[len(filter_button) - 1].click()
    time.sleep(2)
    most_recent_input = driver.find_elements(
        By.XPATH,
        './/label[contains(@for, "advanced-filter-sortBy-DD")]',
    )
    most_recent_input[0].click()
    time.sleep(2)
    apply_button = driver.find_elements(
        By.XPATH,
        './/button[contains(@data-test-reusables-filters-modal-show-results-button, "true")]',
    )
    apply_button[0].click()
    time.sleep(2)
    return driver


def is_english(language):
    """Checks if language term is English or not

    Args:
        language (str): language term

    Returns:
        bool: True if is "en" otherwise is False
    """
    if language != "en":
        return False
    return True


def check_eligible(keyword, job_detail):
    if keyword.lower() in job_detail.lower():
        return False
    return True


def is_eligible(ig_filters, job_detail) -> Tuple[bool, Optional[str]]:
    """Checks if job is eligible or not based on job_detail and ignoring filters
    Details are job's title, job's company, job's location

    Args:
        job_detail (dict): details of job like location, language
        ig_filters (IgnoringFilter): defined filters for a JobSearch

    Returns:
        bool: True if is eligible otherwise is False
    """
    if not is_english(job_detail["language"]):
        return False, "language"
    for ig_filter in ig_filters:
        detail, reason = "", ""
        if ig_filter.place == lin_models.IgnoringFilter.TITLE:
            detail, reason = job_detail["title"], "title"
        elif ig_filter.place == lin_models.IgnoringFilter.COMPANY:
            detail, reason = job_detail["company"], "company"
        elif ig_filter.place == lin_models.IgnoringFilter.LOCATION:
            detail, reason = job_detail["location"], "location"
        if not check_eligible(ig_filter.keyword, detail):
            return False, reason
    return True, None


def get_job_url(element):
    """Extract selected job url from driver

    Args:
        driver (WebDriver): browser driver

    Returns:
        str: job url
    """
    url = ""
    try:
        url = element.find_element(
            By.CLASS_NAME, "job-card-container__link"
        ).get_attribute("href")
    except NoSuchElementException:
        url = "Cannot-extract-url"
    url = url.split("?")[0]  # remove query params
    return url


def get_job_title(element):
    """Extract selected job title from driver

    Args:
        driver (WebDriver): browser driver

    Returns:
        str: job title
    """
    try:
        return element.find_element(By.CLASS_NAME, "artdeco-entity-lockup__title").text
    except NoSuchElementException:
        return "Cannot-extract-title"


def check_easy_apply(element):
    """Check if job has easy apply option

    Args:
        driver (WebDriver): browser driver

    Returns:
        str: check-mark emoji
    """
    try:
        element.find_element(By.CLASS_NAME, "job-card-container__apply-method")
        return "✅"
    except NoSuchElementException:
        return "❌"


def get_job_location(element):
    """Extract selected job location from driver

    Args:
        driver (WebDriver): browser driver

    Returns:
        str: job location
    """
    try:
        location = element.find_element(
            By.CLASS_NAME, "artdeco-entity-lockup__caption"
        ).text
    except NoSuchElementException:
        return "Cannot-extract-location"
    return location.replace("\n", " | ")


def get_job_company(element):
    """Extract selected job company from driver

    Args:
        driver (WebDriver): browser driver

    Returns:
        str: job company
    """
    try:
        return element.find_element(
            By.CLASS_NAME, "artdeco-entity-lockup__subtitle"
        ).text
    except NoSuchElementException:
        return "Cannot-extract-company"


def get_job_description(driver):
    """Extract selected job description from driver

    Args:
        driver (WebDriver): browser driver

    Returns:
        str: job description
    """
    try:
        return driver.find_element(By.ID, "job-details").text
    except NoSuchElementException:
        return "Cannot-extract-description"


def get_job_company_size(driver):
    """Extract selected job's company size

    Args:
        driver (WebDriver): browser driver

    Returns:
        str: job's company size
    """
    try:
        company_size_el = driver.find_elements(
            By.CLASS_NAME, "job-details-jobs-unified-top-card__job-insight"
        )
        if not company_size_el:
            return "Cannot-extract-company-size (empty element)"
        company_size = company_size_el[1].text
        return company_size.split("·")[0].replace("employees", "")
    except NoSuchElementException:
        return "Cannot-extract-company-size (no such element)"
    except IndexError:
        print(company_size)
        return "Cannot-extract-company-size (index error)"


def get_language(description):
    try:
        return detect(description)
    except LangDetectException:
        return "Cannot-detect-language"


def check_keywords(body, keywords):
    result = ""
    body = body.lower()
    for keyword in keywords:
        if keyword.lower() not in body:
            continue
        result += f"\n{keyword}: ✅"
    return result


def send_notification(message, data, keywords, output_channel_pk):
    """This function gets a message template and places the retrieved data into that.
    Then sends it to specified output channel

    Args:
        message (str): message template
        data (dict): dictionary that includes retrieved data
        output_channel_pk (int): primary key of output channel
    """
    not_tasks.send_message_to_telegram_channel(
        message.replace("url", strip_tags(data["url"]))
        .replace("lang", data["language"].upper())
        .replace("title", data["title"])
        .replace("location", data["location"])
        .replace("company", data["company"])
        .replace("size", data["company_size"])
        .replace("easy_apply", data["easy_apply"])
        .replace("keywords", check_keywords(data["description"], keywords)),
        output_channel_pk,
    )


def get_job_detail(driver, element):
    """This function gets browser driver and job html content and returns some
    information like job-link, job-desc and job-language.

    Args:
        driver (Webdriver): browser webdriver
        element (HTMLElement): html element of job

    Returns:
        result (dict): consist of information about job: link, description, language, title,
            location, company
    """
    result = {}
    result["url"] = get_job_url(element)
    result["easy_apply"] = check_easy_apply(element)
    result["description"] = get_job_description(driver)
    result["company_size"] = get_job_company_size(driver)
    result["language"] = get_language(result["description"])
    result["title"] = telegram_text_purify(get_job_title(element))
    result["location"] = telegram_text_purify(get_job_location(element))
    result["company"] = telegram_text_purify(get_job_company(element))
    return result


def get_card_id(element) -> str:
    """Tries to extract card id from element.

    Args:
        element (HTMLElement): job card element

    Returns:
        str: id of card
    """
    try:
        return element.find_element(
            By.XPATH,
            './/div[starts-with(@data-urn, "urn:li:activity:")]',
        ).get_attribute("data-urn")
    except NoSuchElementException:
        return "Cannot-extract-card-id"


@shared_task
def check_page_count(page_id: int, ignore_repetitive: bool, starting_job: int):
    """Check if we should crawl next page or not.

    Args:
        page_id (int): the primary key of JobSearch obj.
        ignore_repetitive (bool): ignore repetitive jobs or not.
        starting_job (int): the starting job of current page.
    """
    page = lin_models.JobSearch.objects.get(pk=page_id)
    if page.page_count == 1:
        return
    if starting_job != ((page.page_count - 1) * 25):
        get_job_page_posts.delay(page_id, ignore_repetitive, starting_job + 25)


@shared_task
def update_job_search_last_crawl_at(page_id: int):
    """Update last_crawl_at field of JobSearch object.
        Will be updated after crawling each page.
        To current time.

    Args:
        page_id (int): the primary key of JobSearch obj.
    """
    lin_models.JobSearch.objects.filter(pk=page_id).update(
        last_crawl_at=timezone.localtime()
    )


# @shared_task
# def get_job_page_posts(
#     page_id: int, ignore_repetitive: bool = True, starting_job: int = 0
# ):
#     """This function gets a page id and crawl it's jobs.

#     Args:
#         page_id (int): the primary key of JobSearch obj.
#         ignore_repetitive (bool, optional): ignore repetitive jobs or not. Defaults to True.
#         starting_job (int, optional): the starting job-id. Defaults to 0.
#     """
#     page = lin_models.JobSearch.objects.get(pk=page_id)
#     message, url, output_channel, keywords, ig_filters = page.page_data
#     driver = initialize_linkedin_driver()
#     url = f"{url}&start={starting_job}"
#     driver.get(url)
#     time.sleep(5)
#     driver = sort_by_most_recent(driver)  # It seems that we don't need this anymore
#     items = driver.find_elements(By.CLASS_NAME, "jobs-search-results__list-item")
#     print(
#         f"*** found {len(items)} items in page: {page_id} with starting-job: {starting_job}"
#     )
#     counter = 0
#     for item in items:
#         try:
#             driver.execute_script("arguments[0].scrollIntoView();", item)
#             job_id = item.get_attribute("data-occludable-job-id")
#             print(f"job_id: {job_id}")
#             # if id is none or is repetitive
#             if not job_id or (ignore_repetitive and DUPLICATE_CHECKER.exists(job_id)):
#                 continue
#             DUPLICATE_CHECKER.set(job_id, "", ex=86400 * 30)
#             item.click()
#             time.sleep(2)
#             job_detail = get_job_detail(driver, item)
#             eligible, reason = is_eligible(ig_filters, job_detail)
#             if not eligible:
#                 print(f"job is not eligible, reason: {reason}")
#                 store_ignored_content.delay(job_detail)
#                 continue
#             send_notification(message, job_detail, keywords, output_channel)
#             counter += 1
#         except StaleElementReferenceException:
#             print("stale element exception")
#             logger.warning("stale element exception")
#             break
#         except NoSuchElementException:
#             print("no such element exception")
#             logger.error(traceback.format_exc())
#         except Exception:
#             print("other exception")
#             logger.error(traceback.format_exc())
#     print(
#         f"*** found {counter} job in page: {page_id} with starting-job: {starting_job}"
#     )
#     check_page_count.delay(page_id, ignore_repetitive, starting_job)
#     update_job_search_last_crawl_at.delay(page_id)
#     driver_exit(driver)

@shared_task
def get_job_page_posts(page_id: int, ignore_repetitive: bool = True, starting_job: int = 0):
    """
    This function gets a page id and crawl its jobs.
    """
    page = lin_models.JobSearch.objects.get(pk=page_id)
    message, url, output_channel, keywords, ig_filters = page.page_data
    try:
        with initialize_linkedin_driver() as driver:
            prepare_driver(driver, url, starting_job)
            items = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "jobs-search-results__list-item"))
            )
            counter = process_items(driver, items, ignore_repetitive, message, keywords, output_channel, ig_filters)
        
        logger.info(f"found {counter} jobs in page: {page_id} with starting-job: {starting_job}")
        update_job_search_last_crawl_at.delay(page_id)
        check_page_count.delay(page_id, ignore_repetitive, starting_job)
    except Exception as e:
        logger.error(f"Error in get_job_page_posts: {e}")

def prepare_driver(driver, url, starting_job):
    full_url = f"{url}&start={starting_job}"
    driver.get(full_url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))  # Wait for page load

def process_items(driver, items, ignore_repetitive, message, keywords, output_channel, ig_filters):
    counter = 0
    for item in items:
        try:
            job_id = process_job_item(driver, item, ignore_repetitive, message, keywords, output_channel, ig_filters)
            if job_id:
                counter += 1
        except StaleElementReferenceException:
            logger.warning("Stale element reference exception")
            break
        except NoSuchElementException:
            logger.error("No such element exception", exc_info=True)
        except Exception:
            logger.error("Unhandled exception in process_items", exc_info=True)
    return counter

def process_job_item(driver, item, ignore_repetitive, message, keywords, output_channel, ig_filters):
    driver.execute_script("arguments[0].scrollIntoView();", item)
    job_id = item.get_attribute("data-occludable-job-id")
    logger.info(f"Processing job_id: {job_id}")

    if not job_id or (ignore_repetitive and DUPLICATE_CHECKER.exists(job_id)):
        return None
    DUPLICATE_CHECKER.set(job_id, "", ex=86400 * 30)

    item.click()
    time.sleep(2)
    # WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "job-detail")))
    job_detail = get_job_detail(driver, item)

    eligible, reason = is_eligible(ig_filters, job_detail)
    if not eligible:
        logger.info(f"Job is not eligible, reason: {reason}")
        store_ignored_content.delay(job_detail)
        return None

    time.sleep(2)  # Delay between sending each message
    send_notification(message, job_detail, keywords, output_channel)
    return job_id


@shared_task
def update_expression_search_last_crawl_at(page_id):
    lin_models.ExpressionSearch.objects.filter(pk=page_id).update(
        last_crawl_at=timezone.localtime()
    )


@shared_task
def get_expression_search_posts(page_id, ignore_repetitive=True):
    try:
        page = lin_models.ExpressionSearch.objects.get(pk=page_id)
        with initialize_linkedin_driver() as driver:
            driver.get(page.url)
            wait = WebDriverWait(driver, 10)
            articles = wait.until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "artdeco-card"))
            )
            counter = process_articles(driver, articles, ignore_repetitive, page)

        logger.info(f"found {counter} post in page {page_id}")
        update_expression_search_last_crawl_at.delay(page.pk)
    except Exception as e:
        logger.error(f"Error in get_expression_search_posts: {e}")


def process_articles(driver, articles, ignore_repetitive, page):
    counter = 0
    for article in articles:
        try:
            process_article(driver, article, ignore_repetitive, page)
            counter += 1
        except NoSuchElementException:
            logger.error("Element not found", exc_info=True)
        except TimeoutException:
            logger.error("Timeout waiting for element", exc_info=True)
    return counter


def process_article(driver, article, ignore_repetitive, page):
    driver.execute_script("arguments[0].scrollIntoView();", article)
    post_id = get_card_id(article)
    if not post_id or (ignore_repetitive and DUPLICATE_CHECKER.exists(post_id)):
        logger.info(f"id is none or duplicate, id: {post_id}")
        return
    DUPLICATE_CHECKER.set(post_id, "", ex=86400 * 30)
    body = extract_body(article)
    link = f"https://www.linkedin.com/feed/update/{post_id}/"
    message = f"{telegram_text_purify(body)}\n\n{link}"
    time.sleep(2)  # Delay between sending each message
    not_tasks.send_message_to_telegram_channel(
        strip_tags(message), page.output_channel.pk
    )


def extract_body(article):
    try:
        return article.find_element(
            By.CLASS_NAME, "feed-shared-update-v2__description"
        ).text
    except NoSuchElementException:
        logger.info("No such element exception")
        return "Cannot-extract-body"


@shared_task
def check_expression_search_pages():
    pages = lin_models.ExpressionSearch.objects.filter(enable=True)
    for page in pages:
        start_time = timezone.localtime()
        print(f"{start_time} Start crawling linkedin page {page.name}")
        get_expression_search_posts(page.pk)


@shared_task
def store_ignored_content(job_detail):
    job_detail.pop("company_size", None)  # Remove extra key
    job_detail.pop("easy_apply", None)  # Remove extra key
    lin_models.IgnoredJob.objects.create(**job_detail)
