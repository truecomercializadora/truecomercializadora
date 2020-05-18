import json

def _base_response(status_code, data):
  """
  Build a base http response. With status code, headers, and body.
  """
  valid_status_codes = {
    100: "Continue",
    101: "Switching Protocols",
    102: "Processing",
    200: "OK",
    201: "Created",
    202: "Accepted",
    203: "Non-authoritative Information",
    204: "No Content",
    205: "Reset Content",
    206: "Partial Content",
    207: "Multi-Status",
    208: "Already Reported",
    226: "IM Used",
    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    305: "Use Proxy",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Payload Too Large",
    414: "Request-URI Too Long",
    415: "Unsupported Media Type",
    416: "Requested Range Not Satisfiable",
    417: "Expectation Failed",
    418: "I'm a teapot",
    421: "Misdirected Request",
    422: "Unprocessable Entity",
    423: "Locked",
    424: "Failed Dependency",
    426: "Upgrade Required",
    428: "Precondition Required",
    429: "Too Many Requests",
    431: "Request Header Fields Too Large",
    444: "Connection Closed Without Response",
    451: "Unavailable For Legal Reasons",
    499: "Client Closed Request",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
    505: "HTTP Version Not Supported",
    506: "Variant Also Negotiates",
    507: "Insufficient Storage",
    508: "Loop Detected",
    510: "Not Extended",
    511: "Network Authentication Required",
    599: "Network Connect Timeout Error"
  }

  if status_code not in valid_status_codes:
    raise Exception("Invalid status code {}".format(status_code))

  if type(data) == dict:
    data = json.dumps(data)

  if type(data) == list:
    data = json.dumps({"items": data})

  return {
    "statusCode": str(status_code),
    "headers": {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Headers": "application/json",
      "Access-Control-Allow-Methods": "POST"
    },
    "body": data
  }

def get_response_text(status_code):
  valid_status_codes = {
    100: "Continue",
    101: "Switching Protocols",
    102: "Processing",
    200: "OK",
    201: "Created",
    202: "Accepted",
    203: "Non-authoritative Information",
    204: "No Content",
    205: "Reset Content",
    206: "Partial Content",
    207: "Multi-Status",
    208: "Already Reported",
    226: "IM Used",
    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    305: "Use Proxy",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Payload Too Large",
    414: "Request-URI Too Long",
    415: "Unsupported Media Type",
    416: "Requested Range Not Satisfiable",
    417: "Expectation Failed",
    418: "I'm a teapot",
    421: "Misdirected Request",
    422: "Unprocessable Entity",
    423: "Locked",
    424: "Failed Dependency",
    426: "Upgrade Required",
    428: "Precondition Required",
    429: "Too Many Requests",
    431: "Request Header Fields Too Large",
    444: "Connection Closed Without Response",
    451: "Unavailable For Legal Reasons",
    499: "Client Closed Request",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
    505: "HTTP Version Not Supported",
    506: "Variant Also Negotiates",
    507: "Insufficient Storage",
    508: "Loop Detected",
    510: "Not Extended",
    511: "Network Authentication Required",
    599: "Network Connect Timeout Error"
  }

  return valid_status_codes.get(status_code, 'Invalid status code')


def informational_response(status_code, data):
  """
  100 Continue
  101 Switching Protocols
  102 Processing
  """

  status_codes = [100, 101, 102]
  if status_code not in status_codes:
    raise Exception("status_code input is not a valid status code." /
                    "Only {} are valid informational codes".format(list(status_codes)))
  
  return _base_response(status_code, data)


def success_response(status_code, data):
  """
  200 OK
  201 Created
  202 Accepted
  203 Non-authoritative Information
  204 No Content
  205 Reset Content
  206 Partial Content
  207 Multi-Status
  208 Already Reported
  226 IM Used
  """

  status_codes = [
    200,
    201,
    202,
    203,
    204,
    205,
    206,
    207,
    208,
    226,
  ]
  if status_code not in status_codes:
    raise Exception("status_code input is not a valid status code." /
                    "Only {} are valid success codes".format(list(status_codes)))

  return _base_response(status_code, data)


def redirect_response(status_code, data):
  """
  300 Multiple Choices
  301 Moved Permanently
  302 Found
  303 See Other
  304 Not Modified
  305 Use Proxy
  307 Temporary Redirect
  308 Permanent Redirect
  """

  status_codes = [
    300,
    301,
    302,
    303,
    304,
    305,
    307,
    308,
  ]
  if status_code not in status_codes:
    raise Exception("status_code input is not a valid status code." /
                    "Only {} are valid redirect codes".format(list(status_codes)))

  return _base_response(status_code, data)


def client_error_response(status_code, data):
  """
  400 Bad Request
  401 Unauthorized
  402 Payment Required
  403 Forbidden
  404 Not Found
  405 Method Not Allowed
  406 Not Acceptable
  407 Proxy Authentication Required
  408 Request Timeout
  409 Conflict
  410 Gone
  411 Length Required
  412 Precondition Failed
  413 Payload Too Large
  414 Request-URI Too Long
  415 Unsupported Media Type
  416 Requested Range Not Satisfiable
  417 Expectation Failed
  418 I'm a teapot
  421 Misdirected Request
  422 Unprocessable Entity
  423 Locked
  424 Failed Dependency
  426 Upgrade Required
  428 Precondition Required
  429 Too Many Requests
  431 Request Header Fields Too Large
  444 Connection Closed Without Response
  451 Unavailable For Legal Reasons
  499 Client Closed Request
  """

  status_codes = [
    400,
    401,
    402,
    403,
    404,
    405,
    406,
    407,
    408,
    409,
    410,
    411,
    412,
    413,
    414,
    415,
    416,
    417,
    418,
    421,
    422,
    423,
    424,
    426,
    428,
    429,
    431,
    444,
    451,
    499
  ]
  if status_code not in status_codes:
    raise Exception("status_code input is not a valid status code." /
                    "Only {} are valid client error codes".format(list(status_codes)))

  return _base_response(status_code, {"error_message": data})


def server_error_response(status_code, data):
  """
  500 Internal Server Error
  501 Not Implemented
  502 Bad Gateway
  503 Service Unavailable
  504 Gateway Timeout
  505 HTTP Version Not Supported
  506 Variant Also Negotiates
  507 Insufficient Storage
  508 Loop Detected
  510 Not Extended
  511 Network Authentication Required
  599 Network Connect Timeout Error
  """

  status_codes = [
    500,
    501,
    502,
    503,
    504,
    505,
    506,
    507,
    508,
    510,
    511,
    599
  ]
  if status_code not in status_codes:
    raise Exception("status_code input is not a valid status code." /
                    "Only {} are valid server error codes".format(list(status_codes)))

  return _base_response(status_code, {"error_message": data})