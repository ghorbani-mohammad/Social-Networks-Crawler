import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from celery import shared_task
from celery.utils.log import get_task_logger

from network import models as net_models

logger = get_task_logger(__name__)


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


@shared_task(name="store_post")
def store_posts(channel_id, post_id, body):
    exists = net_models.Post.objects.filter(
        network_id=post_id, channel_id=channel_id
    ).exists()
    if not exists:
        net_models.Post.objects.create(
            channel_id=channel_id, network_id=post_id, body=body
        )
    else:
        post = net_models.Post.objects.get(network_id=post_id)
        post.save()


@shared_task(name="get_posts")
def get_posts(channel_id):
    channel = net_models.Channel.objects.get(pk=channel_id)
    channel_url = channel.username
    driver = webdriver.Remote(
        "http://social_firefox:4444/wd/hub",
        DesiredCapabilities.FIREFOX,
    )
    driver.get(channel_url)
    scroll(driver, 2)
    articles = driver.find_elements(By.TAG_NAME, "article")
    time.sleep(10)
    articles = driver.find_elements(By.TAG_NAME, "article")
    for article in articles:
        body = article.find_element(
            By.XPATH,
            ".//div[@dir='auto' and starts-with(@id,'id__') and not(contains(@data-testid, 'socialContext'))]",
        )
        post_id = body.get_attribute("id")
        post_body = body.text
        store_posts.delay(channel_id, post_id, post_body)
    driver.quit()
