import json
import re
from typing import List

from .exceptions import (
    ResponseProcessException,
    ClientError,
    ServerError,
    NotFound404Error,
)
from .serializers import SimpleSerializer
from .tapi import TapiInstantiator, TapiClientExecutor


def generate_wrapper_from_adapter(adapter_class):
    return TapiInstantiator(adapter_class)


class Resource:
    def __init__(
        self, name: str,
        url: str,
        url_docs: str = None,
        allowed_http_methods: List[str] = None,
        descriptions: str = None,
        **kwargs
    ):
        """

        :param name: Client method name.
        :param url: Url resource.
        :param url_docs: URL official documentation.
        :param allowed_http_methods: Literal["GET", "POST", "PUT", "OPTIONS", "DELETE", "PATCH"]
        :param descriptions: Descriptions.
        :param kwargs:
        """
        self.name = name
        self.url = url
        self.doc_url = url_docs
        self.allowed_http_methods = allowed_http_methods
        self.descriptions = descriptions
        self.kwargs = kwargs

    def dict(self):
        return {
            self.name: {
                **self.kwargs,
                "resource": self.url,
                "docs": self.doc_url,
                "methods": self.allowed_http_methods,
                "descriptions": self.descriptions
            }
        }

    def __getitem__(self, item):
        return self.dict()[item]


class TapiAdapter(object):
    serializer_class = SimpleSerializer
    api_root = NotImplementedError
    resource_mapping: dict = NotImplementedError

    def __init__(self, serializer_class=None, resource_mapping: List[Resource] = None, **kwargs):
        if serializer_class:
            self.serializer = serializer_class()
        else:
            self.serializer = self.get_serializer()

        if resource_mapping:
            for resource in resource_mapping:
                self.resource_mapping.update(resource.dict())

    @property
    def native_methods(self):
        """Make custom attributes and methods to native"""
        base_attributes = {
            *dir(TapiAdapter),
            *dir(TapiClientExecutor),
            *dir(JSONAdapterMixin),
            "serializer",
        }
        a = [
            attr
            for attr in dir(self)
            if not attr.startswith("_") and attr not in base_attributes
        ]
        return a

    def _method_to_native(self, method_name, **kwargs):
        return getattr(self, method_name)(**kwargs)

    def _value_to_native(self, method_name, value, **kwargs):
        return self.serializer.deserialize(method_name, value, **kwargs)

    def _get_to_native_method(self, method_name, data, **context):
        if not self.serializer and method_name not in self.native_methods:
            raise NotImplementedError(
                "This client does not have a serializer and not have native methods"
            )

        if method_name in self.native_methods:

            def to_native_wrapper(**kwargs):
                return self._method_to_native(
                    method_name, data=data, **{**context, **kwargs}
                )

        else:

            def to_native_wrapper(**kwargs):
                return self._value_to_native(method_name, data, **kwargs)

        return to_native_wrapper

    def get_serializer(self):
        if self.serializer_class:
            return self.serializer_class()

    def get_api_root(self, api_params, resource_name):
        return self.api_root

    def fill_resource_template_url(self, template, params, resource):
        """Create of url request"""
        try:
            return template.format(**params)
        except KeyError:
            all_keys = re.findall(r"{(.[^\}]*)", template)
            range_not_set_keys = set(all_keys) - set(params.keys())
            not_set_keys = "', '".join(range_not_set_keys)

            raise TypeError(
                "{}() missing {} required url params: '{}'".format(
                    resource, len(range_not_set_keys), not_set_keys
                )
            )

    def get_request_kwargs(self, api_params, *args, **kwargs):
        """Adding parameters to a request"""
        serialized = self.serialize_data(kwargs.get("data"))
        kwargs["data"] = self.format_data_to_request(serialized)
        return kwargs

    def get_error_message(self, data, response=None):
        """Get error from response."""
        return str(data)

    def process_response(self, response, request_kwargs, **kwargs):
        """Processing request responses."""
        if response.status_code == 404:
            raise ResponseProcessException(NotFound404Error, None)
        elif 500 <= response.status_code < 600:
            raise ResponseProcessException(ServerError, None)

        data = self.response_to_native(response)

        if 400 <= response.status_code < 500:
            raise ResponseProcessException(ClientError, data)

        return data

    def error_handling(
        self,
        tapi_exception,
        error_message,
        repeat_number,
        response,
        request_kwargs,
        api_params,
        **kwargs
    ):
        """
        Wrapper for throwing custom exceptions. When,
        for example, the server responds with 200,
        and errors are passed inside json.
        """
        raise tapi_exception

    def serialize_data(self, data):
        if self.serializer:
            return self.serializer.serialize(data)

        return data

    def format_data_to_request(self, data):
        raise NotImplementedError()

    def response_to_native(self, response):
        raise NotImplementedError()

    def get_iterator_iteritems(
        self, response_data, response, request_kwargs, api_params, **kwargs
    ):
        raise NotImplementedError()

    def get_iterator_pages(
        self, response_data, response, request_kwargs, api_params, **kwargs
    ):
        raise NotImplementedError()

    def get_iterator_items(self, data, response, request_kwargs, api_params, **kwargs):
        raise NotImplementedError()

    def get_iterator_next_request_kwargs(
        self, response_data, response, request_kwargs, api_params, **kwargs
    ):
        raise NotImplementedError()

    def is_authentication_expired(self, tapi_exception, *args, **kwargs):
        return False

    def refresh_authentication(self, api_params, *args, **kwargs):
        raise NotImplementedError()

    def retry_request(
        self,
        tapi_exception,
        error_message,
        repeat_number,
        response,
        request_kwargs,
        api_params,
        **kwargs
    ):
        """
        Conditions for repeating a request.
        If it returns True, the request will be repeated.
        """
        return False

    def __str__(self, data=None, request_kwargs=None, response=None, api_params=None):
        raise NotImplementedError()


class JSONAdapterMixin(object):
    def get_request_kwargs(self, api_params, *args, **kwargs):
        request_kwargs = super(JSONAdapterMixin, self).get_request_kwargs(
            api_params, *args, **kwargs
        )
        request_kwargs["headers"] = {
            "Content-Type": "application/json",
            **api_params.get("headers", {}),
            **request_kwargs["headers"],
        }

        return request_kwargs

    def format_data_to_request(self, data):
        if data:
            return json.dumps(data)

    def response_to_native(self, response):
        if response.content.strip():
            try:
                return json.loads(response.content.decode())
            except json.JSONDecodeError:
                return response.text

    def get_error_message(self, data, response=None):
        if not data and response.content.strip():
            data = json.loads(response.content.decode())

        if data:
            return data.get("error", None)
