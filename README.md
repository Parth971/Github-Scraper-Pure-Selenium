# GitHub Scraper - Pure Selenium

Web Scraping with [Selenium](https://www.selenium.dev/) allows you to gather all the required data using Selenium
Webdriver Browser Automation. Selenium crawls the target URL webpage and gathers data at scale. This article
demonstrates how to do web scraping using Selenium.

## Aim of Project

We should give one url of GitHub domain. It could be of anything having `github.com` domain like user repository, user
home page, search page, advanced search page, etc.

This scraper will analyse the given url and fetch related urls. For example, if we give
url `https://github.com/Parth971` then it will fetch all repositories url of `Parth971` user.

## Project Setup

Python Version: 3.8+

### 1. Set Python Virtual Environment (recommended)

Install [Python Virtual Environment](https://www.geeksforgeeks.org/creating-python-virtual-environment-windows-linux/)

#### To Activate virtual environment

    # For Linux
    source myenv/bin/activate 
    
    # For Windows
    myenv\Scripts\activate

### 2. Install requirements

```code 
pip install -r requirements.txt
```

### 3. Steps to run

#### Script 0: Get all repositories link

    python script0.py

To see all repositories links, open `/outputs/collected_links.txt` <br>
To see logs of getting repositories, open `/outputs/scraping_links.log`

#### Script 1: Download all repositories as zip file

    python script1.py

To see all downloaded repositories as zip file, open `/RepoDownloads/` <br>
To see all downloaded repositories links, open `/outputs/downloaded_link.txt` <br>
To see failed repositories links, open `/outputs/failed_link.txt` <br>
To see logs of downloading repositories, open `/outputs/downloading_links.log`

#### Script 2. Unzip all zip repositories

    python script2.py

To see list of unzipped files names, open `/outputs/unzipped_repositories.txt` <br>
To see list of failed unzipped files names, open `/outputs/unzip_failed_link.txt` <br>
To see logs of unzipping repositories, open `/outputs/unzip.log`

### Parameters in script0.py file

- To set number for downloading repositories

    ```code 
    # 1. set integer to download specific number of links
    # 2. Set None to download all links
    links_to_download = 15
    ```

- To set initial link (links of : users repository, searches [ repositories, commits, issues, discussion, wikis ] )

    ```code 
    LINK = 'https://github.com/search?q=django+celery+drf'
    ```

- To set ban waiting time (seconds)

    ```code 
    ban_waiting_time = 30
    ```