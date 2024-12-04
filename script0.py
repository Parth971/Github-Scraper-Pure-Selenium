"""
There are three parameters to set:
1. `links_to_download = None`
# a. set integer to download specific number of links
# b. Set None to download all links

2. Initial Link
LINK = 'https://github.com/Parth971'

3. Ban Waiting Time: time to wait until we request for next link
ban_waiting_time = 30
"""

from functools import partial
import json
import logging
import os
import pathlib
import re
from logging.handlers import RotatingFileHandler
import subprocess

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_DIR = pathlib.Path(__file__).parent.resolve()

if not os.path.exists(BASE_DIR / "outputs"):
    os.mkdir("outputs")

log_file = BASE_DIR / "outputs/scraping_links.log"

root_logger = logging.getLogger(__name__)
root_logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

rotating_file_log = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=1)
rotating_file_log.setFormatter(formatter)

console_log = logging.StreamHandler()
console_log.setLevel(logging.INFO)
console_log.setFormatter(formatter)

root_logger.addHandler(rotating_file_log)
root_logger.addHandler(console_log)


class UrlParser:
    def __init__(self, domain):
        self.domain = domain

    def get_parser_name_from_url(self, url):
        domain = self.domain
        url = url if url[-1] != "/" else url[:-1]
        search_prefix = domain + "search?"

        if url[: len(search_prefix)] == search_prefix:
            if "type=issues" in url or "type=Issues" in url:
                return "search_issue_result", url
            elif "type=discussions" in url or "type=Discussions" in url:
                return "search_discussion_result", url
            elif "type=wikis" in url or "type=Wikis" in url:
                return "search_wikis_result", url
            elif "type=commits" in url or "type=Commits" in url:
                return "search_commit_result", url
            return "search_repositories_result", url

        if url[: len(domain)] == domain:
            organization_patterns = [
                # https://github.com/orgs/drivendataorg/repositories
                # https://github.com/orgs/drivendataorg/repositories/
                # https://github.com/orgs/drivendataorg/repositories?page=3
                (
                    "main",
                    "^https:\/\/github\.com\/orgs\/[^\/]+\/repositories\/?(\?page=\d+)?$",
                ),
                # https://github.com/drivendataorg
                # https://github.com/drivendataorg/
                ("main", "^https:\/\/github\.com\/[^\/]+\/?$"),
                # https://github.com/abhisheknaiidu/awesome-github-profile-readme
                # problem : /topics/portfolio also matches
                ("repo", "^https:\/\/github\.com\/[A-Za-z0-9-]+\/[A-Za-z0-9-]+$"),
            ]
            for name, pattern in organization_patterns:
                if re.match(pattern, url):
                    return name, url

        message = f"Url: {url} is not Valid! Maybe you have scraped all repositories OR your input url is incorrect."
        root_logger.warning(message)
        return None, None


class SeleniumWebDriver:
    def __init__(self, download_path):
        self.web_driver = None
        self.download_path = download_path

    def get_webdriver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_experimental_option(
            "prefs", {"download.default_directory": self.download_path}
        )

        self.web_driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )
        return self.web_driver


class Utility:
    @staticmethod
    def get_start_url(output_meta_path):
        if os.path.exists(output_meta_path):
            with open(output_meta_path, "r") as openfile:
                data = json.load(openfile)
            return data

    @staticmethod
    def save_meta(
        current_page_link, downloaded_repo_link, last_file_number, meta_file_path
    ):
        data = {
            "current_page_link": current_page_link,
            "downloaded_repo_links": [downloaded_repo_link],
            "last_file_number": last_file_number,
        }
        if os.path.exists(meta_file_path):
            with open(meta_file_path, "r") as openfile:
                data = json.load(openfile)

            data["current_page_link"] = current_page_link
            data["downloaded_repo_links"].append(downloaded_repo_link)
            data["last_file_number"] = last_file_number

        with open(meta_file_path, "w") as outfile:
            json.dump(data, outfile)

    @staticmethod
    def downloaded_link(link, downloaded_link_file_path, number):
        with open(downloaded_link_file_path, "a") as file:
            file.write(f"{number} {link}\n")

    @staticmethod
    def empty_meta_file(current_page_link, meta_file_path):

        with open(meta_file_path, "r") as openfile:
            data = json.load(openfile)

        data["current_page_link"] = current_page_link
        data["downloaded_repo_links"] = []

        with open(meta_file_path, "w") as outfile:
            json.dump(data, outfile)


