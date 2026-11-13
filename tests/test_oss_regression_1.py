"""Cover sibling stubs on a shared method chain."""

from flexmock import flexmock


def test_chained_stubs_share_intermediate_methods():
    """Both leaves remain callable after the second stub is registered."""
    mock = flexmock()
    mock.should_receive("get_url.parse_html.retrieve_results").and_return([])
    mock.should_receive("get_url.parse_html.retrieve_header").and_return({})

    parsed = mock.get_url().parse_html()
    assert hasattr(parsed, "retrieve_results")
    assert parsed.retrieve_results() == []
    assert parsed.retrieve_header() == {}
