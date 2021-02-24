# -*- coding: utf-8 -*-
import pytest

from tapi.adapters import TapiAdapter


def test_fill_resource_template_url():
    adapter = TapiAdapter()

    template = "{country}/{city}"
    resource = "point"

    url = adapter.fill_resource_template_url(
        template, {"city": "Moscow", "country": "Russia"}, resource
    )
    assert url == "Russia/Moscow"

    with pytest.raises(TypeError):
        adapter.fill_resource_template_url(template, {}, resource)


def test_fill_resource_template_url_exception():
    adapter = TapiAdapter()

    template = "{country}/{city}"
    resource = "point"

    try:
        adapter.fill_resource_template_url(template, {}, resource)
    except Exception as exc:
        assert exc.args == ("point() missing 2 required url params: 'city', 'country'",)
