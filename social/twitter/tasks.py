import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from celery import shared_task
from django.utils import timezone
from django.utils.html import strip_tags
from celery.utils.log import get_task_logger

from . import models
from notification import tasks as not_tasks
from network import models as net_models
from reusable.other import only_one_concurrency

logger = get_task_logger(__name__)
MINUTE = 60
TASKS_TIMEOUT = 1 * MINUTE


def get_driver():
    return webdriver.Remote(
        "http://social_firefox:4444/wd/hub",
        DesiredCapabilities.FIREFOX,
    )


def scroll(driver, counter):
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


@shared_task()
def store_twitter_posts(
    channel_id, post_id, body, replies_counter, retweets_counter, likes_counter
):
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
    channel = net_models.Channel.objects.get(pk=channel_id)
    print(f"****** Twitter crawling {channel} started")
    channel_url = f"{channel.network.url}/{channel.username}"
    driver = get_driver()
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
        except Exception as e:
            logger.error(e)
    time.sleep(2)
    driver.quit()
    channel.last_crawl = timezone.localtime()
    channel.save()


@shared_task()
def get_twitter_post_comments(post_id):
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
        except Exception as e:
            print(e)
            logger.error(e)
    driver.quit()


@shared_task()
def check_twitter_pages():
    pages = models.SearchPage.objects.filter(enable=True)
    for page in pages:
        crawl_search_page(page.pk)
        page.last_crawl_at = timezone.localtime()
        page.save()


def get_post_detail_v2(article):
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
        ".//div[@dir='auto' and starts-with(@id,'id__') and @data-testid='tweetText']",
    ).text
    detail["username"] = article.find_element(
        By.XPATH,
        ".//a[@role='link' and starts-with(@href,'/') and @tabindex='-1']",
    ).text
    detail[
        "link"
    ] = f"https://twitter.com/{detail['username'].replace('@','')}/status/{detail['id']}"
    return detail


def crawl_search_page(page_id):
    page = models.SearchPage.objects.get(pk=page_id)
    driver = get_driver()
    driver.get(page.url)
    scroll(driver, 15)
    time.sleep(5)
    articles = driver.find_elements(By.TAG_NAME, "article")
    terms1 = page.terms_level_1.split() if page.terms_level_1 else []
    terms2 = page.terms_level_2.split() if page.terms_level_2 else []
    for article in articles:
        try:
            post_detail = get_post_detail_v2(article)
            body = post_detail["body"]
            body = body.replace("#", "-").replace("&", "-")
            send = False
            for term in terms2:
                if term in body:
                    for term in terms1:
                        if term in body:
                            send = True
                            break
            if send:
                not_tasks.send_telegram_message(
                    f"{strip_tags(body)}\n\n" + post_detail["link"]
                )
                time.sleep(1)
        except Exception as e:
            print(e)
            logger.error(e)
    time.sleep(2)
    driver.quit()
