from main import main, MAX_RESULTS, search
import requests
import json
import pytest
import requests_mock


TEST_FIXTURE_PATH = "./test-fixture.json"
WIKI_RANDOM_API_URL = "https://en.wikipedia.org/w/api.php?list=random&rnlimit=200&rnnamespace=0&action=query&format=json"
TEST_FIXTURE = json.load(open(TEST_FIXTURE_PATH))


def test_english_search_e2e_with_random_success():
    # "and" is the no. 1 most used word in the English language, so we can have very high 
    # confidence that it will return N results where 0 < N <= MAX_RESULTS for an English search.
    search_term = "      and       "
    result = main(search_term)
    assert len(result) > 0
    assert len(result) <= MAX_RESULTS 


def test_english_search_e2e_success():
    with requests_mock.Mocker() as mock:
        mock.get(WIKI_RANDOM_API_URL, json=TEST_FIXTURE["wikiRandomAPIMockResponse"])
        search_term = "   and           "
        results = main(search_term)
        expectedResults = TEST_FIXTURE["expectedResults"]

        for i, r in enumerate(results):
            assert r["relevance_score"] == expectedResults[i]["relevance_score"]
            assert r["title"] == expectedResults[i]["title"]

    
def test_invalid_inputs():
    search_terms = ["", "   ", 0, None, [], {}]
    with pytest.raises(RuntimeError):
        for t in search_terms:
            main(t)


def test_invalid_http_response():
    search_terms = ["", "   ", 0, None, [], {}]
    with pytest.raises(RuntimeError):
        for t in search_terms:
            result = main(t)
            assert len(result) == 0
