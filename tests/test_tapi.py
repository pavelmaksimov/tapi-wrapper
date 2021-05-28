from __future__ import unicode_literals

import json
import unittest

import responses

from tapi2.adapters import Resource
from tapi2.exceptions import ClientError, ServerError
from tests.client import TesterClient, TokenRefreshClient, FailTokenRefreshClient


class TestTapiClient(unittest.TestCase):

    def setUp(self):
        self.wrapper = TesterClient()

    @responses.activate
    def test_added_custom_resources(self):
        wrapper = TesterClient(
            resource_mapping=[
                Resource("myresource", "http://url.ru/myresource"),
                Resource("myresource2", "https://url.ru/myresource2"),
            ]
        )
        responses.add(
            responses.GET,
            url=wrapper.myresource().data,
            body='[]',
            status=200,
            content_type='application/json'
        )

        response = self.wrapper.myresource().get()
        assert response.data == []

    def test_fill_url_template(self):
        expected_url = 'https://api.test.com/user/123/'

        resource = self.wrapper.user(id='123')

        self.assertEqual(resource.data, expected_url)

    def test_fill_another_root_url_template(self):
        expected_url = 'https://api.another.com/another-root/'

        resource = self.wrapper.another_root()

        self.assertEqual(resource.data, expected_url)

    def test_calling_len_on_tapioca_list(self):
        client = self.wrapper._wrap_in_tapi([0, 1, 2])
        self.assertEqual(len(client), 3)

    def test_iterated_client_items(self):
        client = self.wrapper._wrap_in_tapi([0, 1, 2])

        for i, item in enumerate(client):
            self.assertEqual(item, i)

    def test_client_data_dict(self):
        client = self.wrapper._wrap_in_tapi({"data": 0})

        assert client["data"] == 0
        assert client.data == {"data": 0}

    def test_client_data_list(self):
        client = self.wrapper._wrap_in_tapi([0, 1, 2])

        assert client[0] == 0
        assert client[1] == 1

    @responses.activate
    def test_in_operator(self):
        responses.add(responses.GET, self.wrapper.test().data,
                      body='{"data": 1, "other": 2}',
                      status=200,
                      content_type='application/json')

        response = self.wrapper.test().get()

        self.assertIn('data', response)
        self.assertIn('other', response)
        self.assertNotIn('wat', response)

    @responses.activate
    def test_accessing_index_out_of_bounds_should_raise_index_error(self):
        responses.add(responses.GET, self.wrapper.test().data,
                      body='["a", "b", "c"]',
                      status=200,
                      content_type='application/json')

        response = self.wrapper.test().get()

        with self.assertRaises(IndexError):
            response[3]

    @responses.activate
    def test_accessing_empty_list_should_raise_index_error(self):
        responses.add(responses.GET, self.wrapper.test().data,
                      body='[]',
                      status=200,
                      content_type='application/json')

        response = self.wrapper.test().get()

        with self.assertRaises(IndexError):
            response[3]

    def test_fill_url_from_default_params(self):
        wrapper = TesterClient(default_url_params={'id': 123})
        self.assertEqual(wrapper.user().data, 'https://api.test.com/user/123/')


