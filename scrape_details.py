# facebook marketplace
from time import sleep
import sys
from pymysql import NULL
from selenium import webdriver
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import pymysql
import config

TEST = False
dbclient = NULL
driver = NULL


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


def getImages():
    images = []
    try:
        image_elements = driver.find_elements_by_xpath(
            '//div[contains(@class, "nhd2j8a9 tv7at329 thwo4zme")]/img')
        images = [element.get_attribute('src') for element in image_elements]
    except Exception as e:
        print("exception {}".format(str(e)))
        images = ""
    return images


def getTitle():
    title = ""
    try:
        title_span = driver.find_element_by_xpath(
            '//div[(@class="dati1w0a qt6c0cv9 hv4rvrfc discj3wi")]/div/span')
        title = title_span.text
    except Exception as e:
        print("exception {}".format(str(e)))
        title = ""
    if title == "":
        print("[WARNING]: title is empty, there might be problem with the xpath")
    return title


def getLocation():
    location = ""
    try:
        location = driver.find_element_by_xpath(
            '//div[(@class="sjgh65i0")]/div/span').text
    except Exception as e:
        print("exception {}".format(str(e)))
        location = ""
    return location


def getPrice():
    price = ""
    try:
        price = driver.find_element_by_xpath(
            "//div[(@class='aov4n071')]/div/span").text
    except Exception as e:
        print("exception {}".format(str(e)))
        price = ""
    return price


def getTime():
    date_time = ""
    # try:
    #     date_time = driver.find_element_by_xpath('//a[@class="_r3j"]').text
    # except Exception as e:
    # print("exception {}".format(str(e)))
    #     date_time = ""
    return date_time


def getDescription():
    description = ""
    spans = []
    # seeMore = driver.find_element_by_xpath("//span[contains(text(),'See More')]")
    # description_wrapper = driver.find_element_by_xpath("//span[contains(text(),'See More')]/../..")
    try:
        #     if seeMore.is_displayed():
        #         # seeMore.click()
        #         # driver.execute_script("arguments[0].scrollIntoView();", element)
        #         # description = driver.find_element_by_xpath("//span[contains(text(),'See Less')]").text
        #         description = description_wrapper.text
        #     else:
        spans = driver.find_elements_by_xpath(
            '//div[@class="n851cfcs"]/div[@class="aahdfvyu"]/div/div/div/span')
        descriptions = [span.text for span in spans]
        description = "/n".join(descriptions)
    except Exception as e:
        print("exception {}".format(str(e)))
        description = ""
    return description


def scrape_item_details(pid, link, section):
    try:
        driver.get(link)
    except Exception as e:
        print("Exception while try to get link (Product may have expired){}".format(str(e)))
        return

    sleep(1)
    images = getImages()
    # avoid SQL parse error
    title = getTitle().replace("'", " ")
    date_time = getTime().replace("'", " ")
    location = getLocation().replace("'", " ")
    price = getPrice().replace("'", " ")
    description = getDescription().replace("'", " ")
    if TEST:
        print({'Url': link, 'Images': images, 'Title': title, 'Description': description,
              'Date_Time': date_time, 'Location': location, 'Price': price})
    try:
        with dbclient.cursor() as cur:
            sql = "INSERT INTO product (title, description, time, location, price) VALUES('{}','{}','{}','{}','{}')".format(
                title, description, date_time, location, price)
            # print(sql)
            cur.execute(sql)
            dbclient.commit()
            print("[{}]: {}".format(pid, title))
            for imgUrl in images:
                cur.execute(
                    "INSERT INTO image (pid, url) VALUES('{}','{}')".format(pid, imgUrl))
    except pymysql.MySQLError as e:
        print("Error while inser product/image: ")
        print(e)


def getNewLinks(category, n):
    try:
        with dbclient.cursor() as cur:
            sql = "SELECT link.pid, link.url FROM link WHERE link.category='{}' AND pid NOT IN (SELECT pid FROM product) LIMIT {}".format(
                category, n)
            cur.execute(sql)
            results = cur.fetchall()
            print("find {} new links for {}".format(len(results), category))
            return results
    except pymysql.MySQLError as e:
        print("Error while finding link:")
        print(e)


if __name__ == '__main__':
    categories = ["Vehicles", "Entertainment",
                  "Clothing", "Electronics", "Office supplies"]

    dbclient = dbConnect()
    driver = getDriver()
    while True:
        for category in categories:
            links = getNewLinks(category, 100)
            for pid, link in links:
                scrape_item_details(pid, link, category)
