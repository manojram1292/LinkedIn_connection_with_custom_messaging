from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import parameters, csv, os.path, time

# Function to handle clicking elements using JavaScript
def find_and_click_element(driver, by, value):
    try:
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((by, value))
        )
        driver.execute_script("arguments[0].click();", element)  # Using JavaScript to click to avoid any Selenium click issues.
        return True
    except Exception as e:
        print(f"Failed to find or click element with locator {value}: {str(e)}")
        return False

# Function to handle the connection requests
def search_and_send_request(driver, keywords, start_page, till_page, writer, ignore_list=[]):
    for page in range(start_page, start_page + till_page):
        print('\nINFO: Checking on page %s' % (page))
        query_url = f'https://www.linkedin.com/search/results/people/?keywords={keywords}&origin=GLOBAL_SEARCH_HEADER&page={page}'
        driver.get(query_url)
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'reusable-search__result-container')))
        linkedin_urls = driver.find_elements(By.CLASS_NAME, 'reusable-search__result-container')
        print('INFO: %s connections found on page %s' % (len(linkedin_urls), page))
        for index, result in enumerate(linkedin_urls, start=1):
            name = result.text.split('\n')[0]
            if name in ignore_list or name.strip() in ignore_list:
                print("%s ) IGNORED: %s" % (index, name))
                continue
            connection = result.find_element(By.CLASS_NAME, 'artdeco-button__text')
            if connection.text == 'Connect':
                connection.click()
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Add a note']")))
                driver.find_element(By.XPATH, "//button[@aria-label='Add a note']").click()
                WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, 'custom-message')))
                message_box = driver.find_element(By.ID, 'custom-message')
                message_box.send_keys(parameters.custom_message)
                if not find_and_click_element(driver, By.XPATH, "//button[@aria-label='Send invitation']"):
                    print(f"{index} ) Failed to send to {name}")
                    writer.writerow([name, 'Failed'])
                else:
                    print(f"{index} ) Invitation sent to {name}")
                    writer.writerow([name, 'Sent'])
            else:
                print(f"{index} ) Connection not available for {name}")
                writer.writerow([name, 'Unavailable'])
        time.sleep(5)

# Main script execution block
try:
    options = Options()
    options.add_argument("--disable-notifications")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get('https://www.linkedin.com/login')
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'username'))).send_keys(parameters.linkedin_username)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(parameters.linkedin_password)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@type="submit"]'))).click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'global-nav-typeahead')))
    
    file_name = parameters.file_name
    file_exists = os.path.isfile(file_name)
    writer = csv.writer(open(file_name, 'a', newline=''))
    if not file_exists:
        writer.writerow(['Connection Name', 'Status'])
    ignore_list = parameters.ignore_list.split(',') if parameters.ignore_list else []
    search_and_send_request(driver, parameters.keywords, parameters.start_page, parameters.till_page, writer, ignore_list)
except Exception as e:
    error_message = str(e)
    if "GetHandleVerifier" in error_message:
        print('Limit Reached')
    else:
        print('ERROR: Unable to run, error -', error_message)
finally:
    driver.quit()
