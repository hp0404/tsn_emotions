import re
import requests
import pandas as pd
import bs4
from time import sleep
from random import uniform
from typing import List, Dict, Tuple


BASE_URL = "https://www.pravda.com.ua"
DATE_PAT = re.compile(r"\d{4}/\d{1,2}/\d{1,2}")


def read_page(url: str) -> bytes:
    """Makes a request to get web-page's content.
    
    
    Parameters
    ----------
        url: link containing news-feed from `pravda.com.ua/archive` 
             e.i. https://www.pravda.com.ua/archives/date_10092019/
    """
    
    r = requests.get(url)
    return r.content


def _collect_newsitems_gen(articles: List[bs4.element.Tag]) -> Dict[str, str]:
    """Generator that collects articles' specific metadata.
    
    
    Parameters
    ----------
        articles: list containing bs4 elements to iterate over
        
    Yields
    ------
        Dictionary containing relevant information -  title, 
        subtitle, date, and link of each article 
    """
    
    for article in articles:
        title = article.a
        news_time = article.find(class_="article__time").text
        
        try:
            date = f'{DATE_PAT.search(title["href"]).group()} {news_time}'
        except AttributeError:
            date = f'missing date {news_time}'
            
        yield {
            "title": title.text,
            "subtitle": article.find(class_="article__subtitle").text,
            "date": date,
            "link": BASE_URL + title["href"] if title["href"].startswith("/") else title["href"]
        }


def news_scraper(news_content: bytes) -> Tuple[pd.DataFrame, str]:
    """ Scrapes archives' news-feed: 
    (a) creates table using `_collect_newsitems_gen` generator, and
    (b) locates path for the next page to parse.
    
    
    Parameters
    ----------
        news_content: response to the request made by read_page func.
    
    Returns
    -------
        Tuple containing both the table with all the articles from a specific day
        and the link to the next page
    """
    
    soup = bs4.BeautifulSoup(news_content, "html5lib")
    next_page_url = soup.select_one("div.archive-navigation > a.button.button_next")["href"]

    articles = soup.select("div.news.news_all > div")
    df = pd.DataFrame(_collect_newsitems_gen(articles))
    return df, BASE_URL + next_page_url


def news_to_df(
    start_url: str, 
    end_url: str = "https://www.pravda.com.ua/archives/", 
    data: List[pd.DataFrame] = None
) -> List[pd.DataFrame]:
    """ Scrapes multiple web-pages using all defined functions. 
    
    Parameters
    ----------
        start_url: url to start parsing
          end_url: url to end, defaults to `/archive` page
             data: list containing dataframes, defaults to None
    
    
    Returns
    -------
        list of tables of each scraped day
    """
        
    data = data or []
    next_page = start_url
    
    while True:
        print(next_page)
        
        content = read_page(next_page)
        df, next_page = news_scraper(content)
        data.append(df)
        
        if next_page == end_url:
            print("breaking...")
            break

        sleep(uniform(1,3))

    return data