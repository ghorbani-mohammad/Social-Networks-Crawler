import time
import pickle
import random
import traceback

from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib3.exceptions import MaxRetryError
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import (
    SessionNotCreatedException,
    TimeoutException,
    NoSuchElementException,
)
from celery import shared_task
from django.utils import timezone
from django.utils.html import strip_tags
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.cache import caches

from . import models
from notification import tasks as not_tasks
from notification import utils as not_utils
from network import models as net_models
from reusable.other import only_one_concurrency

logger = get_task_logger(__name__)
MINUTE = 60
HOUR = 60 * MINUTE
DAY = 24 * HOUR
TASKS_TIMEOUT = 1 * MINUTE
DUPLICATE_CHECKER = caches["twitter"]


def get_driver():
    """Creates a webdriver with Firefox capabilities.
    In some situation session can't be created.

    Returns:
        webdriver: webdriver object
    """
    try:
        return webdriver.Remote(
            "http://social_firefox:4444/wd/hub",
            DesiredCapabilities.FIREFOX,
        )
    except SessionNotCreatedException as e:
        logger.error(f"Error: {e}\n\n{traceback.format_exc()}")
    except MaxRetryError as e:
        logger.error(f"Error: {e}\n\n{traceback.format_exc()}")


def initialize_twitter_driver():
    """This function head the browser to the twitter website.

    Returns:
        Webdriver: webdriver browser
    """
    driver = get_driver()
    cookies = pickle.load(open("/app/social/twitter_cookies.pkl", "rb"))
    driver.get("https://www.twitter.com/")
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


def login():
    driver = get_driver()
    driver.get("https://twitter.com/i/flow/login")
    time.sleep(5)
    username_elem = driver.find_element("xpath", "//input[@autocomplete='username']")
    username_elem.send_keys(settings.TWITTER_USERNAME)
    username_elem.send_keys(Keys.ENTER)
    time.sleep(5)
    password_elem = driver.find_element(
        "xpath", "//input[@autocomplete='current-password']"
    )
    password_elem.send_keys(settings.TWITTER_PASSWORD)
    password_elem.send_keys(Keys.ENTER)
    time.sleep(5)
    pickle.dump(driver.get_cookies(), open("/app/social/twitter_cookies.pkl", "wb"))
    driver_exit(driver)


def scroll(driver, counter):
    """Scroll browser for counter times

    Args:
        driver (webdriver): webdriver object
        counter (int): specify number of scrolls
    """
    SCROLL_PAUSE_TIME = 2
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


def get_post_detail(article):
    """extract information from an tweet div (information are id, body, reply, retweet, like)

    Args:
        article (element): it is a tweet html body

    Returns:
        detail (json): extracted information
    """
    detail = {}
    detail["id"] = int(
        article.find_element(
            By.XPATH,
            ".//a[@role='link' and @dir='auto' and @aria-label]",
        )
        .get_attribute("href")
        .split("/")[-1]
    )
    detail["body"] = article.find_element(
        By.XPATH,
        ".//div[@dir='auto' and starts-with(@id,'id__') and not(contains(@data-testid, 'socialContext'))]",
    ).text
    for item in ["reply", "retweet", "like"]:
        detail[f"{item}_count"] = int(
            article.find_element(
                By.XPATH,
                f".//div[@role='button' and @data-testid='{item}']",
            )
            .get_attribute("aria-label")
            .split()[0]
        )
    return detail


def get_comment_detail(article):
    """extract information from an comment div (information are id, body, reply, retweet, like)

    Args:
        article (element): it is a comment html body

    Returns:
        detail (json): extracted information
    """
    detail = {}
    detail["id"] = int(
        article.find_element(
            By.XPATH,
            ".//a[@role='link' and @dir='auto' and starts-with(@id,'id__')]",
        )
        .get_attribute("href")
        .split("/")[-1]
    )
    detail["body"] = article.find_element(
        By.XPATH,
        ".//div[@dir='auto' and starts-with(@id,'id__') and not(@style) and @lang]//span",
    ).text
    for item in ["reply", "retweet", "like"]:
        detail[f"{item}_count"] = int(
            article.find_element(
                By.XPATH,
                f".//div[@role='button' and @data-testid='{item}']",
            )
            .get_attribute("aria-label")
            .split()[0]
        )
    return detail


@shared_task
def store_twitter_posts(
    channel_id, post_id, body, replies_counter, retweets_counter, likes_counter
):
    """Store or update a twitter post

    Args:
        channel_id (int): id of the channel
        post_id (int): id of the post (twitter id)
        body (str): text of the post
        replies_counter (int): number of replies
        retweets_counter (int): number of retweets
        likes_counter (int): number of likes
    """
    exists = net_models.Post.objects.filter(
        network_id=post_id, channel_id=channel_id
    ).exists()
    data = {
        "replies_count": replies_counter,
        "retweets_count": retweets_counter,
        "likes_count": likes_counter,
    }
    views_count = replies_counter + retweets_counter + likes_counter
    if not exists:
        net_models.Post.objects.create(
            channel_id=channel_id,
            network_id=post_id,
            body=body,
            data=data,
            share_count=data["retweets_count"],
            views_count=views_count,
        )
    else:
        post = net_models.Post.objects.filter(body=body, channel_id=channel_id).first()
        post.data = data
        post.share_count = data["retweets_count"]
        post.views_count = views_count
        post.save()


