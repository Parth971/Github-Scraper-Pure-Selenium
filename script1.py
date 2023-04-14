import logging
import os
import pathlib
import re
import time

from selenium import webdriver
from logging.handlers import RotatingFileHandler

from selenium.common import JavascriptException, TimeoutException, NoSuchWindowException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC

BASE_DIR = pathlib.Path(__file__).parent.resolve()

log_file = BASE_DIR / 'outputs/downloading_links.log'

root_logger = logging.getLogger(__name__)
root_logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

rotating_file_log = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=1)
rotating_file_log.setFormatter(formatter)

console_log = logging.StreamHandler()
console_log.setLevel(logging.INFO)
console_log.setFormatter(formatter)

root_logger.addHandler(rotating_file_log)
root_logger.addHandler(console_log)


class Utils:
    @staticmethod
    def get_failed_links_count():
        failed_link_file_path = BASE_DIR / 'outputs/failed_link.txt'
        if os.path.exists(failed_link_file_path):
            with open(failed_link_file_path, 'r') as file:
                return len(set(file.readlines()))
        return 0

    @staticmethod
    def get_collected_links_count():
        collected_link_file_path = BASE_DIR / 'outputs/collected_links.txt'
        if os.path.exists(collected_link_file_path):
            with open(collected_link_file_path, 'r') as file:
                return len(file.readlines())
        return 0

    @staticmethod
    def get_downloaded_links_count():
        downloaded_links_file_path = BASE_DIR / 'outputs/downloaded_link.txt'
        if os.path.exists(downloaded_links_file_path):
            with open(downloaded_links_file_path, 'r') as file:
                return len(file.readlines())
        return 0

    @staticmethod
    def save_failed_link(current_page_link, starting_number):
        failed_link_file_path = BASE_DIR / 'outputs/failed_link.txt'
        with open(failed_link_file_path, 'a') as file:
            file.write(f'{starting_number} {current_page_link}\n')

    @staticmethod
    def rename_file(old_file_name, new_file_name, file_number):
        try:
            old_name = BASE_DIR / 'RepoDownloads' / old_file_name
            new_name = BASE_DIR / 'RepoDownloads' / f'{new_file_name}_N{file_number}.zip'
            os.rename(old_name, new_name)
            return f'{new_file_name}_N{file_number}.zip'
        except FileNotFoundError:
            pass

    @staticmethod
    def get_repository_name(url):
        url = url if url[-1] != "/" else url[:-1]
        return url.split('/')[-2] + "_" + url.split('/')[-1]

    @staticmethod
    def read_urls(file_path):
        raw_data = []
        if not os.path.exists(file_path):
            return raw_data

        with open(file_path, 'r') as file:
            for url in file.readlines():
                raw_data.append(url.strip())

        return raw_data

    @staticmethod
    def get_starting_links(collected_links_path, downloaded_link_path):
        collected_links = Utils.read_urls(file_path=collected_links_path)
        downloaded_links = Utils.read_urls(file_path=downloaded_link_path)

        if downloaded_links:
            root_logger.info(f"Found downloaded links: {len(downloaded_links)}")
            links_ = '\n'.join([i.replace(' ', ' skipping ') for i in downloaded_links])
            root_logger.info(f"links: {links_}")

        for link in downloaded_links:
            collected_links.remove(link)

        return collected_links

    @staticmethod
    def downloaded_link(link, number):
        file_path = BASE_DIR / 'outputs/downloaded_link.txt'
        with open(file_path, 'a') as file:
            file.write(f'{number} {link}\n')


class CleanUp:
    def __init__(self, downloaded_link_path):
        message = 'Started Cleanup.'
        root_logger.debug(message)

        folder_path = BASE_DIR / 'RepoDownloads'
        dir_list = os.listdir(folder_path)
        for file_name in dir_list:
            if not os.path.isdir(folder_path / str(file_name)):
                file_name = str(file_name)
                if not CleanUp.is_file_valid(file_name, downloaded_link_path):
                    message = f'Removing file : {file_name}.'
                    root_logger.info(message)

                    os.remove(folder_path / file_name)

    @classmethod
    def is_file_valid(cls, file_name, downloaded_link_path):
        pattern = r'w?_N[0-9]+.zip'

        downloaded_links = Utils.read_urls(downloaded_link_path)
        for i in range(len(downloaded_links)):
            number = downloaded_links[i].split(' ')[0]
            link = downloaded_links[i].split(' ')[1]
            link = link if link[-1] != '/' else link[:-1]
            file = f"{link.split('/')[-2]}_{link.split('/')[-1]}_N{number}.zip"
            downloaded_links[i] = file

        return bool(re.search(pattern, file_name)) and file_name in downloaded_links


