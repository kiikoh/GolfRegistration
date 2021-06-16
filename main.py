from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from datetime import timedelta, datetime
import time, os, logging, pathlib
from dotenv import load_dotenv
load_dotenv()

##########################################################
#                      KNOWN ISSUES                      #
# Signing up for a time slot with less than the 4 people #
##########################################################

# Configuration
# Also add login credentials to .env file
daysAhead = 14 # This should be kept constant, it signifies the days you can register ahead
startTime = 17  # 20 for 11 o'clock, incrementing one adds ten minutes, this will be the starting time
maxWindow = 8 # Amount of time slots to try in the future, the bot will try all of these in order, each ten minutes apart
names = ["Person Name1", "Person Name2"] # List of names to add to your reservation, maximum 3, less will instead fill with guests, must be registered

# Put Chromedriver on your path
driver = webdriver.Chrome()

def setupLogging():
    global directory
    datestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    directory = f"./logs/{datestamp}/"

    pathlib.Path(directory + "captures/").mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        filename=directory + 'registration.log', 
        level=logging.INFO,
        format='%(asctime)s %(levelname)-8s %(message)s', 
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logging.info("Program started...")

def waitUntilHour(hour):
    t = datetime.today()
    future = datetime(t.year, t.month, t.day, hour, 0)
    sleepTime = (future-t).total_seconds()

    logging.warning(f'Waiting {sleepTime} seconds until {future.strftime("%I:%M %p")}')

    if(sleepTime < 0):
        logging.info("Bypassing waiting, already past 4 PM")
        return
    time.sleep(sleepTime)

def start():
    global startTime
    setupLogging()
    login(os.environ["USER"], os.environ["PASSWORD"])

    waitUntilHour(4 + 12)  # Waits until the next 4 PM(+12 hours)
    # Retries whole process from the login page if it somehow fails
    for attempt in range(5):
        try:
            driver.get("https://newjerseynational.clubhouseonline-e3.com/TeeTimes/TeeSheet.aspx")
            time.sleep(1)

            chooseDate()
            time.sleep(2)

            for _ in range(startTime, maxWindow + startTime):
                logging.info(startTime)
                logging.info(_)
                try:
                    chooseTime()
                    startTime += 1
                    break
                except NoSuchElementException:
                    logging.warning(f"Trying next available time slot... ({_})")
                    startTime += 1
                    continue
            time.sleep(2)

            for name in names:
                driver.execute_script("window.scrollBy(0, 300)")
                addMember(name)
            for i in range(3 - len(names)):
                driver.execute_script("window.scrollBy(0, 300)")
                addGuest()

            # Place the reservation
            driver.find_element_by_css_selector(
                "#form1 > div.inner-wrap > div.container > div > div > div > div.main-content.ng-scope > div > div.content.row > div.col-sm-7.section-2 > div > div.row > div > div > a").click()
            logging.info("Successfully registered time.")
            break
        except Exception as e:
            location = f"{directory}captures/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
            driver.save_screenshot(location)
            logging.error(f"Saving screengrab to {location}")
            logging.error(e)
            logging.error(f"Error registering, retrying again ({attempt})")

            time.sleep(2)
            continue
    time.sleep(120)
    driver.quit()


def login(username, password):
    driver.get("https://newjerseynational.clubhouseonline-e3.com/login.aspx")
    driver.find_element_by_id(
        "p_lt_PageContent_pageplaceholder_p_lt_zoneLeft_CHOLogin_LoginControl_ctl00_Login1_UserName").send_keys(username)
    driver.find_element_by_id(
        "p_lt_PageContent_pageplaceholder_p_lt_zoneLeft_CHOLogin_LoginControl_ctl00_Login1_Password").send_keys(password)
    driver.find_element_by_id(
        "p_lt_PageContent_pageplaceholder_p_lt_zoneLeft_CHOLogin_LoginControl_ctl00_Login1_LoginButton").click()
    logging.info("Login Successful")


