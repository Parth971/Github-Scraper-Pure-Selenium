## Install requirements
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


### 2. Download all repositories as zip file
```code 
python script1.py
```
To see all downloaded repositories links, open `/outputs/downloaded_link.txt` <br>
To see failed repositories links, open `/outputs/failed_link.txt` <br>
To see logs of downloading repositories, open `/outputs/downloading_links.log`

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