import sys
from random import randint
from time import sleep
from selenium import webdriver
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

import pymysql
import config
from xpaths import xpath 

TEST = False
dbclient = ""
driver = ""
proxy_list = []
account_id = 0

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

# called when account is banned
def switch_account():
    print("switch account")
    global account_id, dbclient
    account_id += 1
    if account_id >= 3:
        account_id = 0
        # all account banned, sleep half an hour
        print("All account blocked, long sleep 30 min")
        sleep(60*30)
    initDriver()
    log_in()    
    dbclient = dbConnect() # reconnecting mysql

def dbConnect():
    try:
        conn = pymysql.connect(host=config.HOST, user=config.USER,
                               db=config.DB, passwd=config.PASS, connect_timeout=5)
        return conn
    except pymysql.MySQLError as e:
        print("ERROR: Unexpected error: Could not connect to MySQL instance.")
        print(e)
        sys.exit()

def driverOption():
    opts = FirefoxOptions()
    opts.add_argument("--headless") 
    # optimization
    opts.add_argument("start-maximized")
    opts.add_argument("disable-infobars")
    opts.add_argument("--disable-extensions")
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-application-cache')
    opts.add_argument('--disable-gpu')
    opts.add_argument("--disable-dev-shm-usage")
    return opts

def initDriver():
    global driver
    if driver!="":
        driver.quit()
    opts = driverOption()
    driver = webdriver.Firefox(firefox_options=opts)

def updateDriver():
    global proxy_list, driver
    while len(proxy_list) == 0:
        proxy_list = get_free_proxies()
        print("Fetch proxy list: {}".format(len(proxy_list)))
    proxy = proxy_list.pop()
    proxy_str = "{}:{}".format(proxy['IP Address'], proxy['Port'])
    print("Using proxy: {}".format(proxy_str))

    driver.quit()
    opts = driverOption()
    opts.add_argument('--proxy-server=%s' % proxy_str)    
    try:
        driver = webdriver.Firefox(firefox_options=opts)
    except Exception as e:
        print("exception {}".format(str(e)))
    if not driver:
        initDriver()

def get_free_proxies():
    driver.get('https://sslproxies.org')

    table = driver.find_element(By.TAG_NAME, 'table')
    thead = table.find_element(By.TAG_NAME, 'thead').find_elements(By.TAG_NAME, 'th')
    tbody = table.find_element(By.TAG_NAME, 'tbody').find_elements(By.TAG_NAME, 'tr')

    headers = []
    for th in thead:
        headers.append(th.text.strip())

    proxies = []
    for tr in tbody:
        proxy_data = {}
        tds = tr.find_elements(By.TAG_NAME, 'td')
        for i in range(len(headers)):
            proxy_data[headers[i]] = tds[i].text.strip()
        proxies.append(proxy_data)
    
    return proxies

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
        title = driver.title
        print(title)
        if title == "Facebook":
            print("Account blocked")
            title = ""
            switch_account()       
        if "Log into Facebook" in title or "Facebook - Log In or Sign Up" in title:
            title = ""
            log_in()
        else:            
            title = title.replace("| Facebook", "")
            title = title.replace("Marketplace – ", "")            
    except Exception as e:
        print("exception {}".format(str(e)))
    # try:
    #     WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, '//div[(@class="dati1w0a qt6c0cv9 hv4rvrfc discj3wi")]/div/span')))
    # except TimeoutException as e:
    #     print("exception {}".format(str(e)))      
    return title


def getLocation(category):
    location = ""
    try:
        location = driver.find_element_by_xpath(xpath[category]["Location"]).text
    except Exception as e:
        print("exception {}".format(str(e)))
        location = ""
    return location


def getPrice(category):
    price = ""
    try:
        price = driver.find_element_by_xpath(xpath[category]["Price"]).text
    except Exception as e:
        print("exception {}".format(str(e)))
        price = ""
    return price


