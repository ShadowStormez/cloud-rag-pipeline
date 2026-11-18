from unittest.mock import Mock
import pytest

from documentation_discovery import download_limited


def mock_response(chunks, headers=None, is_redirect=False):
    response = Mock()
    response.headers = headers or {}
    response.is_redirect = is_redirect
    response.iter_content.return_value = chunks

    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)

    return response


def test_download_success():
    session = Mock()
    response = mock_response([b"hello", b" world"])
    session.get.return_value = response

    result = download_limited(
        "https://docs.godotengine.org/sitemap.xml",
        session,
        max_bytes=100,
    )

    assert result == b"hello world"
    session.get.assert_called_once_with(
        "https://docs.godotengine.org/sitemap.xml",
        timeout=(5, 20),
        allow_redirects=False,
        stream=True,
    )


def test_download_exceeds_stream_limit():
    session = Mock()
    session.get.return_value = mock_response(
        [b"12345", b"67890"]
    )

    with pytest.raises(ValueError, match="size limit"):
        download_limited(
            "https://docs.godotengine.org/sitemap.xml",
            session,
            max_bytes=8,
        )


def test_download_rejects_large_content_length():
    session = Mock()
    response = mock_response(
        [b"hello"],
        headers={"Content-Length": "1000"},
    )
    session.get.return_value = response

    with pytest.raises(ValueError, match="size limit"):
        download_limited(
            "https://docs.godotengine.org/sitemap.xml",
            session,
            max_bytes=100,
        )

    response.iter_content.assert_not_called()


def test_download_rejects_redirect():
    session = Mock()
    session.get.return_value = mock_response(
        [],
        is_redirect=True,
    )

    with pytest.raises(ValueError, match="Redirects"):
        download_limited(
            "https://docs.godotengine.org/sitemap.xml",
            session,
            max_bytes=100,
        )