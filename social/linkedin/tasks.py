import time
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from celery import shared_task

from network import models as net_models

driver = None


@shared_task(name="login")
def login():
    driver = webdriver.Remote(
        "http://social_firefox:4444/wd/hub",
        DesiredCapabilities.FIREFOX,
    )
    email = "mahsa.jafari2003@gmail.com"
    password = "nHdkuVm1fi"
    driver.get("https://www.linkedin.com/login")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username")))
    email_elem = driver.find_element_by_id("username")
    email_elem.send_keys(email)
    password_elem = driver.find_element_by_id("password")
    password_elem.send_keys(password)
    password_elem.submit()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "global-nav-search"))
    )

    pickle.dump(driver.get_cookies(), open("social/cookies.pkl", "wb"))


@shared_task(name="get_company_info")
def get_company_info(channel_id):
    channel = net_models.Channel.objects.get(pk=channel_id)
    company_url = channel.username
    driver = webdriver.Remote(
        "http://social_firefox:4444/wd/hub",
        DesiredCapabilities.FIREFOX,
    )
    cookies = pickle.load(open("social/cookies.pkl", "rb"))
    driver.get(company_url)
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.get(company_url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//span[@dir="ltr"]'))
    )
    navigation = driver.find_element_by_class_name("org-page-navigation__items ")
    name = driver.find_element_by_xpath('//span[@dir="ltr"]').text.strip()
    print(name)
    time.sleep(5)
    posts = driver.find_elements_by_class_name("break-words")
    print(len(posts))
    for post in posts:
        if not net_models.Post.objects.filter(body=post.text).exists():
            net_models.Post.objects.create(body=post.text, channel=channel)
        print(post.text)
    driver.close()