@shared_task(name="get_twitter_posts")
@only_one_concurrency(key="browser", timeout=TASKS_TIMEOUT)
def get_twitter_posts(channel_id):
    """Get posts of a channel
    The only-one-concurrency decorator is used to ensure that we will not open
    two browser at the same time.

    Args:
        channel_id (int): id of the channel
    """
    channel = net_models.Channel.objects.get(pk=channel_id)
    print(f"****** Twitter crawling {channel} started")
    channel_url = f"{channel.network.url}/{channel.username}"
    driver = initialize_twitter_driver()
    driver.get(channel_url)
    scroll(driver, 5)
    time.sleep(5)
    articles = driver.find_elements(By.TAG_NAME, "article")
    for article in articles:
        try:
            post_detail = get_post_detail(article)
            store_twitter_posts.delay(
                channel_id,
                post_detail["id"],
                post_detail["body"],
                post_detail["reply_count"],
                post_detail["retweet_count"],
                post_detail["like_count"],
            )
        except Exception:
            logger.error(traceback.format_exc())
    driver_exit(driver)
    channel.last_crawl = timezone.localtime()
    channel.save()


@shared_task
def get_twitter_post_comments(post_id):
    """Get comments of a post

    Args:
        post_id (int): id of the post
    """
    post = net_models.Post.objects.get(pk=post_id)
    driver = get_driver()
    driver.get(f"{post.channel.username}/status/{post.network_id}")
    scroll(driver, 2)
    time.sleep(10)
    articles = driver.find_elements(By.TAG_NAME, "article")
    for article in articles:
        try:
            post_detail = get_comment_detail(article)
            # store on different tables?
            store_twitter_posts.delay(
                post.channel_id,
                post_detail["id"],
                post_detail["body"],
                post_detail["reply_count"],
                post_detail["retweet_count"],
                post_detail["like_count"],
            )
        except Exception:
            logger.error(traceback.format_exc())
    driver_exit(driver)


@shared_task
def check_twitter_pages():
    """Check which page or channel we should craw
    This is a period task.
    """
    pages = models.SearchPage.objects.filter(enable=True)
    for page in pages:
        print(f"Crawling search-page {page.pk} started")
        crawl_search_page(page.pk)


def get_tweet_id(article):
    try:
        return int(
            article.find_element(
                By.XPATH,
                ".//a[@role='link' and @dir and @aria-label and not(@tabindex)]",
            )
            .get_attribute("href")
            .split("/")[-1]
        )
    except NoSuchElementException:
        return random.randint(0, 10**20)


def get_tweet_body(article):
    return article.find_element(
        By.XPATH,
        ".//div[@dir='auto' and starts-with(@id,'id__') and @data-testid='tweetText']",
    ).text


def get_tweet_username(article):
    elements = article.find_elements(
        By.XPATH,
        ".//a[@role='link' and starts-with(@href,'/') and @tabindex='-1']",
    )
    if len(elements) > 1:
        return elements[1].text
    return elements[0].text


def get_tweet_link(tweet_detail):
    return f"https://twitter.com/{tweet_detail['username'].replace('@','')}/status/{tweet_detail['id']}"


def get_post_detail_v2(article):
    """extract post details from html element

    Args:
        article (html element): html of a tweet.

    Returns:
        data (json): information of tweet.
    """
    detail = {}
    detail["id"] = get_tweet_id(article)
    detail["body"] = get_tweet_body(article)
    detail["username"] = get_tweet_username(article)
    detail["link"] = get_tweet_link(detail)
    return detail


@shared_task
def update_last_crawl(page_id):
    page = models.SearchPage.objects.get(pk=page_id)
    page.last_crawl_at = timezone.localtime()
    page.save()


def determine_to_send(body, terms1, terms2):
    for term in terms2:
        if term in body:
            for term in terms1:
                if term in body:
                    return True
    return False


def notification_message_prepare(text, link):
    text = not_utils.telegram_text_purify(text)
    return f"{strip_tags(text)}\n\n{link}"


def driver_head_to_page(driver, url):
    try:
        driver.get(url)
        return driver
    except TimeoutException as e:
        logger.error(f"{e}\n\n{traceback.format_exc()}")
    except Exception as e:
        logger.error(f"{e}\n\n{traceback.format_exc()}")
    return None


@shared_task
def crawl_search_page(page_id):
    """Crawl a search page of twitter.

    Args:
        page_id (int): id of a search page
    """
    update_last_crawl.delay(page_id)
    page = models.SearchPage.objects.get(pk=page_id)
    driver = initialize_twitter_driver()
    if driver is None:
        return
    driver = driver_head_to_page(driver, page.url)
    if driver is None:
        return
    time.sleep(5)
    scroll_counter = 0
    while scroll_counter < 1:
        tweets = driver.find_elements(By.TAG_NAME, "article")
        print(f"found {len(tweets)} tweets")
        terms1 = page.terms_level_1.split("+") if page.terms_level_1 else []
        terms2 = page.terms_level_2.split("+") if page.terms_level_2 else []
        for tweet in tweets:
            body = None
            try:
                driver.execute_script("arguments[0].scrollIntoView();", tweet)
                post_detail = get_post_detail_v2(tweet)
                body = post_detail["body"]
                if DUPLICATE_CHECKER.get(post_detail["id"]):
                    print(f"{post_detail['id']} exists")
                    continue
                print(f"{post_detail['id']} NOT exists")
                DUPLICATE_CHECKER.set(post_detail["id"], 1, DAY * 30)
                send = determine_to_send(body, terms1, terms2)
                if send:
                    body = notification_message_prepare(body, post_detail["link"])
                    not_tasks.send_message_to_telegram_channel(
                        body, page.output_channel.pk
                    )
                    time.sleep(1)
            except Exception:
                logger.error(traceback.format_exc())
        scroll(driver, 1)
        time.sleep(5)
        scroll_counter += 1
    driver_exit(driver)
