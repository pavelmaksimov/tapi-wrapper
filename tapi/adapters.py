# coding: utf-8

import json

from .exceptions import (
    ResponseProcessException,
    ClientError,
    ServerError,
    NotFound404Error,
)
from .serializers import SimpleSerializer
from .tapi import TapiInstantiator


def generate_wrapper_from_adapter(adapter_class):
    return TapiInstantiator(adapter_class)


class TapiAdapter(object):
    serializer_class = SimpleSerializer
    api_root = NotImplementedError

    def __init__(self, serializer_class=None, *args, **kwargs):
        if serializer_class:
            self.serializer = serializer_class()
        else:
            self.serializer = self.get_serializer()

    def _get_to_native_method(self, method_name, value):
        if not self.serializer:
            raise NotImplementedError("This client does not have a serializer")

        def to_native_wrapper(**kwargs):
            return self._value_to_native(method_name, value, **kwargs)

        return to_native_wrapper

    def _value_to_native(self, method_name, value, **kwargs):
        return self.serializer.deserialize(method_name, value, **kwargs)

    def get_serializer(self):
        if self.serializer_class:
            return self.serializer_class()

    def get_api_root(self, api_params):
        return self.api_root

    def fill_resource_template_url(self, template, params):
        """Формирование url запроса"""
        return template.format(**params)

    def get_request_kwargs(self, api_params, *args, **kwargs):
        """Обогащение запроса, параметрами"""
        serialized = self.serialize_data(kwargs.get("data"))

        kwargs.update({"data": self.format_data_to_request(serialized)})
        return kwargs

    def get_error_message(self, data, response=None):
        """Извлечение ошибки из запроса."""
        return str(data)

    def process_response(self, response, **request_kwargs):
        """Обработка ответов запроса."""
        if response.status_code == 404:
            raise ResponseProcessException(NotFound404Error, None)
        elif 500 <= response.status_code < 600:
            raise ResponseProcessException(ServerError, None)

        data = self.response_to_native(response)

        if 400 <= response.status_code < 500:
            raise ResponseProcessException(ClientError, data)

        return data

    def wrapper_call_exception(
        self, response, tapi_exception, api_params, *args, **kwargs
    ):
        """
        Обертка для вызова кастомных исключений.
        Когда например сервер отвечает 200,
        а ошибки передаются внутри json.
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

    def get_iterator_list(self, response_data):
        raise NotImplementedError()

    def get_iterator_next_request_kwargs(
        self, iterator_request_kwargs, response_data, response
    ):
        raise NotImplementedError()

    def is_authentication_expired(self, exception, *args, **kwargs):
        return False

    def refresh_authentication(self, api_params, *args, **kwargs):
        raise NotImplementedError()

    def generate_request_kwargs(self, api_params, *args, **kwargs):
        """
        Выполняется перед первым запросом.
        Здесь можно сразу сформировать дополнительные запросы.
        """
        # Первый/текущий сформированный запрос.
        request_kwargs = self.get_request_kwargs(api_params, *args, **kwargs)
        return [request_kwargs]

    def retry_request(
        self, response, tapi_exception, api_params, count_request_error, *args, **kwargs
    ):
        """
        Условия повторения запроса.
        Если вернет True, то запрос повторится.

        Некоторые доступные данные:
        response = tapi_exception.client().response
        status_code = tapi_exception.client().status_code
        response_data = tapi_exception.client().data
        """
        return False

    def extra_request(
        self,
        api_params,
        current_request_kwargs,
        request_kwargs_list,
        response,
        current_result,
    ):
        """
        Формирование дополнительных запросов.
        Они будут сделаны, если отсюда вернется
        непустой массив из kwargs для доп. запросов.

        :param current_request_kwargs: dict : {headers, data, url, params} : параметры текущего запроса
        :param request_kwargs_list: list :
            Наборы параметров для запросов, которые будут сделаны.
            В него можно добавлять дополнительные наборы параметров, чтоб сделать дополнительные запросы.
        :param response: request object : текущий ответ
        :param current_result: json : текущий результат
        :return: list : request_kwargs_list
        """
        # request_kwargs_list может содержать наборы параметров запросов, которые еще не сделаны.
        # Поэтому в него нужно добавлять новые, а не заменять.
        return request_kwargs_list

    def __str__(self, data=None, request_kwargs=None, response=None, api_params=None):
        raise NotImplementedError()


class FormAdapterMixin(object):
    def format_data_to_request(self, data):
        return data

    def response_to_native(self, response):
        return {"text": response.text}


class JSONAdapterMixin(object):
    def get_request_kwargs(self, api_params, *args, **kwargs):
        arguments = super(JSONAdapterMixin, self).get_request_kwargs(
            api_params, *args, **kwargs
        )

        if "headers" not in arguments:
            arguments["headers"] = {}
        arguments["headers"]["Content-Type"] = "application/json"
        return arguments

    def format_data_to_request(self, data):
        if data:
            return json.dumps(data)

    def response_to_native(self, response):
        if response.content.strip():
            return response.json()

    def get_error_message(self, data, response=None):
        if not data and response.content.strip():
            data = json.loads(response.content.decode("utf-8"))

        if data:
            return data.get("error", None)

    def transform_results(self, results, requests_kwargs, responses, api_params):
        """
        Преобразователь данных после получения всех ответов.

        :param results: list : данные всех запросов
        :param requests_kwargs: параметры всех запросов
        :param responses: ответы всех запросов
        :param api_params: входящие параметры класса
        :return: list
        """
        return results

    def data(self, data, request_kwargs, response, api_params, *args, **kwargs):
        """Преобразователь данных в требуемый формат."""
        return data

    def to_json(self, data, request_kwargs, response, api_params, *args, **kwargs):
        """Преобразователь данных в json."""
        raise NotImplementedError

    def to_df(self, data, request_kwargs, response, api_params, *args, **kwargs):
        """Преобразователь данных в DataFrame."""
        raise NotImplementedError

    def transform(self, data, request_kwargs, response, api_params, *args, **kwargs):
        """Кастомный преобразователь данных."""
        raise NotImplementedError
