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

from django.conf import settings
from django.utils import timezone
from django.utils.html import strip_tags
from celery import shared_task
from celery.utils.log import get_task_logger

from network import models as net_models
from linkedin import models as lin_models
from notification import tasks as not_tasks
from reusable.other import only_one_concurrency

logger = get_task_logger(__name__)
MINUTE = 60
TASKS_TIMEOUT = 1 * MINUTE
DUPLICATE_CHECKER = redis.StrictRedis(host="social_redis", port=6379, db=5)


def get_driver():
    try:
        return webdriver.Remote(
            "http://social_firefox:4444/wd/hub",
            DesiredCapabilities.FIREFOX,
        )
    except MaxRetryError as e:
        logger.error("Couldn't create browser session.")
    # Should do appropriate action instead of exit (for example restarting docker)
    exit()


@shared_task()
def login():
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
    except Exception as e:
        logger.error(traceback.format_exc())
    finally:
        time.sleep(5)
        driver.close()


@shared_task()
def store_posts(channel_id, post_id, body, reaction_count, comment_count, share_count):
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
    print(f"****** Linkedin crawling {channel} started")
    channel_url = channel.username
    driver = get_driver()
    cookies = pickle.load(open("/app/social/cookies.pkl", "rb"))
    driver.get("https://www.linkedin.com/")
    for cookie in cookies:
        driver.add_cookie(cookie)
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
            except Exception as e:
                logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(traceback.format_exc())
    finally:
        time.sleep(2)
        driver.quit()
        channel.last_crawl = timezone.localtime()
        channel.save()


def sort_by_recent(driver):
    sort = driver.find_element(
        "xpath",
        "//button[@class='display-flex full-width artdeco-dropdown__trigger artdeco-dropdown__trigger--placement-bottom ember-view']",
    )
    if "recent" not in sort.text:
        print("sort on recent")
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
    driver = get_driver()
    cookies = pickle.load(open("/app/social/cookies.pkl", "rb"))
    driver.get("https://www.linkedin.com/")
    for cookie in cookies:
        driver.add_cookie(cookie)
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
            body = body.replace("#", "-")
            body = body.replace("&", "-")
            message = f"{body}\n\n{link}"
            not_tasks.send_telegram_message(strip_tags(message))
            time.sleep(3)
        except Exception as e:
            print(traceback.format_exc())
    time.sleep(2)
    driver.quit()


@shared_task()
def check_job_pages():
    pages = lin_models.JobPage.objects.filter(enable=True)
    for page in pages:
        time = timezone.localtime()
        print(f"{time} start crawling linkedin page {page.name}")
        get_job_page_posts(page.message, page.url, page.output_channel.pk)
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


def check_language(language):
    if language != "en":
        return False
    return True


@shared_task
def store_ignored_content(url, content):
    lin_models.IgnoredContent.objects.create(url=url, content=content)


@shared_task()
def get_job_page_posts(message, url, output_channel_pk):
    driver = get_driver()
    cookies = pickle.load(open("/app/social/cookies.pkl", "rb"))
    driver.get("https://www.linkedin.com/")
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.get(url)
    time.sleep(5)
    driver = sort_by_most_recent(driver)
    items = driver.find_elements(By.CLASS_NAME, "jobs-search-results__list-item")
    counter = 0
    for item in items:
        try:
            driver.execute_script("arguments[0].scrollIntoView();", item)
            id = item.get_attribute("data-occludable-job-id")
            if DUPLICATE_CHECKER.exists(id):
                continue
            item.click()
            time.sleep(2)
            DUPLICATE_CHECKER.set(id, "", ex=86400 * 30)
            job_desc = driver.find_element(By.ID, "job-details").text
            detected_language = detect(job_desc)
            counter += 1
            link = item.find_element(
                By.CLASS_NAME, "job-card-container__link"
            ).get_attribute("href")
            link = link.split("?")[0]  # remove query params
            if not check_language(detected_language):
                store_ignored_content.delay(link, job_desc)
                continue
            not_tasks.send_message_to_telegram_channel(
                message.replace("link", strip_tags(link)).replace(
                    "lang", detected_language.upper()
                ),
                output_channel_pk,
            )
            time.sleep(4)
        except Exception as e:
            print(e)
    print(f"found {counter} job")
    time.sleep(2)
    driver.quit()