class DownloadGitZips:
    def __init__(self, downloaded_link_path, download_path):
        root_logger.debug("Started downloading GitHub repository links...")
        self.downloaded_link_path = downloaded_link_path
        self.downloaded_links = Utils.read_urls(file_path=self.downloaded_link_path)
        self.wd = DownloadGitZips.get_webdriver(download_path=str(download_path))

    @classmethod
    def get_webdriver(cls, download_path):
        options = Options()
        options.add_argument("--start-maximized")
        options.add_experimental_option('prefs', {'download.default_directory': download_path})

        return webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

    def get_downloaded_filename(self):
        try:
            self.wd.switch_to.window(self.wd.window_handles[0])
        except NoSuchWindowException as e:
            print(f'Error in get_downloaded_filename: NoSuchWindowException: {e}')
            return
        time.sleep(5)
        while True:
            try:
                # get downloaded percentage
                download_percentage = self.wd.execute_script(
                    "return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector('#progress').value")
                # check if downloadPercentage is 100 (otherwise the script will keep waiting)
                if download_percentage == 100:
                    show_in_folder_option = self.wd.execute_script(
                        "return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector('#progress').parentElement.style.display")

                    while show_in_folder_option != 'none':
                        time.sleep(1)
                        show_in_folder_option = self.wd.execute_script(
                            "return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector('#progress').parentElement.style.display")
                    time.sleep(1)
                    # return the file name once the download is completed
                    return self.wd.execute_script(
                        "return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector('div#content #file-link').text")
                time.sleep(1)
            except JavascriptException as e:
                print(f'Error in get_downloaded_filename: JavascriptException: {e}')

    def download_file(self, url, file_number):
        try:
            self.wd.execute_script("window.open()")
            self.wd.switch_to.window(self.wd.window_handles[-1])
            self.wd.get(url)
            element = 'get-repo details>summary'
            WebDriverWait(self.wd, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, element))
            )
            self.wd.find_element(By.CSS_SELECTOR, element).click()

            element = '//div[@id="local-panel"]/ul/li[last()]/a'
            WebDriverWait(self.wd, 2).until(
                EC.presence_of_element_located((By.XPATH, element))
            )
            self.wd.find_element(By.XPATH, element).click()
        except JavascriptException as e:
            root_logger.info(f'Error in download_file: {e}')
            return
        except TimeoutException as e:
            root_logger.info(f'Error in download_file: {e}')
            raise TimeoutException

        file_name = self.get_downloaded_filename()
        time.sleep(2)
        self.wd.switch_to.window(self.wd.window_handles[-1])
        self.wd.close()
        self.wd.switch_to.window(self.wd.window_handles[0])

        return file_name

    def run(self, repository_urls):
        done_urls = []
        self.wd.get('chrome://downloads')

        for repository_url in repository_urls:
            starting_number, repository_url = repository_url.split(' ')

            root_logger.info(f'Downloading {repository_url} ...')

            if repository_url in self.downloaded_links + done_urls:
                root_logger.info('This url is already downloaded. Skipping...')
                Utils.downloaded_link(repository_url, starting_number)
                continue

            try:
                file_name = self.download_file(url=repository_url, file_number=starting_number)

                if file_name is None:
                    message = 'File not downloaded properly.'
                    root_logger.error(f"File downloading failed. Error: {message}")
                    Utils.save_failed_link(repository_url, starting_number)
                    continue
                
                new_file_name = Utils.get_repository_name(repository_url)
                new_file_name = Utils.rename_file(file_name, new_file_name, starting_number)

                if new_file_name is None:
                    message = 'File not downloaded properly.'
                    root_logger.error(f"File downloading failed. Error: {message}")
                    Utils.save_failed_link(repository_url, starting_number)
                    continue

                message = f'File downloaded successfully with name {new_file_name}'
                root_logger.info(message)

                Utils.downloaded_link(repository_url, starting_number)
                done_urls.append(repository_url)
            except TimeoutException:
                message = f'{repository_url} is invalid'
                root_logger.error(f"File downloading failed. Error: {message}")
                Utils.save_failed_link(repository_url, starting_number)
                
        root_logger.info('############## COMPLETED DOWNLOADING ##############')

        failed_links_count = Utils.get_failed_links_count()
        collected_links_count = Utils.get_collected_links_count()
        downloaded_links_count = Utils.get_downloaded_links_count()

        summary = f'''
########################################## SUMMARY ##########################################
collected links: {collected_links_count}
downloaded_links_count: {downloaded_links_count}
failed_links_count: {failed_links_count}
downloaded_links_count + failed_links_count : {downloaded_links_count + failed_links_count}
        '''

        root_logger.info(summary)


if __name__ == '__main__':
    collected_links_file_path = BASE_DIR / 'outputs/collected_links.txt'
    downloaded_link_file_path = BASE_DIR / 'outputs/downloaded_link.txt'
    downloaded_file_names_path = BASE_DIR / 'outputs/downloaded_file_names.txt'
    repos_download_folder_path = BASE_DIR / 'RepoDownloads'

    root_logger.debug(
        "\n\n#########################################################################################\n\n"
    )

    # This will remove all unfinished zip files
    CleanUp(downloaded_link_file_path)

    links = Utils.get_starting_links(
        collected_links_path=collected_links_file_path,
        downloaded_link_path=downloaded_link_file_path
    )
    root_logger.info(f"\n\nTotal links found to start download: {len(links)}")

    DownloadGitZips(download_path=repos_download_folder_path, downloaded_link_path=downloaded_link_file_path).run(links)

    root_logger.debug(
        "\n\n#########################################################################################\n\n"
    )