def chooseDate():
    now = datetime.now()
    diff = timedelta(14)
    dayToUse = (now+diff).strftime("%b %d")
    driver.switch_to.frame("module")
    driver.find_element_by_css_selector(
        "#form1 > div.inner-wrap > div.container > div > div > div > div.main-content.ng-scope > div > div.date-selector.ng-isolate-scope > button.next.custom-arrow").click()
    driver.find_element_by_css_selector(
        "#form1 > div.inner-wrap > div.container > div > div > div > div.main-content.ng-scope > div > div.date-selector.ng-isolate-scope > button.next.custom-arrow").click()
    
    driver.execute_script("document.evaluate(`//*[contains(text(), '{}')]`, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click()".format(dayToUse))
	
    driver.execute_script("window.scrollBy(0, 100)")
    logging.info("Successfully selected date")


def chooseTime():
    driver.find_element_by_css_selector(
        "#form1 > div.inner-wrap > div.container > div > div > div > div.main-content.ng-scope > div > div.teesheet-scheduler.ng-scope.ng-isolate-scope > div:nth-child(" + str(startTime) + ") > div > div.teesheet-midcol > div.teesheet-midcol-bot > div.quickbook.ng-scope > a").click()
    driver.find_element_by_css_selector(
        "#form1 > div.inner-wrap > div.container > div > div > div > div.main-content.ng-scope > div > div.teesheet-scheduler.ng-scope.ng-isolate-scope > div:nth-child(" + str(startTime) + ") > div > div.teesheet-midcol > div.teesheet-midcol-bot > div.quickbook.ng-scope.active > div > ul > li > a").click()

def addMember(memberName):
    driver.find_element_by_css_selector(
        "#form1 > div.inner-wrap > div.container > div > div > div > div.main-content.ng-scope > div > div.content.row > div.col-sm-7.section-2 > div > div.reservation.ng-scope > span:nth-child(4) > span > span > div > div:nth-child(1) > div:nth-child(1)").click()
    time.sleep(2)
    driver.find_element_by_css_selector(
        "#form1 > div.inner-wrap > div.container > div > div > div > div.main-content.ng-scope > div > div.ng-scope.overlay > div > div.header.row.mar-none > div.col-xs-8 > div > input").send_keys(memberName)
    time.sleep(2)
    driver.find_element_by_css_selector(
        "#form1 > div.inner-wrap > div.container > div > div > div > div.main-content.ng-scope > div > div.ng-scope.overlay > div > div.content > div.row > div > div > i").click()
    logging.info(f"Added Member {memberName}")
    time.sleep(2)

def addGuest():
    driver.find_element_by_css_selector(
        "#form1 > div.inner-wrap > div.container > div > div > div > div.main-content.ng-scope > div > div.content.row > div.col-sm-7.section-2 > div > div.reservation.ng-scope > span:nth-child(4) > span > span > div > div:nth-child(1) > div.col-sm-4.link.ng-scope > a").click()
    time.sleep(1)
    # First
    driver.find_element_by_css_selector(
        "#form1 > div.inner-wrap > div.container > div > div > div > div.main-content.ng-scope > div > div.ng-scope.overlay > div > div.content > ng-form > div > div:nth-child(2) > input").send_keys("Guest")
    time.sleep(1)
    #Last
    driver.find_element_by_css_selector(
        "#form1 > div.inner-wrap > div.container > div > div > div > div.main-content.ng-scope > div > div.ng-scope.overlay > div > div.content > ng-form > div > div:nth-child(3) > input").send_keys("Guest")
    time.sleep(1)
    driver.find_element_by_css_selector(
        "#form1 > div.inner-wrap > div.container > div > div > div > div.main-content.ng-scope > div > div.ng-scope.overlay > div > div.content > ng-form > div > div:nth-child(5) > p > a").click()
    logging.info("Added Guest")
    time.sleep(2)

start()
