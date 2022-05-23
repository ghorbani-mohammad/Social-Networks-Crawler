import time
import redis
import pickle
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
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


@shared_task()
def login():
    driver = webdriver.Remote(
        "http://social_firefox:4444/wd/hub",
        DesiredCapabilities.FIREFOX,
    )
    driver.get("https://www.linkedin.com/login")
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        email_elem = driver.find_element_by_id("username")
        email_elem.send_keys(settings.LINKEDIN_EMAIL)
        password_elem = driver.find_element_by_id("password")
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
    driver = webdriver.Remote(
        "http://social_firefox:4444/wd/hub",
        DesiredCapabilities.FIREFOX,
    )
    cookies = pickle.load(open("/app/social/cookies.pkl", "rb"))
    driver.get("https://www.linkedin.com/")
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.get(channel_url)
    scroll(driver, 1)
    time.sleep(5)
    try:
        articles = driver.find_elements_by_class_name("feed-shared-update-v2")
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


@shared_task()
def get_linkedin_feed():
    config = net_models.Config.objects.last()
    if config is None or not config.crawl_linkedin_feed:
        return
    driver = webdriver.Remote(
        "http://social_firefox:4444/wd/hub",
        DesiredCapabilities.FIREFOX,
    )
    cookies = pickle.load(open("/app/social/cookies.pkl", "rb"))
    driver.get("https://www.linkedin.com/")
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.get("https://www.linkedin.com/feed/")
    scroll(driver, 1)
    time.sleep(5)
    articles = driver.find_elements(
        By.XPATH,
        './/div[starts-with(@data-id, "urn:li:activity:")]',
    )
    driver.implicitly_wait(5)
    for article in articles:
        try:
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
            time.sleep(4)
        except Exception as e:
            print("can't find element")
    time.sleep(2)
    driver.quit()


@shared_task()
def check_job_pages():
    pages = lin_models.JobPage.objects.filter(enable=True)
    for page in pages:
        get_job_page_posts(page.url)
        page.last_crawl_at = timezone.localtime()
        page.save()


@shared_task()
def get_job_page_posts(url):
    driver = webdriver.Remote(
        "http://social_firefox:4444/wd/hub",
        DesiredCapabilities.FIREFOX,
    )
    cookies = pickle.load(open("/app/social/cookies.pkl", "rb"))
    driver.get("https://www.linkedin.com/")
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.get(url)
    time.sleep(5)
    items = driver.find_elements(By.CLASS_NAME, "jobs-search-results__list-item")
    for item in items:
        try:
            id = item.get_attribute("data-occludable-job-id")
            if DUPLICATE_CHECKER.exists(id):
                continue
            link = item.find_element(
                By.CLASS_NAME, "job-card-container__link"
            ).get_attribute("href")
            DUPLICATE_CHECKER.set(id, "", ex=86400 * 30)
            not_tasks.send_telegram_message(strip_tags(link))
            time.sleep(4)
        except Exception as e:
            print("can't find element")
    time.sleep(2)
    driver.quit()
