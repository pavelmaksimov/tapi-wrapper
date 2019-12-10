
class ResponseProcessException(Exception):

    def __init__(self, tapi_exception, data, *args, **kwargs):
        self.tapi_exception = tapi_exception
        self.data = data
        super(ResponseProcessException, self).__init__(*args, **kwargs)


class TapiException(Exception):

    def __init__(self, message, client):
        self.status_code = None
        self.client = client
        if client is not None:
            self.status_code = client().status_code

        if not message:
            message = "response status code: {}".format(self.status_code)
        super(TapiException, self).__init__(message)


class ClientError(TapiException):

    def __init__(self, message='', client=None):
        super(ClientError, self).__init__(message, client=client)


class ServerError(TapiException):

    def __init__(self, message='', client=None):
        super(ServerError, self).__init__(message, client=client)


class NotFound404Error(TapiException):

    def __init__(self, message='Ошибка 404 не найдена страница', client=None):
        super(NotFound404Error, self).__init__(message, client=client)
