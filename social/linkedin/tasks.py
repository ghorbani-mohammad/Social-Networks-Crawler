import time
import redis
import pickle
import traceback
from langdetect import detect
from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib3.exceptions import MaxRetryError
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import StaleElementReferenceException

from django.conf import settings
from django.utils import timezone
from django.utils.html import strip_tags
from celery import shared_task
from celery.utils.log import get_task_logger

from network import models as net_models
from linkedin import models as lin_models
from notification import tasks as not_tasks
from reusable.other import only_one_concurrency
from notification.utils import telegram_text_purify

logger = get_task_logger(__name__)
MINUTE = 60
TASKS_TIMEOUT = 1 * MINUTE
DUPLICATE_CHECKER = redis.StrictRedis(host="social_redis", port=6379, db=5)


def get_driver():
    """This function creates a browser driver and returns it

    Returns:
        Webdriver: webdriver browser
    """
    try:
        return webdriver.Remote(
            "http://social_firefox:4444/wd/hub",
            DesiredCapabilities.FIREFOX,
        )
    except MaxRetryError as e:
        logger.error("Couldn't create browser session.")
    # Should do appropriate action instead of exit (for example restarting docker)
    exit()


def initialize_linkedin_driver():
    """This function head the browser to the LinkedIn website.

    Returns:
        Webdriver: webdriver browser
    """
    driver = get_driver()
    cookies = pickle.load(open("/app/social/cookies.pkl", "rb"))
    driver.get("https://www.linkedin.com/")
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


@shared_task()
def login():
    """This function login into LinkedIn and store credential info into /app/social/cookies.pkl .
    It read username and password from environment variables as follow:
    LINKEDIN_EMAIL -> username
    LINKEDIN_PASSWORD -> password
    """
    driver = get_driver()
    driver.get("https://www.linkedin.com/login")
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
        pickle.dump(driver.get_cookies(), open("/app/social/cookies.pkl", "wb"))
    except Exception:
        logger.error(traceback.format_exc())
    finally:
        driver_exit(driver)


@shared_task()
def store_posts(channel_id, post_id, body, reaction_count, comment_count, share_count):
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
    exists = net_models.Post.objects.filter(
        network_id=post_id, channel_id=channel_id
    ).exists()
    data = {
        "reaction_count": reaction_count,
        "comment_count": comment_count,
        "share_count": share_count,
    }
    if not exists:
        net_models.Post.objects.create(
            channel_id=channel_id,
            network_id=post_id,
            body=body,
            data=data,
            share_count=share_count,
            views_count=reaction_count + comment_count + share_count,
        )
    else:
        post = net_models.Post.objects.get(network_id=post_id)
        post.share_count = share_count
        post.views_count = reaction_count + comment_count + share_count
        post.data = data
        post.save()


def scroll(driver, counter):
    SCROLL_PAUSE_TIME = 0.5
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_counter = 0
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        scroll_counter += 1
        if new_height == last_height or scroll_counter > counter:
            break
        last_height = new_height


@shared_task(name="get_linkedin_posts")
@only_one_concurrency(key="browser1", timeout=TASKS_TIMEOUT)
def get_linkedin_posts(channel_id):
    channel = net_models.Channel.objects.get(pk=channel_id)
    channel_url = channel.username
    driver = initialize_linkedin_driver()
    driver.get(channel_url)
    scroll(driver, 1)
    time.sleep(5)
    try:
        articles = driver.find_elements(By.CLASS_NAME, "feed-shared-update-v2")
        for article in articles:
            try:
                id = article.get_attribute("data-urn")
                body = article.find_element(By.CLASS_NAME, "break-words").text
                reaction = article.find_elements(
                    By.XPATH,
                    './/ul[contains(@class, "social-details-social-counts")]',
                )[0]
                reaction_counter, comment_counter, share_counter = 0, 0, 0
                socials = reaction.find_elements(By.XPATH, ".//li")
                for social in socials:
                    temp = social.get_attribute("aria-label")
                    if not temp:
                        temp = social.find_elements(By.XPATH, ".//button")
                        temp = temp[0].get_attribute("aria-label")
                    temp = temp.split()[:2]
                    value, elem = int(temp[0].replace(",", "")), temp[1]
                    if elem == "reactions":
                        reaction_counter = value
                    elif elem == "comments":
                        comment_counter = value
                    elif elem == "shares":
                        share_counter = value
                store_posts.delay(
                    channel_id,
                    id,
                    body,
                    reaction_counter,
                    comment_counter,
                    share_counter,
                )
            except Exception:
                logger.error(traceback.format_exc())
    except Exception:
        logger.error(traceback.format_exc())
    finally:
        driver_exit(driver)
        channel.last_crawl = timezone.localtime()
        channel.save()


def sort_by_recent(driver):
    sort = driver.find_element(
        "xpath",
        "//button[@class='display-flex full-width artdeco-dropdown__trigger artdeco-dropdown__trigger--placement-bottom ember-view']",
    )
    if "recent" not in sort.text:
        sort.click()
        time.sleep(5)
        sort_by_recent = driver.find_element(
            "xpath",
            "//button[@class='display-flex full-width artdeco-dropdown__trigger artdeco-dropdown__trigger--placement-bottom ember-view']/following-sibling::div",
        )
        sort_by_recent = sort_by_recent.find_elements("tag name", "li")[1]
        sort_by_recent.click()
        time.sleep(5)
    return driver