def getTime():
    date_time = ""
    return date_time


def getDescription(category):
    global driver
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
        spans = driver.find_elements_by_xpath(xpath[category]["Description"])
        descriptions = [span.text for span in spans]
        description = "/n".join(descriptions)
    except Exception as e:
        print("exception {}".format(str(e)))
        description = ""
    return description


def scrape_item_details(pid, link):
    global driver
    print("[pid: {}]: {}".format(pid, link))
    try:
        driver.get(link)
        # wait until the title shows
    except Exception as e:
        print("Exception while try to get link (Product expired or IP banned) {}".format(str(e)))
        return
    
    # avoid SQL parse error
    title = getTitle().replace("'", " ")
    if title == "":
        print("[WARNING]: title is empty, there might be problem with the xpath")
        return

    date_time = getTime().replace("'", " ")
    location = getLocation(category).replace("'", " ")
    price = getPrice(category).replace("'", " ")
    description = getDescription(category).replace("'", " ")
    
    images = getImages()

    if TEST:
        print({'Url': link, 'Images': images, 'Title': title, 'Description': description,
              'Date_Time': date_time, 'Location': location, 'Price': price})
    else:
        try:
            with dbclient.cursor() as cur:
                sql = "INSERT INTO product (pid, title, description, time, location, price) VALUES('{}','{}','{}','{}','{}','{}')".format(
                    pid, title, description, date_time, location, price)
                # print(sql)
                cur.execute(sql)
                dbclient.commit()
                print("title: {}\nprice: {}\ndescription: {}\nlocation: {}\nimages: {}".format(title, price, description, location, len(images)))
                for imgUrl in images:
                    cur.execute(
                        "INSERT INTO image (pid, url) VALUES('{}','{}')".format(pid, imgUrl))
        except pymysql.MySQLError as e:
            print("Error while insert product/image: ")
            print(e)


def getNewLinks(category, n):
    try:
        with dbclient.cursor() as cur:
            sql = "SELECT link.pid, link.url FROM link WHERE link.category='{}' AND pid NOT IN (SELECT pid FROM product) ORDER BY pid DESC LIMIT {}".format(
                category, n)
            cur.execute(sql)
            results = cur.fetchall()
            print("find {} new links for {}".format(len(results), category))
            return results
    except pymysql.MySQLError as e:
        print("Error while finding link:")
        print(e)


if __name__ == '__main__':
    categories = ["Electronics", "Office supplies", "Vehicles" "Clothing", "Entertainment"]
    
    dbclient = dbConnect()

    while len(categories) > 0:     
        initDriver()
        log_in()   
        for category in categories:            
            links = getNewLinks(category, 50)
            if not links or len(links) == 0:
                categories.remove(category)
                continue
            for pid, link in links:
                sleep(randint(10,20))
                # link = "https://api.zenrows.com/v1/?apikey=bdce47f93fe5b3578fe888adb8b1be09079ad874&url="+link
                scrape_item_details(pid, link)
            # free memory
        driver.close()
        # update proxy
        # updateDriver()
        # log_in()  
    print("All tasks finished!")
    driver.quit()                  
    # testurl = "https://www.facebook.com/marketplace/item/352410700144018/?ref=category_feed&referral_code=marketplace_search&referral_story_type=listing&tracking=%7B%22qid%22%3A%22-6579031794026474711%22%2C%22mf_story_key%22%3A%224818493831537129%22%2C%22commerce_rank_obj%22%3A%22%7B%5C%22target_id%5C%22%3A4818493831537129%2C%5C%22target_type%5C%22%3A0%2C%5C%22primary_position%5C%22%3A1373%2C%5C%22ranking_signature%5C%22%3A855142844925476864%2C%5C%22commerce_channel%5C%22%3A504%2C%5C%22value%5C%22%3A1.5007731631484e-7%7D%22%7D"
    # scrape_item_details(1, testurl)