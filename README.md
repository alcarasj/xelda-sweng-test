# xelda-sweng-test
A take-home test for a software engineer position at Xelda.

# Setup
Requires Python >=3.8, pip3 and virtualenv to be installed on your machine.
1. `cd` to repo root.
1. Create a venv with `python3 -m venv .venv`
1. Activate the venv with `. .venv/bin/activate`
1. Install dependencies with `pip3 install -r requirements.txt`
1. Run the script using `python3 main.py -s "some-search-string-here"`
1. Run tests using `pytest`
1. Format code using `black .`

# Design
This program was designed to be simple, resilient, efficient and scalable.

# Flow
1. Fetch a list of 200 random titles of articles using the [Random API](https://www.mediawiki.org/wiki/API:Random).
2. Divide this list of 200 random titles into chunks so that we can use the [Revisions API](https://www.mediawiki.org/wiki/API:Revisions) to fetch the article for each title. This API accepts up to a limit of 50 titles per request, so for 200 titles, we will send 200 / 50 = 4 requests to this API.
3. Using `asyncio` and `aiohttp`, async tasks are batched and executed for each chunk to take advantage of concurrency.
4. Once the articles for all titles are fetched, the program looks for the search term in the title and content strings and assigns a relevance score to each article. This score is determined by how many times the search term appears in the string. The score is multiplied by a factor of 2 if it is in the title. Articles with a score of 0 are discarded.
5. The search results are then sorted in relevance score descending order are returned. A list of dictionaries containing the titles and URLs of the search results are also printed.

(If I had more time, I'd probably improve the tests?)