@shared_task()
def get_linkedin_feed():
    config = net_models.Config.objects.last()
    if config is None or not config.crawl_linkedin_feed:
        return
    driver = initialize_linkedin_driver()
    driver.get("https://www.linkedin.com/feed/")
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
            id = article.get_attribute("data-id")
            body = article.find_element(
                By.CLASS_NAME, "feed-shared-update-v2__commentary"
            ).text
            if DUPLICATE_CHECKER.exists(id):
                continue
            DUPLICATE_CHECKER.set(id, "", ex=86400 * 30)
            link = f"https://www.linkedin.com/feed/update/{id}/"
            body = telegram_text_purify(body)
            message = f"{body}\n\n{link}"
            not_tasks.send_telegram_message(strip_tags(message))
            time.sleep(3)
        except Exception:
            logger.error(traceback.format_exc())
    driver_exit(driver)


@shared_task()
def check_job_pages():
    pages = lin_models.JobSearch.objects.filter(enable=True)
    for page in pages:
        time = timezone.localtime()
        print(f"{time} start crawling linkedin page {page.name}")
        get_job_page_posts(page.pk)
        page.last_crawl_at = time
        page.save()


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


def is_eligible(ig_filters, job_detail):
    """Checks if job is eligible or not based on job_detail and ignoring filters
    Details are job's title, job's company, job's location

    Args:
        job_detail (dict): details of job like location, language
        ig_filters (IgnoringFilter): defined filters for a JobSearch

    Returns:
        bool: True if is eligible otherwise is False
    """
    if not is_english(job_detail["language"]):
        return False
    for filter in ig_filters:
        detail = ""
        if filter.place == lin_models.IgnoringFilter.TITLE:
            detail = job_detail["title"]
        elif filter.place == lin_models.IgnoringFilter.COMPANY:
            detail = job_detail["company"]
        elif filter.place == lin_models.IgnoringFilter.LOCATION:
            detail = job_detail["location"]
        if not check_eligible(filter.keyword, detail):
            return False
    return True


@shared_task
def store_ignored_content(job_detail):
    lin_models.IgnoredJob.objects.create(**job_detail)


def get_job_url(element):
    """Extract selected job url from driver

    Args:
        driver (WebDriver): browser driver

    Returns:
        str: job url
    """
    url = element.find_element(By.CLASS_NAME, "job-card-container__link").get_attribute(
        "href"
    )
    url = url.split("?")[0]  # remove query params
    return url


def get_job_title(element):
    """Extract selected job title from driver

    Args:
        driver (WebDriver): browser driver

    Returns:
        str: job title
    """
    return element.find_element(By.CLASS_NAME, "artdeco-entity-lockup__title").text


def get_job_location(element):
    """Extract selected job location from driver

    Args:
        driver (WebDriver): browser driver

    Returns:
        str: job location
    """
    location = element.find_element(
        By.CLASS_NAME, "artdeco-entity-lockup__caption"
    ).text
    return location.replace("\n", " | ")


def get_job_company(element):
    """Extract selected job company from driver

    Args:
        driver (WebDriver): browser driver

    Returns:
        str: job company
    """
    return element.find_element(By.CLASS_NAME, "artdeco-entity-lockup__subtitle").text


def get_job_description(driver):
    """Extract selected job description from driver

    Args:
        driver (WebDriver): browser driver

    Returns:
        str: job description
    """
    return driver.find_element(By.ID, "job-details").text


def check_keywords(body, keywords):
    result = ""
    body = body.lower()
    for keyword in keywords:
        if keyword.lower() in body:
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
    result["description"] = get_job_description(driver)
    result["language"] = detect(result["description"])
    result["title"] = telegram_text_purify(get_job_title(element))
    result["location"] = telegram_text_purify(get_job_location(element))
    result["company"] = telegram_text_purify(get_job_company(element))
    return result


@shared_task()
def get_job_page_posts(page_id, ignore_repetitive=True):
    page = lin_models.JobSearch.objects.get(pk=page_id)
    message, url, output_channel, keywords, ig_filters = page.page_data
    driver = initialize_linkedin_driver()
    driver.get(url)
    time.sleep(5)
    driver = sort_by_most_recent(driver)
    items = driver.find_elements(By.CLASS_NAME, "jobs-search-results__list-item")
    counter = 0
    for item in items:
        try:
            driver.execute_script("arguments[0].scrollIntoView();", item)
            id = item.get_attribute("data-occludable-job-id")
            if ignore_repetitive and DUPLICATE_CHECKER.exists(id):
                continue
            DUPLICATE_CHECKER.set(id, "", ex=86400 * 30)
            item.click()
            time.sleep(2)
            job_detail = get_job_detail(driver, item)
            if not is_eligible(ig_filters, job_detail):
                store_ignored_content.delay(job_detail)
                continue
            send_notification(message, job_detail, keywords, output_channel)
            counter += 1
        except StaleElementReferenceException:
            logger.error("stale element exception")
            break
        except Exception:
            logger.error(traceback.format_exc())
    print(f"found {counter} job in page {page_id}")
    driver_exit(driver)


@shared_task()
def get_expression_search_posts(page_id, ignore_repetitive=True):
    page = lin_models.ExpressionSearch.objects.get(pk=page_id)
    driver = initialize_linkedin_driver()
    driver.get(page.url)
    time.sleep(5)
    driver = sort_by_most_recent(driver)
    counter = 0
    time.sleep(5)
    print(f"found {counter} job in page {page_id}")
    driver_exit(driver)
