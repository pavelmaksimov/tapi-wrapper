# coding: utf-8

from __future__ import unicode_literals

from tapi.adapters import (
    TapiAdapter, JSONAdapterMixin,
    generate_wrapper_from_adapter
)
from tapi.serializers import SimpleSerializer

RESOURCE_MAPPING = {
    'test': {
        'resource': 'test/',
        'docs': 'http://www.test.com'
    },
    'user': {
        'resource': 'user/{id}/',
        'docs': 'http://www.test.com/user'
    },
    'resource': {
        'resource': 'resource/{number}/',
        'docs': 'http://www.test.com/resource',
        'spam': 'eggs',
        'foo': 'bar'
    },
    'another_root': {
        'resource': 'another-root/',
        'docs': 'http://www.test.com/another-root'
    },
}


class TesterClientAdapter(JSONAdapterMixin, TapiAdapter):
    serializer_class = None
    api_root = 'https://api.test.com'
    resource_mapping = RESOURCE_MAPPING

    def get_api_root(self, api_params, resource_name):
        if resource_name == 'another_root':
            return 'https://api.another.com/'
        else:
            return self.api_root

    def get_iterator_pages(self, response_data, **kwargs):
        return response_data['data']

    def get_iterator_iteritems(self, response_data, **kwargs):
        return response_data['data']

    def get_iterator_list(self, response_data):
        return response_data['data']

    def get_iterator_next_request_kwargs(self, response_data, response, request_kwargs, api_params, **kwargs):
        paging = response_data.get('paging')
        if not paging:
            return
        url = paging.get('next')

        if url:
            return {'url': url}


TesterClient = generate_wrapper_from_adapter(TesterClientAdapter)


class CustomSerializer(SimpleSerializer):

    def to_kwargs(self, data, **kwargs):
        return kwargs


class SerializerClientAdapter(TesterClientAdapter):
    serializer_class = CustomSerializer


SerializerClient = generate_wrapper_from_adapter(SerializerClientAdapter)


class TokenRefreshClientAdapter(TesterClientAdapter):

    def is_authentication_expired(self, exception, *args, **kwargs):
        return exception.status_code == 401

    def refresh_authentication(self, api_params, *args, **kwargs):
        new_token = 'new_token'
        api_params['token'] = new_token
        return new_token


TokenRefreshClient = generate_wrapper_from_adapter(TokenRefreshClientAdapter)


class FailTokenRefreshClientAdapter(TokenRefreshClientAdapter):

    def refresh_authentication(self, api_params, *args, **kwargs):
        return None


FailTokenRefreshClient = generate_wrapper_from_adapter(FailTokenRefreshClientAdapter)
