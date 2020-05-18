from unittest import TestCase

from truecomercializadora import utils_http

def test_base_response():
    status_code = 200
    
    for data in ['teste', {'teste2': 1, 'teste3': 2}, [3,4,5]]:
        response = utils_http._base_response(status_code, data)
        assert isinstance(response, dict)

def test_informational_response():
    response = utils_http.informational_response(100, utils_http.get_response_text(100))
    assert isinstance(response, dict)

def test_success_response():
    response = utils_http.success_response(200, utils_http.get_response_text(200))
    assert isinstance(response, dict)

def test_redirect_response():
    response = utils_http.redirect_response(300, utils_http.get_response_text(300))
    assert isinstance(response, dict)

def test_client_error_response():
    response = utils_http.client_error_response(400, utils_http.get_response_text(400))
    assert isinstance(response, dict)

def test_server_error_response():
    response = utils_http.server_error_response(500, utils_http.get_response_text(500))
    assert isinstance(response, dict)