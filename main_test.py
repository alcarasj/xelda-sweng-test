from http import HTTPStatus
from main import (
    WIKI_API_URL,
    main,
    MAX_RESULTS,
    WIKI_BASE_URL,
    INVALID_SEARCH_TERM_ERROR_MSG_TEMPLATE,
)
import urllib.parse
import json
import pytest
import requests_mock
import requests


TEST_FIXTURE_PATH = "./test-fixture.json"
WIKI_RANDOM_API_URL = (
    "%s?list=random&rnlimit=200&rnnamespace=0&action=query&format=json" % WIKI_API_URL
)
WIKI_REVISION_API_URL = "%s"
TEST_FIXTURE = json.load(open(TEST_FIXTURE_PATH))


def test_english_search_e2e_with_random_success():
    # This test uses both the live Random API and live Revisions API.
    # "and" is the no. 1 most used word in the English language, so we can have very high
    # confidence that it will return N results where 0 < N <= MAX_RESULTS for an English search.
    search_term = "      and       "
    result = main(search_term)
    assert len(result) > 0
    assert len(result) <= MAX_RESULTS


def test_english_search_e2e_success():
    # This test mocks the Random API but uses live Revisions API.
    with requests_mock.Mocker() as mock:
        mock.get(WIKI_RANDOM_API_URL, json=TEST_FIXTURE["wikiRandomAPIMockResponse"])
        search_term = "   and           "
        results = main(search_term)

    expectedResults = TEST_FIXTURE["expectedResults"]
    for i, r in enumerate(results):
        assert r["relevance_score"] == expectedResults[i]["relevance_score"]
        assert r["title"] == expectedResults[i]["title"]
        assert r["url"] == "%s/wiki/%s" % (
            WIKI_BASE_URL,
            urllib.parse.quote(expectedResults[i]["title"]),
        )
        # TO-DO Validate if URL is indeed a valid, active Wiki article.


def test_invalid_inputs():
    search_terms = ["", "   ", 0, None, [], {}]
    for t in search_terms:
        with pytest.raises(RuntimeError) as e:
            main(t)
        assert str(e.value) == INVALID_SEARCH_TERM_ERROR_MSG_TEMPLATE % t


def test_random_api_request_invalid_http_response_status():
    test_cases = [
        {
            "status_code": HTTPStatus.BAD_REQUEST,
            "expected_message": "%i Client Error: None for url: %s"
            % (HTTPStatus.BAD_REQUEST, WIKI_RANDOM_API_URL),
        },
        {
            "status_code": HTTPStatus.INTERNAL_SERVER_ERROR,
            "expected_message": "%i Server Error: None for url: %s"
            % (HTTPStatus.INTERNAL_SERVER_ERROR, WIKI_RANDOM_API_URL),
        },
        {
            "status_code": 418,
            "expected_message": "%i Client Error: None for url: %s"
            % (418, WIKI_RANDOM_API_URL),
        },
    ]
    for test_case in test_cases:
        with requests_mock.Mocker() as mock:
            mock.get(WIKI_RANDOM_API_URL, status_code=test_case["status_code"])
            with pytest.raises(requests.exceptions.HTTPError) as e:
                main("blabla")
            assert str(e.value) == test_case["expected_message"]


def test_rev_api_request_invalid_http_response_status():
    test_cases = [
        {
            "status_code": HTTPStatus.BAD_REQUEST,
            "expected_message": "%i Client Error: None for url: %s"
            % (HTTPStatus.BAD_REQUEST, WIKI_REVISION_API_URL),
        },
        {
            "status_code": HTTPStatus.INTERNAL_SERVER_ERROR,
            "expected_message": "%i Server Error: None for url: %s"
            % (HTTPStatus.INTERNAL_SERVER_ERROR, WIKI_REVISION_API_URL),
        },
        {
            "status_code": 418,
            "expected_message": "%i Client Error: None for url: %s"
            % (418, WIKI_REVISION_API_URL),
        },
    ]
    # TO-DO aiohttp request mocking for testing.
