# GitHub Scraper - Pure Selenium

Web Scraping with [Selenium](https://www.selenium.dev/) allows you to gather all the required data using Selenium Webdriver Browser Automation. Selenium crawls the target URL webpage and gathers data at scale. This article demonstrates how to do web scraping using Selenium.

## Aim of Project

We should give one url of GitHub domain. It could be of anything having `github.com` domain like user repository, user home page, search page, advanced search page, etc. 

This scraper will analyse the given url and fetch related urls. For example, if we give url `https://github.com/Parth971` then it will fetch all repositories url of `Parth971` user.


## Install requirements (Python 3.8)
```code 
pip install -r requirements.txt
```


# Steps to run
### 1. Get all repositories link
```code 
python script0.py
```
To see all repositories links, open `/outputs/collected_links.txt` <br>
To see logs of getting repositories, open `/outputs/scraping_links.log`
<br>
<br>
### 2. Download all repositories as zip file
```code 
python script1.py
```
To see all downloaded repositories links, open `/outputs/downloaded_link.txt` <br>
To see failed repositories links, open `/outputs/failed_link.txt` <br>
To see logs of downloading repositories, open `/outputs/downloading_links.log`
<br>
<br>

### 3. Unzip all zip repositories
```code 
python script2.py
```
To see list of unziped files names, open `/outputs/unzipped_repositories.txt` <br>
To see list of failed unziped files names, open `/outputs/unzip_failed_link.txt` <br>
To see logs of unzipping repositories, open `/outputs/unzip.log`
<br>
<br>

### Parameters in script0.py file
1. To set number for downloding repositories 
```code 
# 1. set integer to download specific number of links
# 2. Set None to download all links
links_to_download = 15
```

2. To set initial link (links of : users repository, searches [ repositories, commits, issues, discussion, wikis ] )
```code 
LINK = 'https://github.com/search?q=django+celery+drf'
```

3. To set ban waiting time (seconds)
```code 
ban_waiting_time = 30
```