import time

SCROLL_PAUSE_TIME = 2


def scroll(driver, counter):
    """Scroll browser for counter times

    Args:
        driver (webdriver): webdriver object
        counter (int): specify number of scrolls
    """

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