class TestTapiExecutor(unittest.TestCase):

    def setUp(self):
        self.wrapper = TesterClient()

    def test_resource_executor_data_should_be_composed_url(self):
        expected_url = 'https://api.test.com/test/'
        resource = self.wrapper.test()

        self.assertEqual(resource.data, expected_url)

    def test_docs(self):
        self.assertEqual(
            '\n'.join(self.wrapper.resource.__doc__.split('\n')[1:]),
            'Resource: ' + self.wrapper.resource._resource['resource'] + '\n'
                                                                         'Docs: ' + self.wrapper.resource._resource[
                'docs'] + '\n'
                          'Foo: ' + self.wrapper.resource._resource['foo'] + '\n'
                                                                             'Spam: ' + self.wrapper.resource._resource[
                'spam'])

    def test_cannot__getittem__(self):
        client = self.wrapper._wrap_in_tapi([0, 1, 2])
        with self.assertRaises(Exception):
            client()[0]

    def test_cannot_iterate(self):
        client = self.wrapper._wrap_in_tapi([0, 1, 2])
        with self.assertRaises(Exception):
            for item in client():
                pass

    def test_dir_call_returns_executor_methods(self):
        client = self.wrapper._wrap_in_tapi([0, 1, 2])

        e_dir = dir(client())

        self.assertIn('data', e_dir)
        self.assertIn('response', e_dir)
        self.assertIn('get', e_dir)
        self.assertIn('post', e_dir)
        self.assertIn('pages', e_dir)
        self.assertIn('open_docs', e_dir)
        self.assertIn('open_in_browser', e_dir)

    @responses.activate
    def test_response_executor_object_has_a_response(self):
        next_url = 'http://api.teste.com/next_batch'

        responses.add(responses.GET, self.wrapper.test().data,
                      body='{"data": [{"key": "value"}], "paging": {"next": "%s"}}' % next_url,
                      status=200,
                      content_type='application/json')

        responses.add(responses.GET, next_url,
                      body='{"data": [{"key": "value"}], "paging": {"next": ""}}',
                      status=200,
                      content_type='application/json')

        response = self.wrapper.test().get()
        executor = response()

        executor.response

        executor._response = None

    def test_raises_error_if_executor_does_not_have_a_response_object(self):
        client = self.wrapper

        with self.assertRaises(Exception):
            client().response

    @responses.activate
    def test_response_executor_has_a_status_code(self):
        responses.add(responses.GET, self.wrapper.test().data,
                      body='{"data": {"key": "value"}}',
                      status=200,
                      content_type='application/json')

        response = self.wrapper.test().get()

        self.assertEqual(response().status_code, 200)


class TestTapiExecutorRequests(unittest.TestCase):

    def setUp(self):
        self.wrapper = TesterClient()

    def test_when_executor_has_no_response(self):
        with self.assertRaises(Exception) as context:
            self.wrapper.test().response

        exception = context.exception

        self.assertIn("has no response", str(exception))

    @responses.activate
    def test_get_request(self):
        responses.add(responses.GET, self.wrapper.test().data,
                      body='{"data": {"key": "value"}}',
                      status=200,
                      content_type='application/json')

        response = self.wrapper.test().get()

        self.assertEqual(response().data, {'data': {'key': 'value'}})

    @responses.activate
    def test_access_response_field(self):
        responses.add(responses.GET, self.wrapper.test().data,
                      body='{"data": {"key": "value"}}',
                      status=200,
                      content_type='application/json')

        response = self.wrapper.test().get()

        self.assertEqual(response.data, {"data": {"key": "value"}})

    @responses.activate
    def test_post_request(self):
        responses.add(responses.POST, self.wrapper.test().data,
                      body='{"data": {"key": "value"}}',
                      status=201,
                      content_type='application/json')

        response = self.wrapper.test().post()

        self.assertEqual(response().data, {'data': {'key': 'value'}})

    @responses.activate
    def test_put_request(self):
        responses.add(responses.PUT, self.wrapper.test().data,
                      body='{"data": {"key": "value"}}',
                      status=201,
                      content_type='application/json')

        response = self.wrapper.test().put()

        self.assertEqual(response().data, {'data': {'key': 'value'}})

    @responses.activate
    def test_patch_request(self):
        responses.add(responses.PATCH, self.wrapper.test().data,
                      body='{"data": {"key": "value"}}',
                      status=201,
                      content_type='application/json')

        response = self.wrapper.test().patch()

        self.assertEqual(response().data, {'data': {'key': 'value'}})

    @responses.activate
    def test_delete_request(self):
        responses.add(responses.DELETE, self.wrapper.test().data,
                      body='{"data": {"key": "value"}}',
                      status=201,
                      content_type='application/json')

        response = self.wrapper.test().delete()

        self.assertEqual(response().data, {'data': {'key': 'value'}})

    @responses.activate
    def test_carries_request_kwargs_over_calls(self):
        responses.add(responses.GET, self.wrapper.test().data,
                      body='{"data": {"key": "value"}}',
                      status=200,
                      content_type='application/json')

        response = self.wrapper.test().get()

        self.assertIn('url', response._request_kwargs)
        self.assertIn('data', response._request_kwargs)
        self.assertIn('headers', response._request_kwargs)

    @responses.activate
    def test_thrown_tapi_exception_with_clienterror_data(self):
        responses.add(responses.GET, self.wrapper.test().data,
                      body='{"error": "bad request test"}',
                      status=400,
                      content_type='application/json')
        with self.assertRaises(ClientError) as client_exception:
            self.wrapper.test().get()
        self.assertIn("bad request test", client_exception.exception.args)

    @responses.activate
    def test_thrown_tapi_exception_with_servererror_data(self):
        responses.add(responses.GET, self.wrapper.test().data,
                      body='{"error": "server error test"}',
                      status=500,
                      content_type='application/json')
        with self.assertRaises(ServerError) as server_exception:
            self.wrapper.test().get()
        self.assertIn("server error test", server_exception.exception.args)


