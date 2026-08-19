from unittest.mock import patch

from src.api_client import get_data
import requests
from unittest.mock import patch

import pytest

from src.api_client import get_data


@patch("src.api_client.requests.get")
def test_get_data(mock_get):
    mock_get.return_value.json.return_value = {
        "name": "Sebastian",
        "role": "AI Agent Developer",
    }
    mock_get.return_value.raise_for_status.return_value = None

    result = get_data("https://example.com/data")

    assert result["name"] == "Sebastian"
    assert result["role"] == "AI Agent Developer"

    mock_get.assert_called_once_with(
        "https://example.com/data",
        timeout=10,
    )

@patch("src.api_client.requests.get")
def test_get_data_http_error(mock_get):
    mock_get.return_value.raise_for_status.side_effect = (
        requests.HTTPError("404 Not Found")
    )

    with pytest.raises(requests.HTTPError):
        get_data("https://example.com/missing")

@patch("src.api_client.requests.get")
def test_get_data_timeout(mock_get):
    mock_get.side_effect = requests.Timeout("Request timed out")

    with pytest.raises(requests.Timeout):
        get_data("https://example.com/slow")        