class GetGitHubLinks:
    github_domain = "https://github.com/"
    output_meta_path = BASE_DIR / "outputs/meta.json"
    downloaded_link_file_path = BASE_DIR / "outputs/collected_links.txt"
    webdriver_waiting_time = 10

    def __init__(
        self, download_path, total_links_to_download, initial_link, banned_waiting_time
    ):
        root_logger.debug("\n\nStarted getting GitHub repository links...")
        self.wd = SeleniumWebDriver(download_path=download_path).get_webdriver()
        self.total_links_to_download = total_links_to_download
        self.initial_link = initial_link
        self.banned_waiting_time = banned_waiting_time
        self.first_time = True

    def banned(self):
        try:
            self.wd.find_element(By.XPATH, "//title[contains(text(),'Rate limit')]")
            return True
        except NoSuchElementException:
            return False

    def run(self):

        def as_it_is(param):
            return param

        def remove_last_value(param):
            return "/".join(param.split("/")[:-1])

        callbacks_list = {
            "main": {
                "repository_page_xpath": '//*[@data-tab-item="org-header-repositories-tab"]/a | //a[@data-tab-item="repositories"]',
                "element_xpath": '//*[@id="user-repositories-list"]/ul/li/div/div/h3/a[@href] | //*[@id="org-repositories"]//ul/li/div/div/div/h3/a[@href]',
                "href_wrapper": as_it_is,
            },
            "search_repositories_result": {
                "element_xpath": '//div[contains(@class, "search-title")]/a[@href]',
                "href_wrapper": as_it_is,
            },
            "search_issue_result": {
                "element_xpath": '//div[@data-testid="results-list"]/div/h3/div[2]/a[@href][1]',
                "href_wrapper": lambda x: remove_last_value(remove_last_value(x)),
            },
            "search_discussion_result": {
                "element_xpath": '//div[@id="discussion_search_results"]/div[1]/div/div[1]/div[1]/a[@href][1]',
                "href_wrapper": remove_last_value,
            },
            "search_wikis_result": {
                "element_xpath": '//div[@id="wiki_search_results"]/div[1]/div/a[@href][1]',
                "href_wrapper": as_it_is,
            },
            "search_commit_result": {
                "element_xpath": '//div[@id="commit_search_results"]/div/div/div[1]/a[@href][1]',
                "href_wrapper": as_it_is,
            },
        }

        starting_number = 1
        downloaded_repo_links = None

        data = Utility.get_start_url(GetGitHubLinks.output_meta_path)

        if data:
            self.first_time = False
            url = data["current_page_link"]
            starting_number = data["last_file_number"] + 1
            downloaded_repo_links = data["downloaded_repo_links"]
        else:
            url = self.initial_link

        key, url = UrlParser(
            domain=GetGitHubLinks.github_domain
        ).get_parser_name_from_url(url)

        message = f"Starting URL ::: {url}"
        root_logger.info(message)

        message = f"Key for URL ::: {key}"
        root_logger.debug(message)

        if key == "repo":
            if downloaded_repo_links and downloaded_repo_links[0] == url:
                root_logger.info(f"{url} already downloaded")
                return
            Utility.save_meta(
                url, url, starting_number, GetGitHubLinks.output_meta_path
            )
            Utility.downloaded_link(
                url, GetGitHubLinks.downloaded_link_file_path, starting_number
            )
            root_logger.info("###################### All Done ######################")
            return

        meta_data = callbacks_list[key]

        self.wd.get("chrome://downloads")

        time.sleep(2)

        self.parse(
            url=url,
            starting_number=starting_number,
            downloaded_repo_links=downloaded_repo_links,
            meta_data=meta_data,
        )

        root_logger.info("###################### All Done ######################")

    def parse(self, url, starting_number, downloaded_repo_links, meta_data):
        root_logger.info(f"Scraping page url ::: {url}")

        self.wd.execute_script("window.open()")
        self.wd.switch_to.window(self.wd.window_handles[-1])
        self.wd.get(url)

        if self.banned():
            root_logger.info(
                f"######### BANNED FOR {self.banned_waiting_time}SEC #########"
            )

            time.sleep(self.banned_waiting_time)
            self.wd.switch_to.window(self.wd.window_handles[-1])
            self.wd.close()
            self.wd.switch_to.window(self.wd.window_handles[-1])
            return self.parse(url, starting_number, downloaded_repo_links, meta_data)

        if self.first_time and meta_data.get("repository_page_xpath"):
            self.first_time = False
            element_xpath = meta_data["repository_page_xpath"]
            element = WebDriverWait(
                self.wd, GetGitHubLinks.webdriver_waiting_time
            ).until(EC.presence_of_all_elements_located((By.XPATH, element_xpath)))
            element[0].click()

        element = meta_data["element_xpath"]
        WebDriverWait(self.wd, GetGitHubLinks.webdriver_waiting_time).until(
            EC.presence_of_all_elements_located((By.XPATH, element))
        )
        repositories = self.wd.find_elements(By.XPATH, element)

        href_wrapper = meta_data["href_wrapper"]

        res = [href_wrapper(elem.get_attribute("href")) for elem in repositories]
        root_logger.debug(f"Found links on page ::: {len(res)} ")

        if downloaded_repo_links:
            root_logger.debug(f"Found old links ::: {len(downloaded_repo_links)} ")
            for repo in downloaded_repo_links:
                if repo in res:
                    res.remove(repo)
            root_logger.debug(f"Remaining links ::: {len(res)} ")

        next_page = None
        element = '//a[@class="next_page"] | //a[text()="Next"]'
        try:
            next_page = self.wd.find_element(By.XPATH, element).get_attribute("href")
        except NoSuchElementException:
            pass

        self.wd.switch_to.window(self.wd.window_handles[-1])
        self.wd.close()
        self.wd.switch_to.window(self.wd.window_handles[-1])

        for repository_url in res:

            if (
                self.total_links_to_download
                and starting_number > self.total_links_to_download
            ):
                return
            Utility.save_meta(
                url, repository_url, starting_number, GetGitHubLinks.output_meta_path
            )
            Utility.downloaded_link(
                repository_url,
                GetGitHubLinks.downloaded_link_file_path,
                starting_number,
            )
            starting_number += 1

        if next_page:
            time.sleep(3)
            Utility.empty_meta_file(next_page, GetGitHubLinks.output_meta_path)
            self.parse(next_page, starting_number, None, meta_data)


if __name__ == "__main__":
    path = str(BASE_DIR / "RepoDownloads")

    # 1. set integer to download specific number of links
    # 2. Set None to download all links
    links_to_download = None

    # Initial Link
    LINK = "https://github.com/search?q=favorita+grocery&type=issues"

    ban_waiting_time = 30

    GetGitHubLinks(
        download_path=path,
        total_links_to_download=links_to_download,
        initial_link=LINK,
        banned_waiting_time=ban_waiting_time,
    ).run()


subprocess.run(["pip", "install", "selenium"], capture_output=True)
