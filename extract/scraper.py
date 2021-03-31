import argparse
import logging
logging.basicConfig(level=logging.INFO)

import csv
import datetime
import re

from requests.exceptions import HTTPError, ContentDecodingError
from urllib3.exceptions import MaxRetryError

import news_page_object as news

from common import config


logger = logging.getLogger(__name__)

is_well_formed_url = re.compile(r"^https?://.+/.+$")   # https://example.com/main
is_root_path = re.compile(r"^/.+$")     #/some_text


def _news_scraper(new_sites_uid):
    host = config()["news_sites"][new_sites_uid]["url"]

    logging.info(f"Beginning the scraper for {host}.")
    homepage = news.HomePage(new_sites_uid, host)

    articles = list()

    for link in homepage.article_links:
        article = _fetch_article(new_sites_uid, host, link)

        if article:
            logger.info("Article fetched!")
            articles.append(article)
            print(article.title)
    print(f"Number of articles fecthed {len(articles)}")

    _save_articles(new_sites_uid, articles)


def _save_articles(new_sites_uid, articles):
    datetime_now = datetime.datetime.now().strftime("%Y_%m_%d")
    out_file_name = f"{new_sites_uid}_{datetime_now}_articles.csv" 
    csv_header = list(filter(lambda property: not property.startswith("_"), dir(articles[0])))

    with open(out_file_name, mode="w+", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(csv_header)

        for article in articles:
            row = [str(getattr(article, prop)) for prop in csv_header]
            writer.writerow(row)
    f.close()


def _fetch_article(new_sites_uid, host, link):
    logger.info(f"Start fetching article at {host}")
    article = None

    try:
        article = news.ArticlePage(new_sites_uid, _build_link(host, link))
    except (HTTPError, ContentDecodingError, MaxRetryError):
        logger.warning("Error while fetching the article.", exc_info=False)

    if article and not article.body:
        logger.warning("Invalid article. There is not body.")
        return None

    return article


def _build_link(host, link):
    if is_well_formed_url.match(link):
        return link
    elif is_root_path.match(link):
        return f"{host}{link}"
    else:
        return f"{host}/{link}"
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    news_site_choices = list(config()["news_sites"].keys())
    parser.add_argument("news_site",
                        help="The news site that you want to scrape.",
                        type=str,
                        choices=news_site_choices)
    
    args = parser.parse_args()
    _news_scraper(args.news_site)