class TestIteratorFeatures(unittest.TestCase):

    def setUp(self):
        self.wrapper = TesterClient()

    @responses.activate
    def test_simple_pages_iterator(self):
        next_url = 'http://api.teste.com/next_batch'

        responses.add(responses.GET, self.wrapper.test().data,
                      body='{"data": [{"key": "value"}], "paging": {"next": "%s"}}' % next_url,
                      status=200,
                      content_type='application/json')

        responses.add(responses.GET, next_url,
                      body='{"data": [{"key": "value"}], "paging": {"next": ""}}',
                      status=200,
                      content_type='application/json')

        response = self.wrapper.test().get()

        iterations_count = 0
        for item in response().pages():
            self.assertIn(item["key"], 'value')
            iterations_count += 1

        self.assertEqual(iterations_count, 2)

    @responses.activate
    def test_simple_pages_with_max_items_iterator(self):
        next_url = 'http://api.teste.com/next_batch'

        responses.add(responses.GET, self.wrapper.test().data,
                      body='{"data": [{"key": "value"}], "paging": {"next": "%s"}}' % next_url,
                      status=200,
                      content_type='application/json')

        responses.add(responses.GET, next_url,
                      body='{"data": [{"key": "value"}, {"key": "value"}, {"key": "value"}], "paging": {"next": ""}}',
                      status=200,
                      content_type='application/json')

        response = self.wrapper.test().get()

        iterations_count = 0
        for item in response().iter_items(max_items=3, max_pages=2):
            self.assertIn(item["key"], 'value')
            iterations_count += 1

        self.assertEqual(iterations_count, 3)

    @responses.activate
    def test_simple_pages_with_max_pages_iterator(self):
        next_url = 'http://api.teste.com/next_batch'

        responses.add(responses.GET, self.wrapper.test().data,
                      body='{"data": [{"key": "value"}], "paging": {"next": "%s"}}' % next_url,
                      status=200,
                      content_type='application/json')
        responses.add(responses.GET, next_url,
                      body='{"data": [{"key": "value"}, {"key": "value"}, {"key": "value"}], "paging": {"next": "%s"}}' % next_url,
                      status=200,
                      content_type='application/json')

        responses.add(responses.GET, next_url,
                      body='{"data": [{"key": "value"}, {"key": "value"}, {"key": "value"}], "paging": {"next": "%s"}}' % next_url,
                      status=200,
                      content_type='application/json')

        responses.add(responses.GET, next_url,
                      body='{"data": [{"key": "value"}, {"key": "value"}, {"key": "value"}], "paging": {"next": ""}}',
                      status=200,
                      content_type='application/json')

        response = self.wrapper.test().get()

        iterations_count = 0
        for item in response().iter_items(max_pages=3):
            self.assertIn(item["key"], 'value')
            iterations_count += 1

        self.assertEqual(iterations_count, 7)

    @responses.activate
    def test_simple_pages_max_page_zero_iterator(self):
        next_url = 'http://api.teste.com/next_batch'

        responses.add(responses.GET, self.wrapper.test().data,
                      body='{"data": [{"key": "value"}], "paging": {"next": "%s"}}' % next_url,
                      status=200,
                      content_type='application/json')

        responses.add(responses.GET, next_url,
                      body='{"data": [{"key": "value"}], "paging": {"next": ""}}',
                      status=200,
                      content_type='application/json')

        response = self.wrapper.test().get()

        iterations_count = 0
        for item in response().pages(max_pages=0):
            self.assertIn(item.key().data, 'value')
            iterations_count += 1

        self.assertEqual(iterations_count, 0)

    @responses.activate
    def test_simple_pages_max_item_zero_iterator(self):
        next_url = 'http://api.teste.com/next_batch'

        responses.add(responses.GET, self.wrapper.test().data,
                      body='{"data": [{"key": "value"}], "paging": {"next": "%s"}}' % next_url,
                      status=200,
                      content_type='application/json')

        responses.add(responses.GET, next_url,
                      body='{"data": [{"key": "value"}], "paging": {"next": ""}}',
                      status=200,
                      content_type='application/json')

        response = self.wrapper.test().get()

        iterations_count = 0
        for item in response().iter_items(max_items=0):
            self.assertIn(item.key().data, 'value')
            iterations_count += 1

        self.assertEqual(iterations_count, 0)


