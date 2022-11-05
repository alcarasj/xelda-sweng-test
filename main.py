import requests
import json
import asyncio
from http import HTTPStatus
import aiohttp
from argparse import ArgumentParser

MAX_RESULTS = 200
REVISIONS_API_TITLES_LIMIT = 50
TITLE_SCORE_MULTIPLIER = 2
WIKI_API_URL = "https://en.wikipedia.org/w/api.php"
RANDOM_API_REQ_PARAMS = {
    "list": "random",
    "rnlimit": MAX_RESULTS,
    "rnnamespace": 0,
    "action": "query",
    "format": "json",
}
REVISIONS_API_REQ_PARAMS = {
    "action": "query",
    "prop": "revisions",
    "rvprop": "timestamp|content",
    "rvslots": "main",
    "formatversion": "2",
    "format": "json",
}
INVALID_SEARCH_TERM_ERROR_MSG_TEMPLATE = (
    "Search term must be a non-blank string but was: %s"
)


def parse_args():
    parser = ArgumentParser(description="Script to search Wikipedia articles.")
    parser.add_argument(
        "-s",
        dest="search_term",
        help="The search term.",
        type=str,
        required=True,
    )
    args = parser.parse_args()
    return args


async def get_articles_by_titles(session, titles):
    # Get the content of the articles using the API at https://www.mediawiki.org/wiki/API:Revisions
    rev_api_params = REVISIONS_API_REQ_PARAMS.copy()
    rev_api_params["titles"] = "|".join(titles)
    async with session.get(url=WIKI_API_URL, params=rev_api_params) as res:
        if res.status != HTTPStatus.OK:
            raise RuntimeError(
                "GET articles by titles request returned status code: %i" % (res.status)
            )

        data = await res.json()
        if data.get("error"):
            raise RuntimeError(
                "GET articles by titles request returned error: %s" % (data["error"])
            )

        articles = data["query"]["pages"]
        return articles


def get_random_article_titles(n):
    # Get titles of N random articles using the API at https://www.mediawiki.org/wiki/API:Random
    res = requests.get(url=WIKI_API_URL, params=RANDOM_API_REQ_PARAMS)
    print(res.url)
    res.raise_for_status()
    results = res.json()["query"]["random"]

    if len(results) < n:
        raise RuntimeError("Expected >= %i articles but got %i" % (n, len(results)))

    results = results[: (n - 1)]
    titles = [result["title"] for result in results if result["title"]]
    return titles


def search(search_term, articles):
    relevant_articles = []

    for article in articles:
        relevance_score = 0
        title = article["title"]
        content = article["revisions"][0]["slots"]["main"]["content"]

        relevance_score += title.count(search_term) * TITLE_SCORE_MULTIPLIER
        relevance_score += content.count(search_term)

        article["relevance_score"] = relevance_score
        if relevance_score > 0:
            relevant_articles.append(article)

    search_results = sorted(
        relevant_articles, key=lambda article: article["relevance_score"], reverse=True
    )
    return search_results


async def get_articles_by_titles_parallel(titles):
    tasks = []
    prev_chunk_end_index = 0
    async with aiohttp.ClientSession() as session:
        tasks = []
        prev_chunk_end_index = 0
        for i, _ in enumerate(titles):
            if (i + 1) % REVISIONS_API_TITLES_LIMIT == 0:
                chunk_of_titles = titles[prev_chunk_end_index : i + 1]
                tasks.append(
                    asyncio.ensure_future(
                        get_articles_by_titles(session, chunk_of_titles)
                    )
                )
                prev_chunk_end_index = i + 1
        chunks_of_articles = await asyncio.gather(*tasks)
        articles = [article for chunk in chunks_of_articles for article in chunk]
        return articles


def main(search_term):
    is_search_term_valid_string = type(search_term) == str and search_term.strip()
    if is_search_term_valid_string:
        search_term = search_term.strip()
    else:
        raise RuntimeError(INVALID_SEARCH_TERM_ERROR_MSG_TEMPLATE % search_term)

    titles = get_random_article_titles(MAX_RESULTS)
    articles = asyncio.run(get_articles_by_titles_parallel(titles))
    search_results = search(search_term, articles)
    return search_results


if __name__ == "__main__":
    args = parse_args()
    main(args.search_term)
