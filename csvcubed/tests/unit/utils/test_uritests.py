import pytest

from csvcubed.utils.uri import (
    get_last_uri_part,
    csvw_column_name_safe,
    looks_like_uri,
    ensure_looks_like_uri,
)


def test_uri_last_part():
    assert "dataset-name#something" == get_last_uri_part(
        "http://gss-data.org.uk/data/stuff/dataset-name#something"
    )


def test_csvw_column_name():
    assert "some_random_column_name" == csvw_column_name_safe(
        "Some Random Column //+Name"
    )
    assert "something_else" == csvw_column_name_safe("Something-else")


def test_looks_like_uri():
    assert looks_like_uri("https://some-domain.org")
    assert looks_like_uri("http://some-domain.org/some-stuff/other-stuff")
    assert looks_like_uri("ftp://some-domain.org")
    assert looks_like_uri("somescheme:somevalue")

    assert not looks_like_uri("somevalue/cheese")


def test_ensure_looks_like_uri():
    ensure_looks_like_uri("http://some-domain.org/")

    with pytest.raises(ValueError) as err:
        ensure_looks_like_uri("not-like-a-uri")

    assert "'not-like-a-uri' does not look like a URI" in str(err)


if __name__ == "__main__":
    pytest.main()