class TestTokenRefreshing(unittest.TestCase):

    def setUp(self):
        self.wrapper = TokenRefreshClient(token='token', refresh_token_by_default=True)

    @responses.activate
    def test_not_token_refresh_client_propagates_client_error(self):
        no_refresh_client = TesterClient()

        responses.add_callback(
            responses.POST, no_refresh_client.test().data,
            callback=lambda *a, **k: (401, {}, ''),
            content_type='application/json',
        )

        with self.assertRaises(ClientError):
            no_refresh_client.test().post()

    @responses.activate
    def test_disable_token_refreshing(self):
        responses.add_callback(
            responses.POST, self.wrapper.test().data,
            callback=lambda *a, **k: (401, {}, ''),
            content_type='application/json',
        )

        with self.assertRaises(ClientError):
            self.wrapper.test().post(refresh_token=False)

    @responses.activate
    def test_token_expired_automatically_refresh_authentication(self):
        self.first_call = True

        def request_callback(request):
            if self.first_call:
                self.first_call = False
                return (401, {'content_type': 'application/json'}, json.dumps({"error": "Token expired"}))
            else:
                self.first_call = None
                return (201, {'content_type': 'application/json'}, '')

        responses.add_callback(
            responses.POST, self.wrapper.test().data,
            callback=request_callback,
            content_type='application/json',
        )

        response = self.wrapper.test().post()

        # refresh_authentication method should be able to update api_params
        self.assertEqual(response._api_params['token'], 'new_token')

    @responses.activate
    def test_raises_error_if_refresh_authentication_method_returns_falsy_value(self):
        client = FailTokenRefreshClient(token='token', refresh_token_by_default=True)

        self.first_call = True

        def request_callback(request):
            if self.first_call:
                self.first_call = False
                return (401, {}, '')
            else:
                self.first_call = None
                return (201, {}, '')

        responses.add_callback(
            responses.POST, client.test().data,
            callback=request_callback,
            content_type='application/json',
        )

        with self.assertRaises(ClientError):
            client.test().post()

    @responses.activate
    def test_stores_refresh_authentication_method_response_for_further_access(self):
        self.first_call = True

        def request_callback(request):
            if self.first_call:
                self.first_call = False
                return (401, {}, '')
            else:
                self.first_call = None
                return (201, {}, '')

        responses.add_callback(
            responses.POST, self.wrapper.test().data,
            callback=request_callback,
            content_type='application/json',
        )

        response = self.wrapper.test().post()

        self.assertEqual(response().refresh_data, 'new_token')
