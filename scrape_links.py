# facebook marketplace
from time import sleep
import sys
from selenium import webdriver
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import pymysql
import config

account_id = 0

def dbConnect():
    try:
        conn = pymysql.connect(host=config.HOST, user=config.USER,
                               db=config.DB, passwd=config.PASS, connect_timeout=5)
        return conn
    except pymysql.MySQLError as e:
        print("ERROR: Unexpected error: Could not connect to MySQL instance.")
        print(e)
        sys.exit()


def getDriver():
    opts = FirefoxOptions()
    opts.add_argument("--headless")
    driver = webdriver.Firefox(firefox_options=opts)
    return driver


def log_in():
    try:
        driver.get(config.MAIN_URL)
        sleep(2)
        email, password = config.ACCOUNTS[account_id]
        email_input = driver.find_element_by_id("email")
        email_input.send_keys(email)
        sleep(0.5)
        password_input = driver.find_element_by_id("pass")
        password_input.send_keys(password)
        sleep(0.5)
        login_button = driver.find_element_by_xpath("//*[@type='submit']")
        login_button.click()
        print("Successfully logged in! (sleep for 3 secs)")
        sleep(3)
    except Exception as e:
        print('Some exception occurred while trying to find username or password field')
        print(e)


def scrape_item_links(category):
    marketplace_button = driver.find_element_by_xpath(
        '//span[contains(text(), "Marketplace")]')
    marketplace_button.click()
    # wait until new page loaded
    sleep(5)
    element = driver.find_element_by_xpath(
        '//span[contains(text(), "{}")]'.format(category))
    element.click()
    driver.implicitly_wait(5)
    print("scrolling")
    for _ in range(100):
        try:
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")
            sleep(1)
        except:
            print("exception while scroll")
            pass
    items_wrapper_list = driver.find_elements_by_xpath(
        "//div[contains(@class, 'kbiprv82')]")
    full_items_list = [wrapper.find_element_by_tag_name(
        'a') for wrapper in items_wrapper_list]

    for item in full_items_list:
        url = item.get_attribute('href')
        url = url.split('?')[0]
        
        try:
            with dbclient.cursor() as cur:
                sql = "INSERT INTO link (url, category) VALUES('{}', '{}')".format(
                    url, category)
                cur.execute(sql)
                dbclient.commit()
                pid = cur.lastrowid
                print("Insert link: {}".format(pid))
        except pymysql.MySQLError as e:
            print("ERROR when insert")
            print(e)


if __name__ == '__main__':
    categories = ["Vehicles", "Entertainment",
                  "Clothing", "Electronics", "Office supplies"]

    dbclient = dbConnect()
    driver = getDriver()
    log_in()
    for category in categories:
        print("Processing {}".format(category))
        driver.get(config.MAIN_URL)
        scrape_item_links(category)
    driver.quit()
