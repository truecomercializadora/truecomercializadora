from __future__ import absolute_import

import collections.abc
import copy
import functools
import http.client as http_client
import inspect
import io
import json
import keyword
import logging
import mimetypes
import os
import platform
import random
import re
import socket
import ssl
import time
import urllib
import uuid
from collections import OrderedDict
from email.generator import BytesGenerator, Generator
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.parser import FeedParser
from functools import reduce

import google.api_core.client_options
import google.auth
import google.auth.credentials
import google_auth_httplib2
import httplib2
import oauth2client
import oauth2client.client
import uritemplate
from google.auth.exceptions import MutualTLSChannelError
from google.auth.transport import mtls
from google.oauth2 import service_account

try:
    import ssl
except ImportError:
    _ssl_SSLError = object()
else:
    _ssl_SSLError = ssl.SSLError
from email.generator import Generator

LOGGER = logging.getLogger(__name__)
DEFAULT_CHUNK_SIZE = 100 * 1024 * 1024
MAX_URI_LENGTH = 2048
MAX_BATCH_LIMIT = 1000
_TOO_MANY_REQUESTS = 429
DEFAULT_HTTP_TIMEOUT_SEC = 60
_LEGACY_BATCH_URI = "https://www.googleapis.com/batch"

logger = logging.getLogger(__name__)
POSITIONAL_WARNING = "WARNING"
POSITIONAL_EXCEPTION = "EXCEPTION"
POSITIONAL_IGNORE = "IGNORE"
POSITIONAL_SET = frozenset(
    [POSITIONAL_WARNING, POSITIONAL_EXCEPTION, POSITIONAL_IGNORE]
)
positional_parameters_enforcement = POSITIONAL_WARNING
_SYM_LINK_MESSAGE = "File: {0}: Is a symbolic link."
_IS_DIR_MESSAGE = "{0}: Is a directory"
_MISSING_FILE_MESSAGE = "Cannot access {0}: No such file or directory"
def positional(max_positional_args):
    def positional_decorator(wrapped):
        @functools.wraps(wrapped)
        def positional_wrapper(*args, **kwargs):
            if len(args) > max_positional_args:
                plural_s = ""
                if max_positional_args != 1:
                    plural_s = "s"
                message = (
                    "{function}() takes at most {args_max} positional "
                    "argument{plural} ({args_given} given)".format(
                        function=wrapped.__name__,
                        args_max=max_positional_args,
                        args_given=len(args),
                        plural=plural_s,
                    )
                )
                if positional_parameters_enforcement == POSITIONAL_EXCEPTION:
                    raise TypeError(message)
                elif positional_parameters_enforcement == POSITIONAL_WARNING:
                    logger.warning(message)
            return wrapped(*args, **kwargs)
        return positional_wrapper
    if isinstance(max_positional_args, int):
        return positional_decorator
    else:
        args, _, _, defaults, _, _, _ = inspect.getfullargspec(max_positional_args)
        return positional(len(args) - len(defaults))(max_positional_args)
def parse_unique_urlencoded(content):
    urlencoded_params = urllib.parse.parse_qs(content)
    params = {}
    for key, value in urlencoded_params.items():
        if len(value) != 1:
            msg = "URL-encoded content contains a repeated value:" "%s -> %s" % (
                key,
                ", ".join(value),
            )
            raise ValueError(msg)
        params[key] = value[0]
    return params
def update_query_params(uri, params):
    parts = urllib.parse.urlparse(uri)
    query_params = parse_unique_urlencoded(parts.query)
    query_params.update(params)
    new_query = urllib.parse.urlencode(query_params)
    new_parts = parts._replace(query=new_query)
    return urllib.parse.urlunparse(new_parts)
def _add_query_parameter(url, name, value):
    if value is None:
        return url
    else:
        return update_query_params(url, {name: value})
def _should_retry_response(resp_status, content):
    reason = None
    if resp_status >= 500:
        return True
    if resp_status == _TOO_MANY_REQUESTS:
        return True
    if resp_status == http_client.FORBIDDEN:
        if not content:
            return False
        try:
            data = json.loads(content.decode("utf-8"))
            if isinstance(data, dict):
                error_detail_keyword = next(
                    (
                        kw
                        for kw in ["errors", "status", "message"]
                        if kw in data["error"]
                    ),
                    "",
                )
                if error_detail_keyword:
                    reason = data["error"][error_detail_keyword]
                    if isinstance(reason, list) and len(reason) > 0:
                        reason = reason[0]
                        if "reason" in reason:
                            reason = reason["reason"]
            else:
                reason = data[0]["error"]["errors"]["reason"]
        except (UnicodeDecodeError, ValueError, KeyError):
            LOGGER.warning("Invalid JSON content from response: %s", content)
            return False
        LOGGER.warning('Encountered 403 Forbidden with reason "%s"', reason)
        if reason in ("userRateLimitExceeded", "rateLimitExceeded"):
            return True
    return False
def _retry_request(
    http, num_retries, req_type, sleep, rand, uri, method, *args, **kwargs
):
    resp = None
    content = None
    exception = None
    for retry_num in range(num_retries + 1):
        if retry_num > 0:
            sleep_time = rand() * 2**retry_num
            LOGGER.warning(
                "Sleeping %.2f seconds before retry %d of %d for %s: %s %s, after %s",
                sleep_time,
                retry_num,
                num_retries,
                req_type,
                method,
                uri,
                resp.status if resp else exception,
            )
            sleep(sleep_time)
        try:
            exception = None
            resp, content = http.request(uri, method, *args, **kwargs)
        except _ssl_SSLError as ssl_error:
            exception = ssl_error
        except socket.timeout as socket_timeout:
            exception = socket_timeout
        except ConnectionError as connection_error:
            exception = connection_error
        except OSError as socket_error:
            if socket.errno.errorcode.get(socket_error.errno) not in {
                "WSAETIMEDOUT",
                "ETIMEDOUT",
                "EPIPE",
                "ECONNABORTED",
                "ECONNREFUSED",
                "ECONNRESET",
            }:
                raise
            exception = socket_error
        except httplib2.ServerNotFoundError as server_not_found_error:
            exception = server_not_found_error
        if exception:
            if retry_num == num_retries:
                raise exception
            else:
                continue
        if not _should_retry_response(resp.status, content):
            break
    return resp, content
class MediaUploadProgress(object):
    def __init__(self, resumable_progress, total_size):
        self.resumable_progress = resumable_progress
        self.total_size = total_size
    def progress(self):
        if self.total_size is not None and self.total_size != 0:
            return float(self.resumable_progress) / float(self.total_size)
        else:
            return 0.0
class MediaDownloadProgress(object):
    def __init__(self, resumable_progress, total_size):
        self.resumable_progress = resumable_progress
        self.total_size = total_size
    def progress(self):
        if self.total_size is not None and self.total_size != 0:
            return float(self.resumable_progress) / float(self.total_size)
        else:
            return 0.0
class MediaUpload(object):
    def chunksize(self):
        raise NotImplementedError()
    def mimetype(self):
        return "application/octet-stream"
    def size(self):
        return None
    def resumable(self):
        return False
    def getbytes(self, begin, end):
        raise NotImplementedError()
    def has_stream(self):
        return False
    def stream(self):
        raise NotImplementedError()
    @positional(1)
    def _to_json(self, strip=None):
        t = type(self)
        d = copy.copy(self.__dict__)
        if strip is not None:
            for member in strip:
                del d[member]
        d["_class"] = t.__name__
        d["_module"] = t.__module__
        return json.dumps(d)
    def to_json(self):
        return self._to_json()
    @classmethod
    def new_from_json(cls, s):
        data = json.loads(s)
        module = data["_module"]
        m = __import__(module, fromlist=module.split(".")[:-1])
        kls = getattr(m, data["_class"])
        from_json = getattr(kls, "from_json")
        return from_json(s)
class MediaIoBaseUpload(MediaUpload):
    @positional(3)
    def __init__(self, fd, mimetype, chunksize=DEFAULT_CHUNK_SIZE, resumable=False):
        super(MediaIoBaseUpload, self).__init__()
        self._fd = fd
        self._mimetype = mimetype
        if not (chunksize == -1 or chunksize > 0):
            raise InvalidChunkSizeError()
        self._chunksize = chunksize
        self._resumable = resumable
        self._fd.seek(0, os.SEEK_END)
        self._size = self._fd.tell()
    def chunksize(self):
        return self._chunksize
    def mimetype(self):
        return self._mimetype
    def size(self):
        return self._size
    def resumable(self):
        return self._resumable
    def getbytes(self, begin, length):
        self._fd.seek(begin)
        return self._fd.read(length)
    def has_stream(self):
        return True
    def stream(self):
        return self._fd
    def to_json(self):
        raise NotImplementedError("MediaIoBaseUpload is not serializable.")
class MediaFileUpload(MediaIoBaseUpload):
    @positional(2)
    def __init__(
        self, filename, mimetype=None, chunksize=DEFAULT_CHUNK_SIZE, resumable=False
    ):
        self._fd = None
        self._filename = filename
        self._fd = open(self._filename, "rb")
        if mimetype is None:
            mimetype, _ = mimetypes.guess_type(filename)
            if mimetype is None:
                mimetype = "application/octet-stream"
        super(MediaFileUpload, self).__init__(
            self._fd, mimetype, chunksize=chunksize, resumable=resumable
        )
    def __del__(self):
        if self._fd:
            self._fd.close()
    def to_json(self):
        return self._to_json(strip=["_fd"])
    @staticmethod
    def from_json(s):
        d = json.loads(s)
        return MediaFileUpload(
            d["_filename"],
            mimetype=d["_mimetype"],
            chunksize=d["_chunksize"],
            resumable=d["_resumable"],
        )
class MediaInMemoryUpload(MediaIoBaseUpload):
    @positional(2)
    def __init__(
        self,
        body,
        mimetype="application/octet-stream",
        chunksize=DEFAULT_CHUNK_SIZE,
        resumable=False,
    ):
        fd = io.BytesIO(body)
        super(MediaInMemoryUpload, self).__init__(
            fd, mimetype, chunksize=chunksize, resumable=resumable
        )
class MediaIoBaseDownload(object):
    @positional(3)
    def __init__(self, fd, request, chunksize=DEFAULT_CHUNK_SIZE):
        self._fd = fd
        self._request = request
        self._uri = request.uri
        self._chunksize = chunksize
        self._progress = 0
        self._total_size = None
        self._done = False
        self._sleep = time.sleep
        self._rand = random.random
        self._headers = {}
        for k, v in request.headers.items():
            if not k.lower() in ("accept", "accept-encoding", "user-agent"):
                self._headers[k] = v
    @positional(1)
    def next_chunk(self, num_retries=0):
        headers = self._headers.copy()
        headers["range"] = "bytes=%d-%d" % (
            self._progress,
            self._progress + self._chunksize - 1,
        )
        http = self._request.http
        resp, content = _retry_request(
            http,
            num_retries,
            "media download",
            self._sleep,
            self._rand,
            self._uri,
            "GET",
            headers=headers,
        )
        if resp.status in [200, 206]:
            if "content-location" in resp and resp["content-location"] != self._uri:
                self._uri = resp["content-location"]
            self._progress += len(content)
            self._fd.write(content)
            if "content-range" in resp:
                content_range = resp["content-range"]
                length = content_range.rsplit("/", 1)[1]
                self._total_size = int(length)
            elif "content-length" in resp:
                self._total_size = int(resp["content-length"])
            if self._total_size is None or self._progress == self._total_size:
                self._done = True
            return MediaDownloadProgress(self._progress, self._total_size), self._done
        elif resp.status == 416:
            content_range = resp["content-range"]
            length = content_range.rsplit("/", 1)[1]
            self._total_size = int(length)
            if self._total_size == 0:
                self._done = True
                return (
                    MediaDownloadProgress(self._progress, self._total_size),
                    self._done,
                )
        raise HttpError(resp, content, uri=self._uri)
class _StreamSlice(object):
    def __init__(self, stream, begin, chunksize):
        self._stream = stream
        self._begin = begin
        self._chunksize = chunksize
        self._stream.seek(begin)
    def read(self, n=-1):
        cur = self._stream.tell()
        end = self._begin + self._chunksize
        if n == -1 or cur + n > end:
            n = end - cur
        return self._stream.read(n)
class HttpRequest(object):
    @positional(4)
    def __init__(
        self,
        http,
        postproc,
        uri,
        method="GET",
        body=None,
        headers=None,
        methodId=None,
        resumable=None,
    ):
        self.uri = uri
        self.method = method
        self.body = body
        self.headers = headers or {}
        self.methodId = methodId
        self.http = http
        self.postproc = postproc
        self.resumable = resumable
        self.response_callbacks = []
        self._in_error_state = False
        self.body_size = len(self.body or "")
        self.resumable_uri = None
        self.resumable_progress = 0
        self._rand = random.random
        self._sleep = time.sleep
    @positional(1)
    def execute(self, http=None, num_retries=0):
        if http is None:
            http = self.http
        if self.resumable:
            body = None
            while body is None:
                _, body = self.next_chunk(http=http, num_retries=num_retries)
            return body
        if "content-length" not in self.headers:
            self.headers["content-length"] = str(self.body_size)
        if len(self.uri) > MAX_URI_LENGTH and self.method == "GET":
            self.method = "POST"
            self.headers["x-http-method-override"] = "GET"
            self.headers["content-type"] = "application/x-www-form-urlencoded"
            parsed = urllib.parse.urlparse(self.uri)
            self.uri = urllib.parse.urlunparse(
                (parsed.scheme, parsed.netloc, parsed.path, parsed.params, None, None)
            )
            self.body = parsed.query
            self.headers["content-length"] = str(len(self.body))
        resp, content = _retry_request(
            http,
            num_retries,
            "request",
            self._sleep,
            self._rand,
            str(self.uri),
            method=str(self.method),
            body=self.body,
            headers=self.headers,
        )
        for callback in self.response_callbacks:
            callback(resp)
        if resp.status >= 300:
            raise HttpError(resp, content, uri=self.uri)
        return self.postproc(resp, content)
    @positional(2)
    def add_response_callback(self, cb):
        self.response_callbacks.append(cb)
    @positional(1)
    def next_chunk(self, http=None, num_retries=0):
        if http is None:
            http = self.http
        if self.resumable.size() is None:
            size = "*"
        else:
            size = str(self.resumable.size())
        if self.resumable_uri is None:
            start_headers = copy.copy(self.headers)
            start_headers["X-Upload-Content-Type"] = self.resumable.mimetype()
            if size != "*":
                start_headers["X-Upload-Content-Length"] = size
            start_headers["content-length"] = str(self.body_size)
            resp, content = _retry_request(
                http,
                num_retries,
                "resumable URI request",
                self._sleep,
                self._rand,
                self.uri,
                method=self.method,
                body=self.body,
                headers=start_headers,
            )
            if resp.status == 200 and "location" in resp:
                self.resumable_uri = resp["location"]
            else:
                raise ResumableUploadError(resp, content)
        elif self._in_error_state:
            headers = {"Content-Range": "bytes */%s" % size, "content-length": "0"}
            resp, content = http.request(self.resumable_uri, "PUT", headers=headers)
            status, body = self._process_response(resp, content)
            if body:
                return (status, body)
        if self.resumable.has_stream():
            data = self.resumable.stream()
            if self.resumable.chunksize() == -1:
                data.seek(self.resumable_progress)
                chunk_end = self.resumable.size() - self.resumable_progress - 1
            else:
                data = _StreamSlice(
                    data, self.resumable_progress, self.resumable.chunksize()
                )
                chunk_end = min(
                    self.resumable_progress + self.resumable.chunksize() - 1,
                    self.resumable.size() - 1,
                )
        else:
            data = self.resumable.getbytes(
                self.resumable_progress, self.resumable.chunksize()
            )
            if len(data) < self.resumable.chunksize():
                size = str(self.resumable_progress + len(data))
            chunk_end = self.resumable_progress + len(data) - 1
        headers = {
            "Content-Length": str(chunk_end - self.resumable_progress + 1),
        }
        if chunk_end != -1:
            headers["Content-Range"] = "bytes %d-%d/%s" % (
                self.resumable_progress,
                chunk_end,
                size,
            )
        for retry_num in range(num_retries + 1):
            if retry_num > 0:
                self._sleep(self._rand() * 2**retry_num)
                LOGGER.warning(
                    "Retry #%d for media upload: %s %s, following status: %d"
                    % (retry_num, self.method, self.uri, resp.status)
                )
            try:
                resp, content = http.request(
                    self.resumable_uri, method="PUT", body=data, headers=headers
                )
            except:
                self._in_error_state = True
                raise
            if not _should_retry_response(resp.status, content):
                break
        return self._process_response(resp, content)
    def _process_response(self, resp, content):
        if resp.status in [200, 201]:
            self._in_error_state = False
            return None, self.postproc(resp, content)
        elif resp.status == 308:
            self._in_error_state = False
            try:
                self.resumable_progress = int(resp["range"].split("-")[1]) + 1
            except KeyError:
                self.resumable_progress = 0
            if "location" in resp:
                self.resumable_uri = resp["location"]
        else:
            self._in_error_state = True
            raise HttpError(resp, content, uri=self.uri)
        return (
            MediaUploadProgress(self.resumable_progress, self.resumable.size()),
            None,
        )
    def to_json(self):
        d = copy.copy(self.__dict__)
        if d["resumable"] is not None:
            d["resumable"] = self.resumable.to_json()
        del d["http"]
        del d["postproc"]
        del d["_sleep"]
        del d["_rand"]
        return json.dumps(d)
    @staticmethod
    def from_json(s, http, postproc):
        d = json.loads(s)
        if d["resumable"] is not None:
            d["resumable"] = MediaUpload.new_from_json(d["resumable"])
        return HttpRequest(
            http,
            postproc,
            uri=d["uri"],
            method=d["method"],
            body=d["body"],
            headers=d["headers"],
            methodId=d["methodId"],
            resumable=d["resumable"],
        )
    @staticmethod
    def null_postproc(resp, contents):
        return resp, contents
class BatchHttpRequest(object):
    @positional(1)
    def __init__(self, callback=None, batch_uri=None):
        if batch_uri is None:
            batch_uri = _LEGACY_BATCH_URI
        if batch_uri == _LEGACY_BATCH_URI:
            LOGGER.warning(
                "You have constructed a BatchHttpRequest using the legacy batch "
                "endpoint %s. This endpoint will be turned down on August 12, 2020. "
                "Please provide the API-specific endpoint or use "
                "service.new_batch_http_request(). For more details see "
                "https://developers.googleblog.com/2018/03/discontinuing-support-for-json-rpc-and.html"
                "and https://developers.google.com/api-client-library/python/guide/batch.",
                _LEGACY_BATCH_URI,
            )
        self._batch_uri = batch_uri
        self._callback = callback
        self._requests = {}
        self._callbacks = {}
        self._order = []
        self._last_auto_id = 0
        self._base_id = None
        self._responses = {}
        self._refreshed_credentials = {}
    def _refresh_and_apply_credentials(self, request, http):
        creds = None
        request_credentials = False
        if request.http is not None:
            creds = get_credentials_from_http(request.http)
            request_credentials = True
        if creds is None and http is not None:
            creds = get_credentials_from_http(http)
        if creds is not None:
            if id(creds) not in self._refreshed_credentials:
                refresh_credentials(creds)
                self._refreshed_credentials[id(creds)] = 1
        if request.http is None or not request_credentials:
            apply_credentials(creds, request.headers)
    def _id_to_header(self, id_):
        if self._base_id is None:
            self._base_id = uuid.uuid4()
        return "<%s + %s>" % (self._base_id, urllib.parse.quote(id_))
    def _header_to_id(self, header):
        if header[0] != "<" or header[-1] != ">":
            raise BatchError("Invalid value for Content-ID: %s" % header)
        if "+" not in header:
            raise BatchError("Invalid value for Content-ID: %s" % header)
        base, id_ = header[1:-1].split(" + ", 1)
        return urllib.parse.unquote(id_)
    def _serialize_request(self, request):
        parsed = urllib.parse.urlparse(request.uri)
        request_line = urllib.parse.urlunparse(
            ("", "", parsed.path, parsed.params, parsed.query, "")
        )
        status_line = request.method + " " + request_line + " HTTP/1.1\n"
        major, minor = request.headers.get("content-type", "application/json").split(
            "/"
        )
        msg = MIMENonMultipart(major, minor)
        headers = request.headers.copy()
        if request.http is not None:
            credentials = get_credentials_from_http(request.http)
            if credentials is not None:
                apply_credentials(credentials, headers)
        if "content-type" in headers:
            del headers["content-type"]
        for key, value in headers.items():
            msg[key] = value
        msg["Host"] = parsed.netloc
        msg.set_unixfrom(None)
        if request.body is not None:
            msg.set_payload(request.body)
            msg["content-length"] = str(len(request.body))
        fp = io.StringIO()
        g = Generator(fp, maxheaderlen=0)
        g.flatten(msg, unixfrom=False)
        body = fp.getvalue()
        return status_line + body
    def _deserialize_response(self, payload):
        status_line, payload = payload.split("\n", 1)
        protocol, status, reason = status_line.split(" ", 2)
        parser = FeedParser()
        parser.feed(payload)
        msg = parser.close()
        msg["status"] = status
        resp = httplib2.Response(msg)
        resp.reason = reason
        resp.version = int(protocol.split("/", 1)[1].replace(".", ""))
        content = payload.split("\r\n\r\n", 1)[1]
        return resp, content
    def _new_id(self):
        self._last_auto_id += 1
        while str(self._last_auto_id) in self._requests:
            self._last_auto_id += 1
        return str(self._last_auto_id)
    @positional(2)
    def add(self, request, callback=None, request_id=None):
        if len(self._order) >= MAX_BATCH_LIMIT:
            raise BatchError(
                "Exceeded the maximum calls(%d) in a single batch request."
                % MAX_BATCH_LIMIT
            )
        if request_id is None:
            request_id = self._new_id()
        if request.resumable is not None:
            raise BatchError("Media requests cannot be used in a batch request.")
        if request_id in self._requests:
            raise KeyError("A request with this ID already exists: %s" % request_id)
        self._requests[request_id] = request
        self._callbacks[request_id] = callback
        self._order.append(request_id)
    def _execute(self, http, order, requests):
        message = MIMEMultipart("mixed")
        setattr(message, "_write_headers", lambda self: None)
        for request_id in order:
            request = requests[request_id]
            msg = MIMENonMultipart("application", "http")
            msg["Content-Transfer-Encoding"] = "binary"
            msg["Content-ID"] = self._id_to_header(request_id)
            body = self._serialize_request(request)
            msg.set_payload(body)
            message.attach(msg)
        fp = io.StringIO()
        g = Generator(fp, mangle_from_=False)
        g.flatten(message, unixfrom=False)
        body = fp.getvalue()
        headers = {}
        headers["content-type"] = (
            "multipart/mixed; " 'boundary="%s"'
        ) % message.get_boundary()
        resp, content = http.request(
            self._batch_uri, method="POST", body=body, headers=headers
        )
        if resp.status >= 300:
            raise HttpError(resp, content, uri=self._batch_uri)
        header = "content-type: %s\r\n\r\n" % resp["content-type"]
        content = content.decode("utf-8")
        for_parser = header + content
        parser = FeedParser()
        parser.feed(for_parser)
        mime_response = parser.close()
        if not mime_response.is_multipart():
            raise BatchError(
                "Response not in multipart/mixed format.", resp=resp, content=content
            )
        for part in mime_response.get_payload():
            request_id = self._header_to_id(part["Content-ID"])
            response, content = self._deserialize_response(part.get_payload())
            if isinstance(content, str):
                content = content.encode("utf-8")
            self._responses[request_id] = (response, content)
    @positional(1)
    def execute(self, http=None):
        if len(self._order) == 0:
            return None
        if http is None:
            for request_id in self._order:
                request = self._requests[request_id]
                if request is not None:
                    http = request.http
                    break
        if http is None:
            raise ValueError("Missing a valid http object.")
        creds = get_credentials_from_http(http)
        if creds is not None:
            if not is_valid(creds):
                LOGGER.info("Attempting refresh to obtain initial access_token")
                refresh_credentials(creds)
        self._execute(http, self._order, self._requests)
        redo_requests = {}
        redo_order = []
        for request_id in self._order:
            resp, content = self._responses[request_id]
            if resp["status"] == "401":
                redo_order.append(request_id)
                request = self._requests[request_id]
                self._refresh_and_apply_credentials(request, http)
                redo_requests[request_id] = request
        if redo_requests:
            self._execute(http, redo_order, redo_requests)
        for request_id in self._order:
            resp, content = self._responses[request_id]
            request = self._requests[request_id]
            callback = self._callbacks[request_id]
            response = None
            exception = None
            try:
                if resp.status >= 300:
                    raise HttpError(resp, content, uri=request.uri)
                response = request.postproc(resp, content)
            except HttpError as e:
                exception = e
            if callback is not None:
                callback(request_id, response, exception)
            if self._callback is not None:
                self._callback(request_id, response, exception)
class HttpRequestMock(object):
    def __init__(self, resp, content, postproc):
        self.resp = resp
        self.content = content
        self.postproc = postproc
        if resp is None:
            self.resp = httplib2.Response({"status": 200, "reason": "OK"})
        if "reason" in self.resp:
            self.resp.reason = self.resp["reason"]
    def execute(self, http=None):
        return self.postproc(self.resp, self.content)
class RequestMockBuilder(object):
    def __init__(self, responses, check_unexpected=False):
        self.responses = responses
        self.check_unexpected = check_unexpected
    def __call__(
        self,
        http,
        postproc,
        uri,
        method="GET",
        body=None,
        headers=None,
        methodId=None,
        resumable=None,
    ):
        if methodId in self.responses:
            response = self.responses[methodId]
            resp, content = response[:2]
            if len(response) > 2:
                expected_body = response[2]
                if bool(expected_body) != bool(body):
                    raise UnexpectedBodyError(expected_body, body)
                if isinstance(expected_body, str):
                    expected_body = json.loads(expected_body)
                body = json.loads(body)
                if body != expected_body:
                    raise UnexpectedBodyError(expected_body, body)
            return HttpRequestMock(resp, content, postproc)
        elif self.check_unexpected:
            raise UnexpectedMethodError(methodId=methodId)
        else:
            model = JsonModel(False)
            return HttpRequestMock(None, "{}", model.response)
class HttpMock(object):
    def __init__(self, filename=None, headers=None):
        if headers is None:
            headers = {"status": "200"}
        if filename:
            with open(filename, "rb") as f:
                self.data = f.read()
        else:
            self.data = None
        self.response_headers = headers
        self.headers = None
        self.uri = None
        self.method = None
        self.body = None
        self.headers = None
    def request(
        self,
        uri,
        method="GET",
        body=None,
        headers=None,
        redirections=1,
        connection_type=None,
    ):
        self.uri = uri
        self.method = method
        self.body = body
        self.headers = headers
        return httplib2.Response(self.response_headers), self.data
    def close(self):
        return None
class HttpMockSequence(object):
    def __init__(self, iterable):
        self._iterable = iterable
        self.follow_redirects = True
        self.request_sequence = list()
    def request(
        self,
        uri,
        method="GET",
        body=None,
        headers=None,
        redirections=1,
        connection_type=None,
    ):
        self.request_sequence.append((uri, method, body, headers))
        resp, content = self._iterable.pop(0)
        if isinstance(content, str):
            content = content.encode("utf-8")
        if content == b"echo_request_headers":
            content = headers
        elif content == b"echo_request_headers_as_json":
            content = json.dumps(headers)
        elif content == b"echo_request_body":
            if hasattr(body, "read"):
                content = body.read()
            else:
                content = body
        elif content == b"echo_request_uri":
            content = uri
        if isinstance(content, str):
            content = content.encode("utf-8")
        return httplib2.Response(resp), content
def set_user_agent(http, user_agent):
    request_orig = http.request
    def new_request(
        uri,
        method="GET",
        body=None,
        headers=None,
        redirections=httplib2.DEFAULT_MAX_REDIRECTS,
        connection_type=None,
    ):
        if headers is None:
            headers = {}
        if "user-agent" in headers:
            headers["user-agent"] = user_agent + " " + headers["user-agent"]
        else:
            headers["user-agent"] = user_agent
        resp, content = request_orig(
            uri,
            method=method,
            body=body,
            headers=headers,
            redirections=redirections,
            connection_type=connection_type,
        )
        return resp, content
    http.request = new_request
    return http
def tunnel_patch(http):
    request_orig = http.request
    def new_request(
        uri,
        method="GET",
        body=None,
        headers=None,
        redirections=httplib2.DEFAULT_MAX_REDIRECTS,
        connection_type=None,
    ):
        if headers is None:
            headers = {}
        if method == "PATCH":
            if "oauth_token" in headers.get("authorization", ""):
                LOGGER.warning(
                    "OAuth 1.0 request made with Credentials after tunnel_patch."
                )
            headers["x-http-method-override"] = "PATCH"
            method = "POST"
        resp, content = request_orig(
            uri,
            method=method,
            body=body,
            headers=headers,
            redirections=redirections,
            connection_type=connection_type,
        )
        return resp, content
    http.request = new_request
    return http
def build_http():
    if socket.getdefaulttimeout() is not None:
        http_timeout = socket.getdefaulttimeout()
    else:
        http_timeout = DEFAULT_HTTP_TIMEOUT_SEC
    http = httplib2.Http(timeout=http_timeout)
    try:
        http.redirect_codes = http.redirect_codes - {308}
    except AttributeError:
        pass
    return http
from email.generator import BytesGenerator


try:
    import google_auth_httplib2
except ImportError:  
    google_auth_httplib2 = None
httplib2.RETRIES = 1
logger = logging.getLogger(__name__)
URITEMPLATE = re.compile("{[^}]*}")
VARNAME = re.compile("[a-zA-Z0-9_-]+")
DISCOVERY_URI = (
    "https://www.googleapis.com/discovery/v1/apis/" "{api}/{apiVersion}/rest"
)
V1_DISCOVERY_URI = DISCOVERY_URI
V2_DISCOVERY_URI = (
    "https://{api}.googleapis.com/$discovery/rest?" "version={apiVersion}"
)
DEFAULT_METHOD_DOC = "A description of how to use this function"
HTTP_PAYLOAD_METHODS = frozenset(["PUT", "POST", "PATCH"])
_MEDIA_SIZE_BIT_SHIFTS = {"KB": 10, "MB": 20, "GB": 30, "TB": 40}
BODY_PARAMETER_DEFAULT_VALUE = {"description": "The request body.", "type": "object"}
MEDIA_BODY_PARAMETER_DEFAULT_VALUE = {
    "description": (
        "The filename of the media request body, or an instance "
        "of a MediaUpload object."
    ),
    "type": "string",
    "required": False,
}
MEDIA_MIME_TYPE_PARAMETER_DEFAULT_VALUE = {
    "description": (
        "The MIME type of the media request body, or an instance "
        "of a MediaUpload object."
    ),
    "type": "string",
    "required": False,
}
_PAGE_TOKEN_NAMES = ("pageToken", "nextPageToken")
GOOGLE_API_USE_CLIENT_CERTIFICATE = "GOOGLE_API_USE_CLIENT_CERTIFICATE"
GOOGLE_API_USE_MTLS_ENDPOINT = "GOOGLE_API_USE_MTLS_ENDPOINT"
STACK_QUERY_PARAMETERS = frozenset(["trace", "pp", "userip", "strict"])
STACK_QUERY_PARAMETER_DEFAULT_VALUE = {"type": "string", "location": "query"}
RESERVED_WORDS = frozenset(["body"])
class _BytesGenerator(BytesGenerator):
    _write_lines = BytesGenerator.write
def fix_method_name(name):
    name = name.replace("$", "_").replace("-", "_")
    if keyword.iskeyword(name) or name in RESERVED_WORDS:
        return name + "_"
    else:
        return name
def key2param(key):
    result = []
    key = list(key)
    if not key[0].isalpha():
        result.append("x")
    for c in key:
        if c.isalnum():
            result.append(c)
        else:
            result.append("_")
    return "".join(result)
@positional(2)
def build(
    serviceName,
    version,
    http=None,
    discoveryServiceUrl=None,
    developerKey=None,
    model=None,
    requestBuilder=HttpRequest,
    credentials=None,
    cache_discovery=True,
    cache=None,
    client_options=None,
    adc_cert_path=None,
    adc_key_path=None,
    num_retries=1,
    static_discovery=None,
    always_use_jwt_access=False,
):
    params = {"api": serviceName, "apiVersion": version}
    if static_discovery is None:
        if discoveryServiceUrl is None:
            static_discovery = True
        else:
            static_discovery = False
    if http is None:
        discovery_http = build_http()
    else:
        discovery_http = http
    service = None
    for discovery_url in _discovery_service_uri_options(discoveryServiceUrl, version):
        requested_url = uritemplate.expand(discovery_url, params)
        try:
            content = _retrieve_discovery_doc(
                requested_url,
                discovery_http,
                cache_discovery,
                serviceName,
                version,
                cache,
                developerKey,
                num_retries=num_retries,
                static_discovery=static_discovery,
            )
            service = build_from_document(
                content,
                base=discovery_url,
                http=http,
                developerKey=developerKey,
                model=model,
                requestBuilder=requestBuilder,
                credentials=credentials,
                client_options=client_options,
                adc_cert_path=adc_cert_path,
                adc_key_path=adc_key_path,
                always_use_jwt_access=always_use_jwt_access,
            )
            break  
        except HttpError as e:
            if e.resp.status == http_client.NOT_FOUND:
                continue
            else:
                raise e
    if http is None:
        discovery_http.close()
    if service is None:
        raise UnknownApiNameOrVersion("name: %s  version: %s" % (serviceName, version))
    else:
        return service
def _discovery_service_uri_options(discoveryServiceUrl, version):
    if discoveryServiceUrl is not None:
        return [discoveryServiceUrl]
    if version is None:
        logger.warning(
            "Discovery V1 does not support empty versions. Defaulting to V2..."
        )
        return [V2_DISCOVERY_URI]
    else:
        return [DISCOVERY_URI, V2_DISCOVERY_URI]

LOGGER = logging.getLogger(__name__)
DISCOVERY_DOC_MAX_AGE = 60 * 60 * 24  
DISCOVERY_DOC_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "documents"
)
def autodetect():
    if "GAE_ENV" in os.environ:
        try:
            from . import appengine_memcache
            return appengine_memcache.cache
        except Exception:
            pass
    try:
        from . import file_cache
        return file_cache.cache
    except Exception:
        LOGGER.info(
            "file_cache is only supported with oauth2client<4.0.0", exc_info=False
        )
        return None
def get_static_doc(serviceName, version):
    content = None
    doc_name = "{}.{}.json".format(serviceName, version)
    try:
        with open(os.path.join(DISCOVERY_DOC_DIR, doc_name), "r") as f:
            content = f.read()
    except FileNotFoundError:
        pass
    return content
def _retrieve_discovery_doc(
    url,
    http,
    cache_discovery,
    serviceName,
    version,
    cache=None,
    developerKey=None,
    num_retries=1,
    static_discovery=True,
):
    if cache_discovery:
        if cache is None:
            cache = autodetect()
        if cache:
            content = cache.get(url)
            if content:
                return content
    if static_discovery:
        content = '{\n  "auth": {\n    "oauth2": {\n      "scopes": {\n        "https://www.googleapis.com/auth/chat.bot": {\n          "description": "Private Service: https://www.googleapis.com/auth/chat.bot"\n        },\n        "https://www.googleapis.com/auth/chat.delete": {\n          "description": "Delete conversations and spaces & remove access to associated files in Google Chat"\n        },\n        "https://www.googleapis.com/auth/chat.import": {\n          "description": "Import spaces, messages, and memberships into Google Chat."\n        },\n        "https://www.googleapis.com/auth/chat.memberships": {\n          "description": "View, add, and remove members from conversations in Google Chat"\n        },\n        "https://www.googleapis.com/auth/chat.memberships.app": {\n          "description": "Add and remove itself from conversations in Google Chat"\n        },\n        "https://www.googleapis.com/auth/chat.memberships.readonly": {\n          "description": "View members in Google Chat conversations."\n        },\n        "https://www.googleapis.com/auth/chat.messages": {\n          "description": "View, compose, send, update, and delete messages, and add, view, and delete reactions to messages."\n        },\n        "https://www.googleapis.com/auth/chat.messages.create": {\n          "description": "Compose and send messages in Google Chat"\n        },\n        "https://www.googleapis.com/auth/chat.messages.reactions": {\n          "description": "View, add, and delete reactions to messages in Google Chat"\n        },\n        "https://www.googleapis.com/auth/chat.messages.reactions.create": {\n          "description": "Add reactions to messages in Google Chat"\n        },\n        "https://www.googleapis.com/auth/chat.messages.reactions.readonly": {\n          "description": "View reactions to messages in Google Chat"\n        },\n        "https://www.googleapis.com/auth/chat.messages.readonly": {\n          "description": "View messages and reactions in Google Chat"\n        },\n        "https://www.googleapis.com/auth/chat.spaces": {\n          "description": "Create conversations and spaces and view or update metadata (including history settings) in Google Chat"\n        },\n        "https://www.googleapis.com/auth/chat.spaces.create": {\n          "description": "Create new conversations in Google Chat"\n        },\n        "https://www.googleapis.com/auth/chat.spaces.readonly": {\n          "description": "View chat and spaces in Google Chat"\n        }\n      }\n    }\n  },\n  "basePath": "",\n  "baseUrl": "https://chat.googleapis.com/",\n  "batchPath": "batch",\n  "canonicalName": "Hangouts Chat",\n  "description": "Enables apps to fetch information and perform actions in Google Chat. Authentication is a prerequisite for using the Google Chat REST API.",\n  "discoveryVersion": "v1",\n  "documentationLink": "https://developers.google.com/hangouts/chat",\n  "fullyEncodeReservedExpansion": true,\n  "icons": {\n    "x16": "http://www.google.com/images/icons/product/search-16.gif",\n    "x32": "http://www.google.com/images/icons/product/search-32.gif"\n  },\n  "id": "chat:v1",\n  "kind": "discovery#restDescription",\n  "mtlsRootUrl": "https://chat.mtls.googleapis.com/",\n  "name": "chat",\n  "ownerDomain": "google.com",\n  "ownerName": "Google",\n  "parameters": {\n    "$.xgafv": {\n      "description": "V1 error format.",\n      "enum": [\n        "1",\n        "2"\n      ],\n      "enumDescriptions": [\n        "v1 error format",\n        "v2 error format"\n      ],\n      "location": "query",\n      "type": "string"\n    },\n    "access_token": {\n      "description": "OAuth access token.",\n      "location": "query",\n      "type": "string"\n    },\n    "alt": {\n      "default": "json",\n      "description": "Data format for response.",\n      "enum": [\n        "json",\n        "media",\n        "proto"\n      ],\n      "enumDescriptions": [\n        "Responses with Content-Type of application/json",\n        "Media download with context-dependent Content-Type",\n        "Responses with Content-Type of application/x-protobuf"\n      ],\n      "location": "query",\n      "type": "string"\n    },\n    "callback": {\n      "description": "JSONP",\n      "location": "query",\n      "type": "string"\n    },\n    "fields": {\n      "description": "Selector specifying which fields to include in a partial response.",\n      "location": "query",\n      "type": "string"\n    },\n    "key": {\n      "description": "API key. Your API key identifies your project and provides you with API access, quota, and reports. Required unless you provide an OAuth 2.0 token.",\n      "location": "query",\n      "type": "string"\n    },\n    "oauth_token": {\n      "description": "OAuth 2.0 token for the current user.",\n      "location": "query",\n      "type": "string"\n    },\n    "prettyPrint": {\n      "default": "true",\n      "description": "Returns response with indentations and line breaks.",\n      "location": "query",\n      "type": "boolean"\n    },\n    "quotaUser": {\n      "description": "Available to use for quota purposes for server-side applications. Can be any arbitrary string assigned to a user, but should not exceed 40 characters.",\n      "location": "query",\n      "type": "string"\n    },\n    "uploadType": {\n      "description": "Legacy upload protocol for media (e.g. \\"media\\", \\"multipart\\").",\n      "location": "query",\n      "type": "string"\n    },\n    "upload_protocol": {\n      "description": "Upload protocol for media (e.g. \\"raw\\", \\"multipart\\").",\n      "location": "query",\n      "type": "string"\n    }\n  },\n  "protocol": "rest",\n  "resources": {\n    "media": {\n      "methods": {\n        "download": {\n          "description": "Downloads media. Download is supported on the URI `/v1/media/{+name}?alt=media`.",\n          "flatPath": "v1/media/{mediaId}",\n          "httpMethod": "GET",\n          "id": "chat.media.download",\n          "parameterOrder": [\n            "resourceName"\n          ],\n          "parameters": {\n            "resourceName": {\n              "description": "Name of the media that is being downloaded. See ReadRequest.resource_name.",\n              "location": "path",\n              "pattern": "^.*$",\n              "required": true,\n              "type": "string"\n            }\n          },\n          "path": "v1/media/{+resourceName}",\n          "response": {\n            "$ref": "Media"\n          },\n          "scopes": [\n            "https://www.googleapis.com/auth/chat.bot",\n            "https://www.googleapis.com/auth/chat.messages",\n            "https://www.googleapis.com/auth/chat.messages.readonly"\n          ],\n          "supportsMediaDownload": true\n        },\n        "upload": {\n          "description": "Uploads an attachment. For an example, see [Upload media as a file attachment](https://developers.google.com/chat/api/guides/v1/media-and-attachments/upload). Requires user [authentication](https://developers.google.com/chat/api/guides/auth/users) and the `chat.messages` or `chat.messages.create` authorization scope. You can upload attachments up to 200 MB. Certain file types aren\'t supported. For details, see [File types blocked by Google Chat](https://support.google.com/chat/answer/7651457?&co=GENIE.Platform%3DDesktop#File%20types%20blocked%20in%20Google%20Chat).",\n          "flatPath": "v1/spaces/{spacesId}/attachments:upload",\n          "httpMethod": "POST",\n          "id": "chat.media.upload",\n          "mediaUpload": {\n            "accept": [\n              "*/*"\n            ],\n            "maxSize": "209715200",\n            "protocols": {\n              "resumable": {\n                "multipart": true,\n                "path": "/resumable/upload/v1/{+parent}/attachments:upload"\n              },\n              "simple": {\n                "multipart": true,\n                "path": "/upload/v1/{+parent}/attachments:upload"\n              }\n            }\n          },\n          "parameterOrder": [\n            "parent"\n          ],\n          "parameters": {\n            "parent": {\n              "description": "Required. Resource name of the Chat space in which the attachment is uploaded. Format \\"spaces/{space}\\".",\n              "location": "path",\n              "pattern": "^spaces/[^/]+$",\n              "required": true,\n              "type": "string"\n            }\n          },\n          "path": "v1/{+parent}/attachments:upload",\n          "request": {\n            "$ref": "UploadAttachmentRequest"\n          },\n          "response": {\n            "$ref": "UploadAttachmentResponse"\n          },\n          "scopes": [\n            "https://www.googleapis.com/auth/chat.import",\n            "https://www.googleapis.com/auth/chat.messages",\n            "https://www.googleapis.com/auth/chat.messages.create"\n          ],\n          "supportsMediaUpload": true\n        }\n      }\n    },\n    "spaces": {\n      "methods": {\n        "create": {\n          "description": "Creates a named space. Spaces grouped by topics or that have guest access aren\'t supported. For an example, see [Create a space](https://developers.google.com/chat/api/guides/v1/spaces/create). Requires [user authentication](https://developers.google.com/chat/api/guides/auth/users) and the `chat.spaces.create` or `chat.spaces` scope.",\n          "flatPath": "v1/spaces",\n          "httpMethod": "POST",\n          "id": "chat.spaces.create",\n          "parameterOrder": [],\n          "parameters": {\n            "requestId": {\n              "description": "Optional. A unique identifier for this request. A random UUID is recommended. Specifying an existing request ID returns the space created with that ID instead of creating a new space. Specifying an existing request ID from the same Chat app with a different authenticated user returns an error.",\n              "location": "query",\n              "type": "string"\n            }\n          },\n          "path": "v1/spaces",\n          "request": {\n            "$ref": "Space"\n          },\n          "response": {\n            "$ref": "Space"\n          },\n          "scopes": [\n            "https://www.googleapis.com/auth/chat.import",\n            "https://www.googleapis.com/auth/chat.spaces",\n            "https://www.googleapis.com/auth/chat.spaces.create"\n          ]\n        },\n        "delete": {\n          "description": "Deletes a named space. Always performs a cascading delete, which means that the space\'s child resources\\u2014like messages posted in the space and memberships in the space\\u2014are also deleted. For an example, see [Delete a space](https://developers.google.com/chat/api/guides/v1/spaces/delete). Requires [user authentication](https://developers.google.com/chat/api/guides/auth/users) from a user who has permission to delete the space, and the `chat.delete` scope.",\n          "flatPath": "v1/spaces/{spacesId}",\n          "httpMethod": "DELETE",\n          "id": "chat.spaces.delete",\n          "parameterOrder": [\n            "name"\n          ],\n          "parameters": {\n            "name": {\n              "description": "Required. Resource name of the space to delete. Format: `spaces/{space}`",\n              "location": "path",\n              "pattern": "^spaces/[^/]+$",\n              "required": true,\n              "type": "string"\n            }\n          },\n          "path": "v1/{+name}",\n          "response": {\n            "$ref": "Empty"\n          },\n          "scopes": [\n            "https://www.googleapis.com/auth/chat.delete",\n            "https://www.googleapis.com/auth/chat.import"\n          ]\n        },\n        "findDirectMessage": {\n          "description": "Returns the existing direct message with the specified user. If no direct message space is found, returns a `404 NOT_FOUND` error. For an example, see [Find a direct message](/chat/api/guides/v1/spaces/find-direct-message). With [user authentication](https://developers.google.com/chat/api/guides/auth/users), returns the direct message space between the specified user and the authenticated user. With [service account authentication](https://developers.google.com/chat/api/guides/auth/service-accounts), returns the direct message space between the specified user and the calling Chat app. Requires [user authentication](https://developers.google.com/chat/api/guides/auth/users) or [service account authentication](https://developers.google.com/chat/api/guides/auth/service-accounts).",\n          "flatPath": "v1/spaces:findDirectMessage",\n          "httpMethod": "GET",\n          "id": "chat.spaces.findDirectMessage",\n          "parameterOrder": [],\n          "parameters": {\n            "name": {\n              "description": "Required. Resource name of the user to find direct message with. Format: `users/{user}`, where `{user}` is either the `{person_id}` for the [person](https://developers.google.com/people/api/rest/v1/people) from the People API, or the `id` for the [user](https://developers.google.com/admin-sdk/directory/reference/rest/v1/users) in the Directory API. For example, if the People API `Person.resourceName` is `people/123456789`, you can find a direct message with that person by using `users/123456789` as the `name`.",\n              "location": "query",\n              "type": "string"\n            }\n          },\n          "path": "v1/spaces:findDirectMessage",\n          "response": {\n            "$ref": "Space"\n          },\n          "scopes": [\n            "https://www.googleapis.com/auth/chat.bot",\n            "https://www.googleapis.com/auth/chat.spaces",\n            "https://www.googleapis.com/auth/chat.spaces.readonly"\n          ]\n        },\n        "get": {\n          "description": "Returns details about a space. For an example, see [Get a space](https://developers.google.com/chat/api/guides/v1/spaces/get). Requires [authentication](https://developers.google.com/chat/api/guides/auth). Fully supports [service account authentication](https://developers.google.com/chat/api/guides/auth/service-accounts) and [user authentication](https://developers.google.com/chat/api/guides/auth/users). [User authentication](https://developers.google.com/chat/api/guides/auth/users) requires the `chat.spaces` or `chat.spaces.readonly` authorization scope.",\n          "flatPath": "v1/spaces/{spacesId}",\n          "httpMethod": "GET",\n          "id": "chat.spaces.get",\n          "parameterOrder": [\n            "name"\n          ],\n          "parameters": {\n            "name": {\n              "description": "Required. Resource name of the space, in the form \\"spaces/*\\". Format: `spaces/{space}`",\n              "location": "path",\n              "pattern": "^spaces/[^/]+$",\n              "required": true,\n              "type": "string"\n            }\n          },\n          "path": "v1/{+name}",\n          "response": {\n            "$ref": "Space"\n          },\n          "scopes": [\n            "https://www.googleapis.com/auth/chat.bot",\n            "https://www.googleapis.com/auth/chat.spaces",\n            "https://www.googleapis.com/auth/chat.spaces.readonly"\n          ]\n        },\n        "list": {\n          "description": "Lists spaces the caller is a member of. Group chats and DMs aren\'t listed until the first message is sent. For an example, see [List spaces](https://developers.google.com/chat/api/guides/v1/spaces/list). Requires [authentication](https://developers.google.com/chat/api/guides/auth). Fully supports [service account authentication](https://developers.google.com/chat/api/guides/auth/service-accounts) and [user authentication](https://developers.google.com/chat/api/guides/auth/users) requires the `chat.spaces` or `chat.spaces.readonly` authorization scope. Lists spaces visible to the caller or authenticated user. Group chats and DMs aren\'t listed until the first message is sent.",\n          "flatPath": "v1/spaces",\n          "httpMethod": "GET",\n          "id": "chat.spaces.list",\n          "parameterOrder": [],\n          "parameters": {\n            "filter": {\n              "description": "Optional. A query filter. Requires [user authentication](https://developers.google.com/chat/api/guides/auth/users). You can filter spaces by the space type ([`space_type`](https://developers.google.com/chat/api/reference/rest/v1/spaces#spacetype)). To filter by space type, you must specify valid enum value, such as `SPACE` or `GROUP_CHAT` (the `space_type` can\'t be `SPACE_TYPE_UNSPECIFIED`). To query for multiple space types, use the `OR` operator. For example, the following queries are valid: ``` space_type = \\"SPACE\\" spaceType = \\"GROUP_CHAT\\" OR spaceType = \\"DIRECT_MESSAGE\\" ``` Invalid queries are rejected by the server with an `INVALID_ARGUMENT` error. With [service account authentication](https://developers.google.com/chat/api/guides/auth/service-accounts), this field is ignored and the query always returns all spaces. But the Chat API still validates the query syntax with service accounts, so invalid queries are still rejected.",\n              "location": "query",\n              "type": "string"\n            },\n            "pageSize": {\n              "description": "Optional. The maximum number of spaces to return. The service might return fewer than this value. If unspecified, at most 100 spaces are returned. The maximum value is 1,000. If you use a value more than 1,000, it\'s automatically changed to 1,000. Negative values return an `INVALID_ARGUMENT` error.",\n              "format": "int32",\n              "location": "query",\n              "type": "integer"\n            },\n            "pageToken": {\n              "description": "Optional. A page token, received from a previous list spaces call. Provide this parameter to retrieve the subsequent page. When paginating, the filter value should match the call that provided the page token. Passing a different value may lead to unexpected results.",\n              "location": "query",\n              "type": "string"\n            }\n          },\n          "path": "v1/spaces",\n          "response": {\n            "$ref": "ListSpacesResponse"\n          },\n          "scopes": [\n            "https://www.googleapis.com/auth/chat.bot",\n            "https://www.googleapis.com/auth/chat.spaces",\n            "https://www.googleapis.com/auth/chat.spaces.readonly"\n          ]\n        },\n        "patch": {\n          "description": "Updates a space. For an example, see [Update a space](https://developers.google.com/chat/api/guides/v1/spaces/update). Requires [user authentication](https://developers.google.com/chat/api/guides/auth/users) and the `chat.spaces` scope.",\n          "flatPath": "v1/spaces/{spacesId}",\n          "httpMethod": "PATCH",\n          "id": "chat.spaces.patch",\n          "parameterOrder": [\n            "name"\n          ],\n          "parameters": {\n            "name": {\n              "description": "Resource name of the space. Format: `spaces/{space}`",\n              "location": "path",\n              "pattern": "^spaces/[^/]+$",\n              "required": true,\n              "type": "string"\n            },\n            "updateMask": {\n              "description": "Required. The updated field paths, comma separated if there are multiple. Currently supported field paths: - `display_name` (Only supports changing the display name of a space with the `SPACE` type, or when also including the `space_type` mask to change a `GROUP_CHAT` space type to `SPACE`. Trying to update the display name of a `GROUP_CHAT` or a `DIRECT_MESSAGE` space results in an invalid argument error.) - `space_type` (Only supports changing a `GROUP_CHAT` space type to `SPACE`. Include `display_name` together with `space_type` in the update mask and ensure that the specified space has a non-empty display name and the `SPACE` space type. Including the `space_type` mask and the `SPACE` type in the specified space when updating the display name is optional if the existing space already has the `SPACE` type. Trying to update the space type in other ways results in an invalid argument error). - `space_details` - `space_history_state` (Supports [turning history on or off for the space](https://support.google.com/chat/answer/7664687) if [the organization allows users to change their history setting](https://support.google.com/a/answer/7664184). Warning: mutually exclusive with all other field paths.)",\n              "format": "google-fieldmask",\n              "location": "query",\n              "type": "string"\n            }\n          },\n          "path": "v1/{+name}",\n          "request": {\n            "$ref": "Space"\n          },\n          "response": {\n            "$ref": "Space"\n          },\n          "scopes": [\n            "https://www.googleapis.com/auth/chat.import",\n            "https://www.googleapis.com/auth/chat.spaces"\n          ]\n        },\n        "setup": {\n          "description": "Creates a space and adds specified users to it. The calling user is automatically added to the space, and shouldn\'t be specified as a membership in the request. For an example, see [Set up a space](https://developers.google.com/chat/api/guides/v1/spaces/set-up). To specify the human members to add, add memberships with the appropriate `member.name` in the `SetUpSpaceRequest`. To add a human user, use `users/{user}`, where `{user}` is either the `{person_id}` for the [person](https://developers.google.com/people/api/rest/v1/people) from the People API, or the `id` for the [user](https://developers.google.com/admin-sdk/directory/reference/rest/v1/users) in the Admin SDK Directory API. For example, if the People API `Person` `resourceName` is `people/123456789`, you can add the user to the space by including a membership with `users/123456789` as the `member.name`. For a space or group chat, if the caller blocks or is blocked by some members, then those members aren\'t added to the created space. To create a direct message (DM) between the calling user and another human user, specify exactly one membership to represent the human user. If one user blocks the other, the request fails and the DM isn\'t created. To create a DM between the calling user and the calling app, set `Space.singleUserBotDm` to `true` and don\'t specify any memberships. You can only use this method to set up a DM with the calling app. To add the calling app as a member of a space or an existing DM between two human users, see [create a membership](https://developers.google.com/chat/api/guides/v1/members/create). If a DM already exists between two users, even when one user blocks the other at the time a request is made, then the existing DM is returned. Spaces with threaded replies or guest access aren\'t supported. Requires [user authentication](https://developers.google.com/chat/api/guides/auth/users) and the `chat.spaces.create` or `chat.spaces` scope.",\n          "flatPath": "v1/spaces:setup",\n          "httpMethod": "POST",\n          "id": "chat.spaces.setup",\n          "parameterOrder": [],\n          "parameters": {},\n          "path": "v1/spaces:setup",\n          "request": {\n            "$ref": "SetUpSpaceRequest"\n          },\n          "response": {\n            "$ref": "Space"\n          },\n          "scopes": [\n            "https://www.googleapis.com/auth/chat.spaces",\n            "https://www.googleapis.com/auth/chat.spaces.create"\n          ]\n        }\n      },\n      "resources": {\n        "members": {\n          "methods": {\n            "create": {\n              "description": "Creates a human membership or app membership for the calling app. Creating memberships for other apps isn\'t supported. For an example, see [ Create a membership](https://developers.google.com/chat/api/guides/v1/members/create). When creating a membership, if the specified member has their auto-accept policy turned off, then they\'re invited, and must accept the space invitation before joining. Otherwise, creating a membership adds the member directly to the specified space. Requires [user authentication](https://developers.google.com/chat/api/guides/auth/users) and the `chat.memberships` (for human membership) or `chat.memberships.app` (for app membership) scope. To specify the member to add, set the `membership.member.name` in the `CreateMembershipRequest`: - To add the calling app to a space or a direct message between two human users, use `users/app`. Unable to add other apps to the space. - To add a human user, use `users/{user}`, where `{user}` is either the `{person_id}` for the [person](https://developers.google.com/people/api/rest/v1/people) from the People API, or the `id` for the [user](https://developers.google.com/admin-sdk/directory/reference/rest/v1/users) in the Directory API. For example, if the People API `Person` `resourceName` is `people/123456789`, you can add the user to the space by setting the `membership.member.name` to `users/123456789`.",\n              "flatPath": "v1/spaces/{spacesId}/members",\n              "httpMethod": "POST",\n              "id": "chat.spaces.members.create",\n              "parameterOrder": [\n                "parent"\n              ],\n              "parameters": {\n                "parent": {\n                  "description": "Required. The resource name of the space for which to create the membership. Format: spaces/{space}",\n                  "location": "path",\n                  "pattern": "^spaces/[^/]+$",\n                  "required": true,\n                  "type": "string"\n                }\n              },\n              "path": "v1/{+parent}/members",\n              "request": {\n                "$ref": "Membership"\n              },\n              "response": {\n                "$ref": "Membership"\n              },\n              "scopes": [\n                "https://www.googleapis.com/auth/chat.memberships",\n                "https://www.googleapis.com/auth/chat.memberships.app"\n              ]\n            },\n            "delete": {\n              "description": "Deletes a membership. For an example, see [Delete a membership](https://developers.google.com/chat/api/guides/v1/members/delete). Requires [user authentication](https://developers.google.com/chat/api/guides/auth/users) and the `chat.memberships` or `chat.memberships.app` authorization scope.",\n              "flatPath": "v1/spaces/{spacesId}/members/{membersId}",\n              "httpMethod": "DELETE",\n              "id": "chat.spaces.members.delete",\n              "parameterOrder": [\n                "name"\n              ],\n              "parameters": {\n                "name": {\n                  "description": "Required. Resource name of the membership to delete. Chat apps can delete human users\' or their own memberships. Chat apps can\'t delete other apps\' memberships. When deleting a human membership, requires the `chat.memberships` scope and `spaces/{space}/members/{member}` format. When deleting an app membership, requires the `chat.memberships.app` scope and `spaces/{space}/members/app` format. Format: `spaces/{space}/members/{member}` or `spaces/{space}/members/app`",\n                  "location": "path",\n                  "pattern": "^spaces/[^/]+/members/[^/]+$",\n                  "required": true,\n                  "type": "string"\n                }\n              },\n              "path": "v1/{+name}",\n              "response": {\n                "$ref": "Membership"\n              },\n              "scopes": [\n                "https://www.googleapis.com/auth/chat.memberships",\n                "https://www.googleapis.com/auth/chat.memberships.app"\n              ]\n            },\n            "get": {\n              "description": "Returns details about a membership. For an example, see [Get a membership](https://developers.google.com/chat/api/guides/v1/members/get). Requires [authentication](https://developers.google.com/chat/api/guides/auth). Fully supports [service account authentication](https://developers.google.com/chat/api/guides/auth/service-accounts) and [user authentication](https://developers.google.com/chat/api/guides/auth/users). [User authentication](https://developers.google.com/chat/api/guides/auth/users) requires the `chat.memberships` or `chat.memberships.readonly` authorization scope.",\n              "flatPath": "v1/spaces/{spacesId}/members/{membersId}",\n              "httpMethod": "GET",\n              "id": "chat.spaces.members.get",\n              "parameterOrder": [\n                "name"\n              ],\n              "parameters": {\n                "name": {\n                  "description": "Required. Resource name of the membership to retrieve. To get the app\'s own membership, you can optionally use `spaces/{space}/members/app`. Format: `spaces/{space}/members/{member}` or `spaces/{space}/members/app`",\n                  "location": "path",\n                  "pattern": "^spaces/[^/]+/members/[^/]+$",\n                  "required": true,\n                  "type": "string"\n                }\n              },\n              "path": "v1/{+name}",\n              "response": {\n                "$ref": "Membership"\n              },\n              "scopes": [\n                "https://www.googleapis.com/auth/chat.bot",\n                "https://www.googleapis.com/auth/chat.memberships",\n                "https://www.googleapis.com/auth/chat.memberships.readonly"\n              ]\n            },\n            "list": {\n              "description": "Lists memberships in a space. For an example, see [List memberships](https://developers.google.com/chat/api/guides/v1/members/list). Listing memberships with [app authentication](https://developers.google.com/chat/api/guides/auth/service-accounts) lists memberships in spaces that the Chat app has access to, but excludes Chat app memberships, including its own. Listing memberships with [User authentication](https://developers.google.com/chat/api/guides/auth/users) lists memberships in spaces that the authenticated user has access to. Requires [authentication](https://developers.google.com/chat/api/guides/auth). Fully supports [service account authentication](https://developers.google.com/chat/api/guides/auth/service-accounts) and [user authentication](https://developers.google.com/chat/api/guides/auth/users). [User authentication](https://developers.google.com/chat/api/guides/auth/users) requires the `chat.memberships` or `chat.memberships.readonly` authorization scope.",\n              "flatPath": "v1/spaces/{spacesId}/members",\n              "httpMethod": "GET",\n              "id": "chat.spaces.members.list",\n              "parameterOrder": [\n                "parent"\n              ],\n              "parameters": {\n                "filter": {\n                  "description": "Optional. A query filter. You can filter memberships by a member\'s role ([`role`](https://developers.google.com/chat/api/reference/rest/v1/spaces.members#membershiprole)) and type ([`member.type`](https://developers.google.com/chat/api/reference/rest/v1/User#type)). To filter by role, set `role` to `ROLE_MEMBER` or `ROLE_MANAGER`. To filter by type, set `member.type` to `HUMAN` or `BOT`. To filter by both role and type, use the `AND` operator. To filter by either role or type, use the `OR` operator. For example, the following queries are valid: ``` role = \\"ROLE_MANAGER\\" OR role = \\"ROLE_MEMBER\\" member.type = \\"HUMAN\\" AND role = \\"ROLE_MANAGER\\" ``` The following queries are invalid: ``` member.type = \\"HUMAN\\" AND member.type = \\"BOT\\" role = \\"ROLE_MANAGER\\" AND role = \\"ROLE_MEMBER\\" ``` Invalid queries are rejected by the server with an `INVALID_ARGUMENT` error.",\n                  "location": "query",\n                  "type": "string"\n                },\n                "pageSize": {\n                  "description": "The maximum number of memberships to return. The service might return fewer than this value. If unspecified, at most 100 memberships are returned. The maximum value is 1,000. If you use a value more than 1,000, it\'s automatically changed to 1,000. Negative values return an `INVALID_ARGUMENT` error.",\n                  "format": "int32",\n                  "location": "query",\n                  "type": "integer"\n                },\n                "pageToken": {\n                  "description": "A page token, received from a previous call to list memberships. Provide this parameter to retrieve the subsequent page. When paginating, all other parameters provided should match the call that provided the page token. Passing different values to the other parameters might lead to unexpected results.",\n                  "location": "query",\n                  "type": "string"\n                },\n                "parent": {\n                  "description": "Required. The resource name of the space for which to fetch a membership list. Format: spaces/{space}",\n                  "location": "path",\n                  "pattern": "^spaces/[^/]+$",\n                  "required": true,\n                  "type": "string"\n                },\n                "showInvited": {\n                  "description": "Optional. When `true`, also returns memberships associated with invited members, in addition to other types of memberships. If a filter is set, invited memberships that don\'t match the filter criteria aren\'t returned. Currently requires [user authentication](https://developers.google.com/chat/api/guides/auth/users).",\n                  "location": "query",\n                  "type": "boolean"\n                }\n              },\n              "path": "v1/{+parent}/members",\n              "response": {\n                "$ref": "ListMembershipsResponse"\n              },\n              "scopes": [\n                "https://www.googleapis.com/auth/chat.bot",\n                "https://www.googleapis.com/auth/chat.memberships",\n                "https://www.googleapis.com/auth/chat.memberships.readonly"\n              ]\n            }\n          }\n        },\n        "messages": {\n          "methods": {\n            "create": {\n              "description": "Creates a message. For an example, see [Create a message](https://developers.google.com/chat/api/guides/crudl/messages#create_a_message). Requires [authentication](https://developers.google.com/chat/api/guides/auth). Creating a text message supports both [user authentication](https://developers.google.com/chat/api/guides/auth/users) and [app authentication] (https://developers.google.com/chat/api/guides/auth/service-accounts). [User authentication](https://developers.google.com/chat/api/guides/auth/users) requires the `chat.messages` or `chat.messages.create` authorization scope. Creating a card message only supports and requires [app authentication] (https://developers.google.com/chat/api/guides/auth/service-accounts). Because Chat provides authentication for [webhooks](https://developers.google.com/chat/how-tos/webhooks) as part of the URL that\'s generated when a webhook is registered, webhooks can create messages without a service account or user authentication.",\n              "flatPath": "v1/spaces/{spacesId}/messages",\n              "httpMethod": "POST",\n              "id": "chat.spaces.messages.create",\n              "parameterOrder": [\n                "parent"\n              ],\n              "parameters": {\n                "messageId": {\n                  "description": "Optional. A custom name for a Chat message assigned at creation. Must start with `client-` and contain only lowercase letters, numbers, and hyphens up to 63 characters in length. Specify this field to get, update, or delete the message with the specified value. Assigning a custom name lets a a Chat app recall the message without saving the message `name` from the [response body](/chat/api/reference/rest/v1/spaces.messages/get#response-body) returned when creating the message. Assigning a custom name doesn\'t replace the generated `name` field, the message\'s resource name. Instead, it sets the custom name as the `clientAssignedMessageId` field, which you can reference while processing later operations, like updating or deleting the message. For example usage, see [Name a created message](https://developers.google.com/chat/api/guides/v1/messages/create#name_a_created_message).",\n                  "location": "query",\n                  "type": "string"\n                },\n                "messageReplyOption": {\n                  "description": "Optional. Specifies whether a message starts a thread or replies to one. Only supported in named spaces.",\n                  "enum": [\n                    "MESSAGE_REPLY_OPTION_UNSPECIFIED",\n                    "REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD",\n                    "REPLY_MESSAGE_OR_FAIL"\n                  ],\n                  "enumDescriptions": [\n                    "Default. Starts a thread.",\n                    "Creates the message as a reply to the thread specified by thread ID or `thread_key`. If it fails, the message starts a new thread instead.",\n                    "Creates the message as a reply to the thread specified by thread ID or `thread_key`. If it fails, a `NOT_FOUND` error is returned instead."\n                  ],\n                  "location": "query",\n                  "type": "string"\n                },\n                "parent": {\n                  "description": "Required. The resource name of the space in which to create a message. Format: `spaces/{space}`",\n                  "location": "path",\n                  "pattern": "^spaces/[^/]+$",\n                  "required": true,\n                  "type": "string"\n                },\n                "requestId": {\n                  "description": "Optional. A unique request ID for this message. Specifying an existing request ID returns the message created with that ID instead of creating a new message.",\n                  "location": "query",\n                  "type": "string"\n                },\n                "threadKey": {\n                  "deprecated": true,\n                  "description": "Optional. Deprecated: Use thread.thread_key instead. Opaque thread identifier. To start or add to a thread, create a message and specify a `threadKey` or the thread.name. For example usage, see [Start or reply to a message thread](https://developers.google.com/chat/api/guides/crudl/messages#start_or_reply_to_a_message_thread).",\n                  "location": "query",\n                  "type": "string"\n                }\n              },\n              "path": "v1/{+parent}/messages",\n              "request": {\n                "$ref": "Message"\n              },\n              "response": {\n                "$ref": "Message"\n              },\n              "scopes": [\n                "https://www.googleapis.com/auth/chat.bot",\n                "https://www.googleapis.com/auth/chat.import",\n                "https://www.googleapis.com/auth/chat.messages",\n                "https://www.googleapis.com/auth/chat.messages.create"\n              ]\n            },\n            "delete": {\n              "description": "Deletes a message. For an example, see [Delete a message](https://developers.google.com/chat/api/guides/v1/messages/delete). Requires [authentication](https://developers.google.com/chat/api/guides/auth). Fully supports [service account authentication](https://developers.google.com/chat/api/guides/auth/service-accounts) and [user authentication](https://developers.google.com/chat/api/guides/auth/users). [User authentication](https://developers.google.com/chat/api/guides/auth/users) requires the `chat.messages` authorization scope.",\n              "flatPath": "v1/spaces/{spacesId}/messages/{messagesId}",\n              "httpMethod": "DELETE",\n              "id": "chat.spaces.messages.delete",\n              "parameterOrder": [\n                "name"\n              ],\n              "parameters": {\n                "force": {\n                  "description": "When `true`, deleting a message also deletes its threaded replies. When `false`, if a message has threaded replies, deletion fails. Only applies when [authenticating as a user](https://developers.google.com/chat/api/guides/auth/users). Has no effect when [authenticating with a service account] (https://developers.google.com/chat/api/guides/auth/service-accounts).",\n                  "location": "query",\n                  "type": "boolean"\n                },\n                "name": {\n                  "description": "Required. Resource name of the message that you want to delete, in the form `spaces/*/messages/*` Example: `spaces/AAAAAAAAAAA/messages/BBBBBBBBBBB.BBBBBBBBBBB`",\n                  "location": "path",\n                  "pattern": "^spaces/[^/]+/messages/[^/]+$",\n                  "required": true,\n                  "type": "string"\n                }\n              },\n              "path": "v1/{+name}",\n              "response": {\n                "$ref": "Empty"\n              },\n              "scopes": [\n                "https://www.googleapis.com/auth/chat.bot",\n                "https://www.googleapis.com/auth/chat.import",\n                "https://www.googleapis.com/auth/chat.messages"\n              ]\n            },\n            "get": {\n              "description": "Returns details about a message. For an example, see [Read a message](https://developers.google.com/chat/api/guides/v1/messages/get). Requires [authentication](https://developers.google.com/chat/api/guides/auth). Fully supports [service account authentication](https://developers.google.com/chat/api/guides/auth/service-accounts) and [user authentication](https://developers.google.com/chat/api/guides/auth/users). [User authentication](https://developers.google.com/chat/api/guides/auth/users) requires the `chat.messages` or `chat.messages.readonly` authorization scope. Note: Might return a message from a blocked member or space.",\n              "flatPath": "v1/spaces/{spacesId}/messages/{messagesId}",\n              "httpMethod": "GET",\n              "id": "chat.spaces.messages.get",\n              "parameterOrder": [\n                "name"\n              ],\n              "parameters": {\n                "name": {\n                  "description": "Required. Resource name of the message to retrieve. Format: `spaces/{space}/messages/{message}` If the message begins with `client-`, then it has a custom name assigned by a Chat app that created it with the Chat REST API. That Chat app (but not others) can pass the custom name to get, update, or delete the message. To learn more, see [create and name a message] (https://developers.google.com/chat/api/guides/v1/messages/create#name_a_created_message).",\n                  "location": "path",\n                  "pattern": "^spaces/[^/]+/messages/[^/]+$",\n                  "required": true,\n                  "type": "string"\n                }\n              },\n              "path": "v1/{+name}",\n              "response": {\n                "$ref": "Message"\n              },\n              "scopes": [\n                "https://www.googleapis.com/auth/chat.bot",\n                "https://www.googleapis.com/auth/chat.messages",\n                "https://www.googleapis.com/auth/chat.messages.readonly"\n              ]\n            },\n            "list": {\n              "description": "Lists messages in a space that the caller is a member of, including messages from blocked members and spaces. For an example, see [List messages](/chat/api/guides/v1/messages/list). Requires [user authentication](https://developers.google.com/chat/api/guides/auth/users) and the `chat.messages` or `chat.messages.readonly` authorization scope. This method is only supported in spaces that don\'t allow users from outside the Workspace organization to join.",\n              "flatPath": "v1/spaces/{spacesId}/messages",\n              "httpMethod": "GET",\n              "id": "chat.spaces.messages.list",\n              "parameterOrder": [\n                "parent"\n              ],\n              "parameters": {\n                "filter": {\n                  "description": "A query filter. You can filter messages by date (`create_time`) and thread (`thread.name`). To filter messages by the date they were created, specify the `create_time` with a timestamp in [RFC-3339](https://www.rfc-editor.org/rfc/rfc3339) format and double quotation marks. For example, `\\"2023-04-21T11:30:00-04:00\\"`. You can use the greater than operator `>` to list messages that were created after a timestamp, or the less than operator `<` to list messages that were created before a timestamp. To filter messages within a time interval, use the `AND` operator between two timestamps. To filter by thread, specify the `thread.name`, formatted as `spaces/{space}/threads/{thread}`. You can only specify one `thread.name` per query. To filter by both thread and date, use the `AND` operator in your query. For example, the following queries are valid: ``` create_time > \\"2012-04-21T11:30:00-04:00\\" create_time > \\"2012-04-21T11:30:00-04:00\\" AND thread.name = spaces/AAAAAAAAAAA/threads/123 create_time > \\"2012-04-21T11:30:00+00:00\\" AND create_time < \\"2013-01-01T00:00:00+00:00\\" AND thread.name = spaces/AAAAAAAAAAA/threads/123 thread.name = spaces/AAAAAAAAAAA/threads/123 ``` Invalid queries are rejected by the server with an `INVALID_ARGUMENT` error.",\n                  "location": "query",\n                  "type": "string"\n                },\n                "orderBy": {\n                  "description": "Optional, if resuming from a previous query. How the list of messages is ordered. Specify a value to order by an ordering operation. Valid ordering operation values are as follows: - `ASC` for ascending. - `DESC` for descending. The default ordering is `create_time ASC`.",\n                  "location": "query",\n                  "type": "string"\n                },\n                "pageSize": {\n                  "description": "The maximum number of messages returned. The service might return fewer messages than this value. If unspecified, at most 25 are returned. The maximum value is 1,000. If you use a value more than 1,000, it\'s automatically changed to 1,000. Negative values return an `INVALID_ARGUMENT` error.",\n                  "format": "int32",\n                  "location": "query",\n                  "type": "integer"\n                },\n                "pageToken": {\n                  "description": "Optional, if resuming from a previous query. A page token received from a previous list messages call. Provide this parameter to retrieve the subsequent page. When paginating, all other parameters provided should match the call that provided the page token. Passing different values to the other parameters might lead to unexpected results.",\n                  "location": "query",\n                  "type": "string"\n                },\n                "parent": {\n                  "description": "Required. The resource name of the space to list messages from. Format: `spaces/{space}`",\n                  "location": "path",\n                  "pattern": "^spaces/[^/]+$",\n                  "required": true,\n                  "type": "string"\n                },\n                "showDeleted": {\n                  "description": "Whether to include deleted messages. Deleted messages include deleted time and metadata about their deletion, but message content is unavailable.",\n                  "location": "query",\n                  "type": "boolean"\n                }\n              },\n              "path": "v1/{+parent}/messages",\n              "response": {\n                "$ref": "ListMessagesResponse"\n              },\n              "scopes": [\n                "https://www.googleapis.com/auth/chat.import",\n                "https://www.googleapis.com/auth/chat.messages",\n                "https://www.googleapis.com/auth/chat.messages.readonly"\n              ]\n            },\n            "patch": {\n              "description": "Updates a message. There\'s a difference between the `patch` and `update` methods. The `patch` method uses a `patch` request while the `update` method uses a `put` request. We recommend using the `patch` method. For an example, see [Update a message](https://developers.google.com/chat/api/guides/v1/messages/update). Requires [authentication](https://developers.google.com/chat/api/guides/auth). Fully supports [service account authentication](https://developers.google.com/chat/api/guides/auth/service-accounts) and [user authentication](https://developers.google.com/chat/api/guides/auth/users). [User authentication](https://developers.google.com/chat/api/guides/auth/users) requires the `chat.messages` authorization scope.",\n              "flatPath": "v1/spaces/{spacesId}/messages/{messagesId}",\n              "httpMethod": "PATCH",\n              "id": "chat.spaces.messages.patch",\n              "parameterOrder": [\n                "name"\n              ],\n              "parameters": {\n                "allowMissing": {\n                  "description": "Optional. If `true` and the message isn\'t found, a new message is created and `updateMask` is ignored. The specified message ID must be [client-assigned](https://developers.google.com/chat/api/guides/v1/messages/create#name_a_created_message) or the request fails.",\n                  "location": "query",\n                  "type": "boolean"\n                },\n                "name": {\n                  "description": "Resource name in the form `spaces/*/messages/*`. Example: `spaces/AAAAAAAAAAA/messages/BBBBBBBBBBB.BBBBBBBBBBB`",\n                  "location": "path",\n                  "pattern": "^spaces/[^/]+/messages/[^/]+$",\n                  "required": true,\n                  "type": "string"\n                },\n                "updateMask": {\n                  "description": "Required. The field paths to update. Separate multiple values with commas. Currently supported field paths: - `text` - `attachment` - `cards` (Requires [service account authentication](/chat/api/guides/auth/service-accounts).) - `cards_v2` (Requires [service account authentication](/chat/api/guides/auth/service-accounts).)",\n                  "format": "google-fieldmask",\n                  "location": "query",\n                  "type": "string"\n                }\n              },\n              "path": "v1/{+name}",\n              "request": {\n                "$ref": "Message"\n              },\n              "response": {\n                "$ref": "Message"\n              },\n              "scopes": [\n                "https://www.googleapis.com/auth/chat.bot",\n                "https://www.googleapis.com/auth/chat.import",\n                "https://www.googleapis.com/auth/chat.messages"\n              ]\n            },\n            "update": {\n              "description": "Updates a message. There\'s a difference between the `patch` and `update` methods. The `patch` method uses a `patch` request while the `update` method uses a `put` request. We recommend using the `patch` method. For an example, see [Update a message](https://developers.google.com/chat/api/guides/v1/messages/update). Requires [authentication](https://developers.google.com/chat/api/guides/auth). Fully supports [service account authentication](https://developers.google.com/chat/api/guides/auth/service-accounts) and [user authentication](https://developers.google.com/chat/api/guides/auth/users). [User authentication](https://developers.google.com/chat/api/guides/auth/users) requires the `chat.messages` authorization scope.",\n              "flatPath": "v1/spaces/{spacesId}/messages/{messagesId}",\n              "httpMethod": "PUT",\n              "id": "chat.spaces.messages.update",\n              "parameterOrder": [\n                "name"\n              ],\n              "parameters": {\n                "allowMissing": {\n                  "description": "Optional. If `true` and the message isn\'t found, a new message is created and `updateMask` is ignored. The specified message ID must be [client-assigned](https://developers.google.com/chat/api/guides/v1/messages/create#name_a_created_message) or the request fails.",\n                  "location": "query",\n                  "type": "boolean"\n                },\n                "name": {\n                  "description": "Resource name in the form `spaces/*/messages/*`. Example: `spaces/AAAAAAAAAAA/messages/BBBBBBBBBBB.BBBBBBBBBBB`",\n                  "location": "path",\n                  "pattern": "^spaces/[^/]+/messages/[^/]+$",\n                  "required": true,\n                  "type": "string"\n                },\n                "updateMask": {\n                  "description": "Required. The field paths to update. Separate multiple values with commas. Currently supported field paths: - `text` - `attachment` - `cards` (Requires [service account authentication](/chat/api/guides/auth/service-accounts).) - `cards_v2` (Requires [service account authentication](/chat/api/guides/auth/service-accounts).)",\n                  "format": "google-fieldmask",\n                  "location": "query",\n                  "type": "string"\n                }\n              },\n              "path": "v1/{+name}",\n              "request": {\n                "$ref": "Message"\n              },\n              "response": {\n                "$ref": "Message"\n              },\n              "scopes": [\n                "https://www.googleapis.com/auth/chat.bot",\n                "https://www.googleapis.com/auth/chat.import",\n                "https://www.googleapis.com/auth/chat.messages"\n              ]\n            }\n          },\n          "resources": {\n            "attachments": {\n              "methods": {\n                "get": {\n                  "description": "Gets the metadata of a message attachment. The attachment data is fetched using the [media API](https://developers.google.com/chat/api/reference/rest/v1/media/download). For an example, see [Get a message attachment](https://developers.google.com/chat/api/guides/v1/media-and-attachments/get). Requires [service account authentication](https://developers.google.com/chat/api/guides/auth/service-accounts).",\n                  "flatPath": "v1/spaces/{spacesId}/messages/{messagesId}/attachments/{attachmentsId}",\n                  "httpMethod": "GET",\n                  "id": "chat.spaces.messages.attachments.get",\n                  "parameterOrder": [\n                    "name"\n                  ],\n                  "parameters": {\n                    "name": {\n                      "description": "Required. Resource name of the attachment, in the form `spaces/*/messages/*/attachments/*`.",\n                      "location": "path",\n                      "pattern": "^spaces/[^/]+/messages/[^/]+/attachments/[^/]+$",\n                      "required": true,\n                      "type": "string"\n                    }\n                  },\n                  "path": "v1/{+name}",\n                  "response": {\n                    "$ref": "Attachment"\n                  },\n                  "scopes": [\n                    "https://www.googleapis.com/auth/chat.bot"\n                  ]\n                }\n              }\n            },\n            "reactions": {\n              "methods": {\n                "create": {\n                  "description": "Creates a reaction and adds it to a message. For an example, see [Create a reaction](https://developers.google.com/chat/api/guides/v1/reactions/create). Requires [user authentication](https://developers.google.com/chat/api/guides/auth/users) and the `chat.messages`, `chat.messages.reactions`, or `chat.messages.reactions.create` scope. Only unicode emoji are supported.",\n                  "flatPath": "v1/spaces/{spacesId}/messages/{messagesId}/reactions",\n                  "httpMethod": "POST",\n                  "id": "chat.spaces.messages.reactions.create",\n                  "parameterOrder": [\n                    "parent"\n                  ],\n                  "parameters": {\n                    "parent": {\n                      "description": "Required. The message where the reaction is created. Format: `spaces/{space}/messages/{message}`",\n                      "location": "path",\n                      "pattern": "^spaces/[^/]+/messages/[^/]+$",\n                      "required": true,\n                      "type": "string"\n                    }\n                  },\n                  "path": "v1/{+parent}/reactions",\n                  "request": {\n                    "$ref": "Reaction"\n                  },\n                  "response": {\n                    "$ref": "Reaction"\n                  },\n                  "scopes": [\n                    "https://www.googleapis.com/auth/chat.import",\n                    "https://www.googleapis.com/auth/chat.messages",\n                    "https://www.googleapis.com/auth/chat.messages.reactions",\n                    "https://www.googleapis.com/auth/chat.messages.reactions.create"\n                  ]\n                },\n                "delete": {\n                  "description": "Deletes a reaction to a message. For an example, see [Delete a reaction](https://developers.google.com/chat/api/guides/v1/reactions/delete). Requires [user authentication](https://developers.google.com/chat/api/guides/auth/users) and the `chat.messages` or `chat.messages.reactions` scope.",\n                  "flatPath": "v1/spaces/{spacesId}/messages/{messagesId}/reactions/{reactionsId}",\n                  "httpMethod": "DELETE",\n                  "id": "chat.spaces.messages.reactions.delete",\n                  "parameterOrder": [\n                    "name"\n                  ],\n                  "parameters": {\n                    "name": {\n                      "description": "Required. Name of the reaction to delete. Format: `spaces/{space}/messages/{message}/reactions/{reaction}`",\n                      "location": "path",\n                      "pattern": "^spaces/[^/]+/messages/[^/]+/reactions/[^/]+$",\n                      "required": true,\n                      "type": "string"\n                    }\n                  },\n                  "path": "v1/{+name}",\n                  "response": {\n                    "$ref": "Empty"\n                  },\n                  "scopes": [\n                    "https://www.googleapis.com/auth/chat.import",\n                    "https://www.googleapis.com/auth/chat.messages",\n                    "https://www.googleapis.com/auth/chat.messages.reactions"\n                  ]\n                },\n                "list": {\n                  "description": "Lists reactions to a message. For an example, see [List reactions](https://developers.google.com/chat/api/guides/v1/reactions/list). Requires [user authentication](https://developers.google.com/chat/api/guides/auth/users) and `chat.messages`, `chat.messages.readonly`, `chat.messages.reactions`, or `chat.messages.reactions.readonly` scope.",\n                  "flatPath": "v1/spaces/{spacesId}/messages/{messagesId}/reactions",\n                  "httpMethod": "GET",\n                  "id": "chat.spaces.messages.reactions.list",\n                  "parameterOrder": [\n                    "parent"\n                  ],\n                  "parameters": {\n                    "filter": {\n                      "description": "Optional. A query filter. You can filter reactions by [emoji](https://developers.google.com/chat/api/reference/rest/v1/Emoji) (either `emoji.unicode` or `emoji.custom_emoji.uid`) and [user](https://developers.google.com/chat/api/reference/rest/v1/User) (`user.name`). To filter reactions for multiple emojis or users, join similar fields with the `OR` operator, such as `emoji.unicode = \\"\\ud83d\\ude42\\" OR emoji.unicode = \\"\\ud83d\\udc4d\\"` and `user.name = \\"users/AAAAAA\\" OR user.name = \\"users/BBBBBB\\"`. To filter reactions by emoji and user, use the `AND` operator, such as `emoji.unicode = \\"\\ud83d\\ude42\\" AND user.name = \\"users/AAAAAA\\"`. If your query uses both `AND` and `OR`, group them with parentheses. For example, the following queries are valid: ``` user.name = \\"users/{user}\\" emoji.unicode = \\"\\ud83d\\ude42\\" emoji.custom_emoji.uid = \\"{uid}\\" emoji.unicode = \\"\\ud83d\\ude42\\" OR emoji.unicode = \\"\\ud83d\\udc4d\\" emoji.unicode = \\"\\ud83d\\ude42\\" OR emoji.custom_emoji.uid = \\"{uid}\\" emoji.unicode = \\"\\ud83d\\ude42\\" AND user.name = \\"users/{user}\\" (emoji.unicode = \\"\\ud83d\\ude42\\" OR emoji.custom_emoji.uid = \\"{uid}\\") AND user.name = \\"users/{user}\\" ``` The following queries are invalid: ``` emoji.unicode = \\"\\ud83d\\ude42\\" AND emoji.unicode = \\"\\ud83d\\udc4d\\" emoji.unicode = \\"\\ud83d\\ude42\\" AND emoji.custom_emoji.uid = \\"{uid}\\" emoji.unicode = \\"\\ud83d\\ude42\\" OR user.name = \\"users/{user}\\" emoji.unicode = \\"\\ud83d\\ude42\\" OR emoji.custom_emoji.uid = \\"{uid}\\" OR user.name = \\"users/{user}\\" emoji.unicode = \\"\\ud83d\\ude42\\" OR emoji.custom_emoji.uid = \\"{uid}\\" AND user.name = \\"users/{user}\\" ``` Invalid queries are rejected by the server with an `INVALID_ARGUMENT` error.",\n                      "location": "query",\n                      "type": "string"\n                    },\n                    "pageSize": {\n                      "description": "Optional. The maximum number of reactions returned. The service can return fewer reactions than this value. If unspecified, the default value is 25. The maximum value is 200; values above 200 are changed to 200.",\n                      "format": "int32",\n                      "location": "query",\n                      "type": "integer"\n                    },\n                    "pageToken": {\n                      "description": "Optional. (If resuming from a previous query.) A page token received from a previous list reactions call. Provide this to retrieve the subsequent page. When paginating, the filter value should match the call that provided the page token. Passing a different value might lead to unexpected results.",\n                      "location": "query",\n                      "type": "string"\n                    },\n                    "parent": {\n                      "description": "Required. The message users reacted to. Format: `spaces/{space}/messages/{message}`",\n                      "location": "path",\n                      "pattern": "^spaces/[^/]+/messages/[^/]+$",\n                      "required": true,\n                      "type": "string"\n                    }\n                  },\n                  "path": "v1/{+parent}/reactions",\n                  "response": {\n                    "$ref": "ListReactionsResponse"\n                  },\n                  "scopes": [\n                    "https://www.googleapis.com/auth/chat.messages",\n                    "https://www.googleapis.com/auth/chat.messages.reactions",\n                    "https://www.googleapis.com/auth/chat.messages.reactions.readonly",\n                    "https://www.googleapis.com/auth/chat.messages.readonly"\n                  ]\n                }\n              }\n            }\n          }\n        }\n      }\n    }\n  },\n  "revision": "20230706",\n  "rootUrl": "https://chat.googleapis.com/",\n  "schemas": {\n    "ActionParameter": {\n      "description": "List of string parameters to supply when the action method is invoked. For example, consider three snooze buttons: snooze now, snooze one day, snooze next week. You might use `action method = snooze()`, passing the snooze type and snooze time in the list of string parameters.",\n      "id": "ActionParameter",\n      "properties": {\n        "key": {\n          "description": "The name of the parameter for the action script.",\n          "type": "string"\n        },\n        "value": {\n          "description": "The value of the parameter.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "ActionResponse": {\n      "description": "Parameters that a Chat app can use to configure how its response is posted.",\n      "id": "ActionResponse",\n      "properties": {\n        "dialogAction": {\n          "$ref": "DialogAction",\n          "description": "Input only. A response to an event related to a [dialog](https://developers.google.com/chat/how-tos/dialogs). Must be accompanied by `ResponseType.Dialog`."\n        },\n        "type": {\n          "description": "Input only. The type of Chat app response.",\n          "enum": [\n            "TYPE_UNSPECIFIED",\n            "NEW_MESSAGE",\n            "UPDATE_MESSAGE",\n            "UPDATE_USER_MESSAGE_CARDS",\n            "REQUEST_CONFIG",\n            "DIALOG"\n          ],\n          "enumDescriptions": [\n            "Default type that\'s handled as `NEW_MESSAGE`.",\n            "Post as a new message in the topic.",\n            "Update the Chat app\'s message. This is only permitted on a `CARD_CLICKED` event where the message sender type is `BOT`.",\n            "Update the cards on a user\'s message. This is only permitted as a response to a `MESSAGE` event with a matched url, or a `CARD_CLICKED` event where the message sender type is `HUMAN`. Text is ignored.",\n            "Privately ask the user for additional authentication or configuration.",\n            "Presents a [dialog](https://developers.google.com/chat/how-tos/dialogs)."\n          ],\n          "type": "string"\n        },\n        "url": {\n          "description": "Input only. URL for users to authenticate or configure. (Only for `REQUEST_CONFIG` response types.)",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "ActionStatus": {\n      "description": "Represents the status for a request to either invoke or submit a [dialog](https://developers.google.com/chat/how-tos/dialogs).",\n      "id": "ActionStatus",\n      "properties": {\n        "statusCode": {\n          "description": "The status code.",\n          "enum": [\n            "OK",\n            "CANCELLED",\n            "UNKNOWN",\n            "INVALID_ARGUMENT",\n            "DEADLINE_EXCEEDED",\n            "NOT_FOUND",\n            "ALREADY_EXISTS",\n            "PERMISSION_DENIED",\n            "UNAUTHENTICATED",\n            "RESOURCE_EXHAUSTED",\n            "FAILED_PRECONDITION",\n            "ABORTED",\n            "OUT_OF_RANGE",\n            "UNIMPLEMENTED",\n            "INTERNAL",\n            "UNAVAILABLE",\n            "DATA_LOSS"\n          ],\n          "enumDescriptions": [\n            "Not an error; returned on success. HTTP Mapping: 200 OK",\n            "The operation was cancelled, typically by the caller. HTTP Mapping: 499 Client Closed Request",\n            "Unknown error. For example, this error may be returned when a `Status` value received from another address space belongs to an error space that is not known in this address space. Also errors raised by APIs that do not return enough error information may be converted to this error. HTTP Mapping: 500 Internal Server Error",\n            "The client specified an invalid argument. Note that this differs from `FAILED_PRECONDITION`. `INVALID_ARGUMENT` indicates arguments that are problematic regardless of the state of the system (e.g., a malformed file name). HTTP Mapping: 400 Bad Request",\n            "The deadline expired before the operation could complete. For operations that change the state of the system, this error may be returned even if the operation has completed successfully. For example, a successful response from a server could have been delayed long enough for the deadline to expire. HTTP Mapping: 504 Gateway Timeout",\n            "Some requested entity (e.g., file or directory) was not found. Note to server developers: if a request is denied for an entire class of users, such as gradual feature rollout or undocumented allowlist, `NOT_FOUND` may be used. If a request is denied for some users within a class of users, such as user-based access control, `PERMISSION_DENIED` must be used. HTTP Mapping: 404 Not Found",\n            "The entity that a client attempted to create (e.g., file or directory) already exists. HTTP Mapping: 409 Conflict",\n            "The caller does not have permission to execute the specified operation. `PERMISSION_DENIED` must not be used for rejections caused by exhausting some resource (use `RESOURCE_EXHAUSTED` instead for those errors). `PERMISSION_DENIED` must not be used if the caller can not be identified (use `UNAUTHENTICATED` instead for those errors). This error code does not imply the request is valid or the requested entity exists or satisfies other pre-conditions. HTTP Mapping: 403 Forbidden",\n            "The request does not have valid authentication credentials for the operation. HTTP Mapping: 401 Unauthorized",\n            "Some resource has been exhausted, perhaps a per-user quota, or perhaps the entire file system is out of space. HTTP Mapping: 429 Too Many Requests",\n            "The operation was rejected because the system is not in a state required for the operation\'s execution. For example, the directory to be deleted is non-empty, an rmdir operation is applied to a non-directory, etc. Service implementors can use the following guidelines to decide between `FAILED_PRECONDITION`, `ABORTED`, and `UNAVAILABLE`: (a) Use `UNAVAILABLE` if the client can retry just the failing call. (b) Use `ABORTED` if the client should retry at a higher level. For example, when a client-specified test-and-set fails, indicating the client should restart a read-modify-write sequence. (c) Use `FAILED_PRECONDITION` if the client should not retry until the system state has been explicitly fixed. For example, if an \\"rmdir\\" fails because the directory is non-empty, `FAILED_PRECONDITION` should be returned since the client should not retry unless the files are deleted from the directory. HTTP Mapping: 400 Bad Request",\n            "The operation was aborted, typically due to a concurrency issue such as a sequencer check failure or transaction abort. See the guidelines above for deciding between `FAILED_PRECONDITION`, `ABORTED`, and `UNAVAILABLE`. HTTP Mapping: 409 Conflict",\n            "The operation was attempted past the valid range. E.g., seeking or reading past end-of-file. Unlike `INVALID_ARGUMENT`, this error indicates a problem that may be fixed if the system state changes. For example, a 32-bit file system will generate `INVALID_ARGUMENT` if asked to read at an offset that is not in the range [0,2^32-1], but it will generate `OUT_OF_RANGE` if asked to read from an offset past the current file size. There is a fair bit of overlap between `FAILED_PRECONDITION` and `OUT_OF_RANGE`. We recommend using `OUT_OF_RANGE` (the more specific error) when it applies so that callers who are iterating through a space can easily look for an `OUT_OF_RANGE` error to detect when they are done. HTTP Mapping: 400 Bad Request",\n            "The operation is not implemented or is not supported/enabled in this service. HTTP Mapping: 501 Not Implemented",\n            "Internal errors. This means that some invariants expected by the underlying system have been broken. This error code is reserved for serious errors. HTTP Mapping: 500 Internal Server Error",\n            "The service is currently unavailable. This is most likely a transient condition, which can be corrected by retrying with a backoff. Note that it is not always safe to retry non-idempotent operations. See the guidelines above for deciding between `FAILED_PRECONDITION`, `ABORTED`, and `UNAVAILABLE`. HTTP Mapping: 503 Service Unavailable",\n            "Unrecoverable data loss or corruption. HTTP Mapping: 500 Internal Server Error"\n          ],\n          "type": "string"\n        },\n        "userFacingMessage": {\n          "description": "The message to send users about the status of their request. If unset, a generic message based on the `status_code` is sent.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "Annotation": {\n      "description": "Annotations associated with the plain-text body of the message. Example plain-text message body: ``` Hello @FooBot how are you!\\" ``` The corresponding annotations metadata: ``` \\"annotations\\":[{ \\"type\\":\\"USER_MENTION\\", \\"startIndex\\":6, \\"length\\":7, \\"userMention\\": { \\"user\\": { \\"name\\":\\"users/{user}\\", \\"displayName\\":\\"FooBot\\", \\"avatarUrl\\":\\"https://goo.gl/aeDtrS\\", \\"type\\":\\"BOT\\" }, \\"type\\":\\"MENTION\\" } }] ```",\n      "id": "Annotation",\n      "properties": {\n        "length": {\n          "description": "Length of the substring in the plain-text message body this annotation corresponds to.",\n          "format": "int32",\n          "type": "integer"\n        },\n        "slashCommand": {\n          "$ref": "SlashCommandMetadata",\n          "description": "The metadata for a slash command."\n        },\n        "startIndex": {\n          "description": "Start index (0-based, inclusive) in the plain-text message body this annotation corresponds to.",\n          "format": "int32",\n          "type": "integer"\n        },\n        "type": {\n          "description": "The type of this annotation.",\n          "enum": [\n            "ANNOTATION_TYPE_UNSPECIFIED",\n            "USER_MENTION",\n            "SLASH_COMMAND"\n          ],\n          "enumDescriptions": [\n            "Default value for the enum. Don\'t use.",\n            "A user is mentioned.",\n            "A slash command is invoked."\n          ],\n          "type": "string"\n        },\n        "userMention": {\n          "$ref": "UserMentionMetadata",\n          "description": "The metadata of user mention."\n        }\n      },\n      "type": "object"\n    },\n    "AttachedGif": {\n      "description": "A GIF image that\'s specified by a URL.",\n      "id": "AttachedGif",\n      "properties": {\n        "uri": {\n          "description": "Output only. The URL that hosts the GIF image.",\n          "readOnly": true,\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "Attachment": {\n      "description": "An attachment in Google Chat.",\n      "id": "Attachment",\n      "properties": {\n        "attachmentDataRef": {\n          "$ref": "AttachmentDataRef",\n          "description": "A reference to the attachment data. This field is used with the media API to download the attachment data."\n        },\n        "contentName": {\n          "description": "The original file name for the content, not the full path.",\n          "type": "string"\n        },\n        "contentType": {\n          "description": "The content type (MIME type) of the file.",\n          "type": "string"\n        },\n        "downloadUri": {\n          "description": "Output only. The download URL which should be used to allow a human user to download the attachment. Chat apps shouldn\'t use this URL to download attachment content.",\n          "readOnly": true,\n          "type": "string"\n        },\n        "driveDataRef": {\n          "$ref": "DriveDataRef",\n          "description": "A reference to the drive attachment. This field is used with the Drive API."\n        },\n        "name": {\n          "description": "Resource name of the attachment, in the form `spaces/*/messages/*/attachments/*`.",\n          "type": "string"\n        },\n        "source": {\n          "description": "The source of the attachment.",\n          "enum": [\n            "SOURCE_UNSPECIFIED",\n            "DRIVE_FILE",\n            "UPLOADED_CONTENT"\n          ],\n          "enumDescriptions": [\n            "",\n            "",\n            ""\n          ],\n          "type": "string"\n        },\n        "thumbnailUri": {\n          "description": "Output only. The thumbnail URL which should be used to preview the attachment to a human user. Chat apps shouldn\'t use this URL to download attachment content.",\n          "readOnly": true,\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "AttachmentDataRef": {\n      "id": "AttachmentDataRef",\n      "properties": {\n        "attachmentUploadToken": {\n          "description": "Opaque token containing a reference to an uploaded attachment. Treated by clients as an opaque string and used to create or update Chat messages with attachments.",\n          "type": "string"\n        },\n        "resourceName": {\n          "description": "The resource name of the attachment data. This field is used with the media API to download the attachment data.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "Button": {\n      "description": "A button. Can be a text button or an image button.",\n      "id": "Button",\n      "properties": {\n        "imageButton": {\n          "$ref": "ImageButton",\n          "description": "A button with image and `onclick` action."\n        },\n        "textButton": {\n          "$ref": "TextButton",\n          "description": "A button with text and `onclick` action."\n        }\n      },\n      "type": "object"\n    },\n    "Card": {\n      "description": "A card is a UI element that can contain UI widgets such as text and images.",\n      "id": "Card",\n      "properties": {\n        "cardActions": {\n          "description": "The actions of this card.",\n          "items": {\n            "$ref": "CardAction"\n          },\n          "type": "array"\n        },\n        "header": {\n          "$ref": "CardHeader",\n          "description": "The header of the card. A header usually contains a title and an image."\n        },\n        "name": {\n          "description": "Name of the card.",\n          "type": "string"\n        },\n        "sections": {\n          "description": "Sections are separated by a line divider.",\n          "items": {\n            "$ref": "Section"\n          },\n          "type": "array"\n        }\n      },\n      "type": "object"\n    },\n    "CardAction": {\n      "description": "A card action is the action associated with the card. For an invoice card, a typical action would be: delete invoice, email invoice or open the invoice in browser. Not supported by Google Chat apps.",\n      "id": "CardAction",\n      "properties": {\n        "actionLabel": {\n          "description": "The label used to be displayed in the action menu item.",\n          "type": "string"\n        },\n        "onClick": {\n          "$ref": "OnClick",\n          "description": "The onclick action for this action item."\n        }\n      },\n      "type": "object"\n    },\n    "CardHeader": {\n      "id": "CardHeader",\n      "properties": {\n        "imageStyle": {\n          "description": "The image\'s type (for example, square border or circular border).",\n          "enum": [\n            "IMAGE_STYLE_UNSPECIFIED",\n            "IMAGE",\n            "AVATAR"\n          ],\n          "enumDescriptions": [\n            "",\n            "Square border.",\n            "Circular border."\n          ],\n          "type": "string"\n        },\n        "imageUrl": {\n          "description": "The URL of the image in the card header.",\n          "type": "string"\n        },\n        "subtitle": {\n          "description": "The subtitle of the card header.",\n          "type": "string"\n        },\n        "title": {\n          "description": "The title must be specified. The header has a fixed height: if both a title and subtitle is specified, each takes up one line. If only the title is specified, it takes up both lines.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "CardWithId": {\n      "description": "Widgets for Chat apps to specify.",\n      "id": "CardWithId",\n      "properties": {\n        "card": {\n          "$ref": "GoogleAppsCardV1Card",\n          "description": "Cards support a defined layout, interactive UI elements like buttons, and rich media like images. Use this card to present detailed information, gather information from users, and guide users to take a next step."\n        },\n        "cardId": {\n          "description": "Required for `cardsV2` messages. Chat app-specified identifier for this widget. Scoped within a message.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "ChatAppLogEntry": {\n      "description": "JSON payload of error messages. If the Cloud Logging API is enabled, these error messages are logged to [Google Cloud Logging](https://cloud.google.com/logging/docs).",\n      "id": "ChatAppLogEntry",\n      "properties": {\n        "deployment": {\n          "description": "The deployment that caused the error. For Chat apps built in Apps Script, this is the deployment ID defined by Apps Script.",\n          "type": "string"\n        },\n        "deploymentFunction": {\n          "description": "The unencrypted `callback_method` name that was running when the error was encountered.",\n          "type": "string"\n        },\n        "error": {\n          "$ref": "Status",\n          "description": "The error code and message."\n        }\n      },\n      "type": "object"\n    },\n    "Color": {\n      "description": "Represents a color in the RGBA color space. This representation is designed for simplicity of conversion to and from color representations in various languages over compactness. For example, the fields of this representation can be trivially provided to the constructor of `java.awt.Color` in Java; it can also be trivially provided to UIColor\'s `+colorWithRed:green:blue:alpha` method in iOS; and, with just a little work, it can be easily formatted into a CSS `rgba()` string in JavaScript. This reference page doesn\'t have information about the absolute color space that should be used to interpret the RGB value\\u2014for example, sRGB, Adobe RGB, DCI-P3, and BT.2020. By default, applications should assume the sRGB color space. When color equality needs to be decided, implementations, unless documented otherwise, treat two colors as equal if all their red, green, blue, and alpha values each differ by at most `1e-5`. Example (Java): import com.google.type.Color; // ... public static java.awt.Color fromProto(Color protocolor) { float alpha = protocolor.hasAlpha() ? protocolor.getAlpha().getValue() : 1.0; return new java.awt.Color( protocolor.getRed(), protocolor.getGreen(), protocolor.getBlue(), alpha); } public static Color toProto(java.awt.Color color) { float red = (float) color.getRed(); float green = (float) color.getGreen(); float blue = (float) color.getBlue(); float denominator = 255.0; Color.Builder resultBuilder = Color .newBuilder() .setRed(red / denominator) .setGreen(green / denominator) .setBlue(blue / denominator); int alpha = color.getAlpha(); if (alpha != 255) { result.setAlpha( FloatValue .newBuilder() .setValue(((float) alpha) / denominator) .build()); } return resultBuilder.build(); } // ... Example (iOS / Obj-C): // ... static UIColor* fromProto(Color* protocolor) { float red = [protocolor red]; float green = [protocolor green]; float blue = [protocolor blue]; FloatValue* alpha_wrapper = [protocolor alpha]; float alpha = 1.0; if (alpha_wrapper != nil) { alpha = [alpha_wrapper value]; } return [UIColor colorWithRed:red green:green blue:blue alpha:alpha]; } static Color* toProto(UIColor* color) { CGFloat red, green, blue, alpha; if (![color getRed:&red green:&green blue:&blue alpha:&alpha]) { return nil; } Color* result = [[Color alloc] init]; [result setRed:red]; [result setGreen:green]; [result setBlue:blue]; if (alpha <= 0.9999) { [result setAlpha:floatWrapperWithValue(alpha)]; } [result autorelease]; return result; } // ... Example (JavaScript): // ... var protoToCssColor = function(rgb_color) { var redFrac = rgb_color.red || 0.0; var greenFrac = rgb_color.green || 0.0; var blueFrac = rgb_color.blue || 0.0; var red = Math.floor(redFrac * 255); var green = Math.floor(greenFrac * 255); var blue = Math.floor(blueFrac * 255); if (!(\'alpha\' in rgb_color)) { return rgbToCssColor(red, green, blue); } var alphaFrac = rgb_color.alpha.value || 0.0; var rgbParams = [red, green, blue].join(\',\'); return [\'rgba(\', rgbParams, \',\', alphaFrac, \')\'].join(\'\'); }; var rgbToCssColor = function(red, green, blue) { var rgbNumber = new Number((red << 16) | (green << 8) | blue); var hexString = rgbNumber.toString(16); var missingZeros = 6 - hexString.length; var resultBuilder = [\'#\']; for (var i = 0; i < missingZeros; i++) { resultBuilder.push(\'0\'); } resultBuilder.push(hexString); return resultBuilder.join(\'\'); }; // ...",\n      "id": "Color",\n      "properties": {\n        "alpha": {\n          "description": "The fraction of this color that should be applied to the pixel. That is, the final pixel color is defined by the equation: `pixel color = alpha * (this color) + (1.0 - alpha) * (background color)` This means that a value of 1.0 corresponds to a solid color, whereas a value of 0.0 corresponds to a completely transparent color. This uses a wrapper message rather than a simple float scalar so that it is possible to distinguish between a default value and the value being unset. If omitted, this color object is rendered as a solid color (as if the alpha value had been explicitly given a value of 1.0).",\n          "format": "float",\n          "type": "number"\n        },\n        "blue": {\n          "description": "The amount of blue in the color as a value in the interval [0, 1].",\n          "format": "float",\n          "type": "number"\n        },\n        "green": {\n          "description": "The amount of green in the color as a value in the interval [0, 1].",\n          "format": "float",\n          "type": "number"\n        },\n        "red": {\n          "description": "The amount of red in the color as a value in the interval [0, 1].",\n          "format": "float",\n          "type": "number"\n        }\n      },\n      "type": "object"\n    },\n    "CommonEventObject": {\n      "description": "Represents information about the user\'s client, such as locale, host app, and platform. For Chat apps, `CommonEventObject` includes data submitted by users interacting with cards, like data entered in [dialogs](https://developers.google.com/chat/how-tos/dialogs).",\n      "id": "CommonEventObject",\n      "properties": {\n        "formInputs": {\n          "additionalProperties": {\n            "$ref": "Inputs"\n          },\n          "description": "A map containing the current values of the widgets in a card. The map keys are the string IDs assigned to each widget, and the values represent inputs to the widget. Depending on the input data type, a different object represents each input: For single-value widgets, `StringInput`. For multi-value widgets, an array of `StringInput` objects. For a date-time picker, a `DateTimeInput`. For a date-only picker, a `DateInput`. For a time-only picker, a `TimeInput`. Corresponds with the data entered by a user on a card in a [dialog](https://developers.google.com/chat/how-tos/dialogs).",\n          "type": "object"\n        },\n        "hostApp": {\n          "description": "The hostApp enum which indicates the app the add-on is invoked from. Always `CHAT` for Chat apps.",\n          "enum": [\n            "UNSPECIFIED_HOST_APP",\n            "GMAIL",\n            "CALENDAR",\n            "DRIVE",\n            "DEMO",\n            "DOCS",\n            "MEET",\n            "SHEETS",\n            "SLIDES",\n            "DRAWINGS",\n            "CHAT"\n          ],\n          "enumDescriptions": [\n            "Google can\'t identify a host app.",\n            "The add-on launches from Gmail.",\n            "The add-on launches from Google Calendar.",\n            "The add-on launches from Google Drive.",\n            "Not used.",\n            "The add-on launches from Google Docs.",\n            "The add-on launches from Google Meet.",\n            "The add-on launches from Google Sheets.",\n            "The add-on launches from Google Slides.",\n            "The add-on launches from Google Drawings.",\n            "A Google Chat app. Not used for Google Workspace Add-ons."\n          ],\n          "type": "string"\n        },\n        "invokedFunction": {\n          "description": "Name of the invoked function associated with the widget. Only set for Chat apps.",\n          "type": "string"\n        },\n        "parameters": {\n          "additionalProperties": {\n            "type": "string"\n          },\n          "description": "Custom [parameters](/chat/api/reference/rest/v1/cards#ActionParameter) passed to the invoked function. Both keys and values must be strings.",\n          "type": "object"\n        },\n        "platform": {\n          "description": "The platform enum which indicates the platform where the event originates (`WEB`, `IOS`, or `ANDROID`). Not supported by Chat apps.",\n          "enum": [\n            "UNKNOWN_PLATFORM",\n            "WEB",\n            "IOS",\n            "ANDROID"\n          ],\n          "enumDescriptions": [\n            "",\n            "",\n            "",\n            ""\n          ],\n          "type": "string"\n        },\n        "timeZone": {\n          "$ref": "TimeZone",\n          "description": "The timezone ID and offset from Coordinated Universal Time (UTC). Only supported for the event types [`CARD_CLICKED`](https://developers.google.com/chat/api/reference/rest/v1/EventType#ENUM_VALUES.CARD_CLICKED) and [`SUBMIT_DIALOG`](https://developers.google.com/chat/api/reference/rest/v1/DialogEventType#ENUM_VALUES.SUBMIT_DIALOG)."\n        },\n        "userLocale": {\n          "description": "The full `locale.displayName` in the format of [ISO 639 language code]-[ISO 3166 country/region code] such as \\"en-US\\".",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "CustomEmoji": {\n      "description": "Represents a custom emoji.",\n      "id": "CustomEmoji",\n      "properties": {\n        "uid": {\n          "description": "Unique key for the custom emoji resource.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "DateInput": {\n      "description": "Date input values.",\n      "id": "DateInput",\n      "properties": {\n        "msSinceEpoch": {\n          "description": "Time since epoch time, in milliseconds.",\n          "format": "int64",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "DateTimeInput": {\n      "description": "Date and time input values.",\n      "id": "DateTimeInput",\n      "properties": {\n        "hasDate": {\n          "description": "Whether the `datetime` input includes a calendar date.",\n          "type": "boolean"\n        },\n        "hasTime": {\n          "description": "Whether the `datetime` input includes a timestamp.",\n          "type": "boolean"\n        },\n        "msSinceEpoch": {\n          "description": "Time since epoch time, in milliseconds.",\n          "format": "int64",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "DeletionMetadata": {\n      "description": "Information about a deleted message. A message is deleted when `delete_time` is set.",\n      "id": "DeletionMetadata",\n      "properties": {\n        "deletionType": {\n          "description": "Indicates who deleted the message.",\n          "enum": [\n            "DELETION_TYPE_UNSPECIFIED",\n            "CREATOR",\n            "SPACE_OWNER",\n            "ADMIN",\n            "APP_MESSAGE_EXPIRY",\n            "CREATOR_VIA_APP",\n            "SPACE_OWNER_VIA_APP"\n          ],\n          "enumDescriptions": [\n            "This value is unused.",\n            "User deleted their own message.",\n            "The space owner deleted the message.",\n            "A Google Workspace admin deleted the message.",\n            "A Chat app deleted its own message when it expired.",\n            "A Chat app deleted the message on behalf of the user.",\n            "A Chat app deleted the message on behalf of the space owner."\n          ],\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "DeprecatedEvent": {\n      "description": "Google Chat events. To learn how to use events, see [Receive and respond to Google Chat events](https://developers.google.com/chat/api/guides/message-formats).",\n      "id": "DeprecatedEvent",\n      "properties": {\n        "action": {\n          "$ref": "FormAction",\n          "description": "The form action data associated with an interactive card that was clicked. Only populated for CARD_CLICKED events. See the [Interactive Cards guide](/chat/how-tos/cards-onclick) for more information."\n        },\n        "common": {\n          "$ref": "CommonEventObject",\n          "description": "Represents information about the user\'s client, such as locale, host app, and platform. For Chat apps, `CommonEventObject` includes information submitted by users interacting with [dialogs](https://developers.google.com/chat/how-tos/dialogs), like data entered on a card."\n        },\n        "configCompleteRedirectUrl": {\n          "description": "The URL the Chat app should redirect the user to after they have completed an authorization or configuration flow outside of Google Chat. For more information, see [Connect a Chat app with other services & tools](https://developers.google.com/chat/how-tos/connect-web-services-tools).",\n          "type": "string"\n        },\n        "dialogEventType": {\n          "description": "The type of [dialog](https://developers.google.com/chat/how-tos/dialogs) event received.",\n          "enum": [\n            "TYPE_UNSPECIFIED",\n            "REQUEST_DIALOG",\n            "SUBMIT_DIALOG",\n            "CANCEL_DIALOG"\n          ],\n          "enumDescriptions": [\n            "This could be used when the corresponding event is not dialog related. For example an @mention.",\n            "Any user action that opens a [dialog](https://developers.google.com/chat/how-tos/dialogs).",\n            "A card click event from a [dialog](https://developers.google.com/chat/how-tos/dialogs).",\n            "The [dialog](https://developers.google.com/chat/how-tos/dialogs) was cancelled."\n          ],\n          "type": "string"\n        },\n        "eventTime": {\n          "description": "The timestamp indicating when the event occurred.",\n          "format": "google-datetime",\n          "type": "string"\n        },\n        "isDialogEvent": {\n          "description": "True when the event is related to [dialogs](https://developers.google.com/chat/how-tos/dialogs).",\n          "type": "boolean"\n        },\n        "message": {\n          "$ref": "Message",\n          "description": "The message that triggered the event, if applicable."\n        },\n        "space": {\n          "$ref": "Space",\n          "description": "The space in which the event occurred."\n        },\n        "threadKey": {\n          "description": "The Chat app-defined key for the thread related to the event. See [`spaces.messages.thread.threadKey`](/chat/api/reference/rest/v1/spaces.messages#Thread.FIELDS.thread_key) for more information.",\n          "type": "string"\n        },\n        "token": {\n          "description": "A secret value that legacy Chat apps can use to verify if a request is from Google. Google randomly generates the token, and its value remains static. You can obtain, revoke, or regenerate the token from the [Chat API configuration page](https://console.cloud.google.com/apis/api/chat.googleapis.com/hangouts-chat) in the Google Cloud Console. Modern Chat apps don\'t use this field. It is absent from API responses and the [Chat API configuration page](https://console.cloud.google.com/apis/api/chat.googleapis.com/hangouts-chat).",\n          "type": "string"\n        },\n        "type": {\n          "description": "The type of the event.",\n          "enum": [\n            "UNSPECIFIED",\n            "MESSAGE",\n            "ADDED_TO_SPACE",\n            "REMOVED_FROM_SPACE",\n            "CARD_CLICKED"\n          ],\n          "enumDescriptions": [\n            "Default value for the enum. DO NOT USE.",\n            "A message was sent in a space.",\n            "The Chat app was added to a space by a Chat user or Workspace administrator.",\n            "The Chat app was removed from a space by a Chat user or Workspace administrator.",\n            "The Chat app\'s interactive card was clicked."\n          ],\n          "type": "string"\n        },\n        "user": {\n          "$ref": "User",\n          "description": "The user that triggered the event."\n        }\n      },\n      "type": "object"\n    },\n    "Dialog": {\n      "description": "Wrapper around the card body of the dialog.",\n      "id": "Dialog",\n      "properties": {\n        "body": {\n          "$ref": "GoogleAppsCardV1Card",\n          "description": "Input only. Body of the dialog, which is rendered in a modal. Google Chat apps don\'t support the following card entities: `DateTimePicker`, `OnChangeAction`."\n        }\n      },\n      "type": "object"\n    },\n    "DialogAction": {\n      "description": "Contains a [dialog](https://developers.google.com/chat/how-tos/dialogs) and request status code.",\n      "id": "DialogAction",\n      "properties": {\n        "actionStatus": {\n          "$ref": "ActionStatus",\n          "description": "Input only. Status for a request to either invoke or submit a [dialog](https://developers.google.com/chat/how-tos/dialogs). Displays a status and message to users, if necessary. For example, in case of an error or success."\n        },\n        "dialog": {\n          "$ref": "Dialog",\n          "description": "Input only. [Dialog](https://developers.google.com/chat/how-tos/dialogs) for the request."\n        }\n      },\n      "type": "object"\n    },\n    "DriveDataRef": {\n      "description": "A reference to the data of a drive attachment.",\n      "id": "DriveDataRef",\n      "properties": {\n        "driveFileId": {\n          "description": "The ID for the drive file. Use with the Drive API.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "Emoji": {\n      "description": "An emoji that is used as a reaction to a message.",\n      "id": "Emoji",\n      "properties": {\n        "customEmoji": {\n          "$ref": "CustomEmoji",\n          "description": "Output only. A custom emoji.",\n          "readOnly": true\n        },\n        "unicode": {\n          "description": "A basic emoji represented by a unicode string.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "EmojiReactionSummary": {\n      "description": "The number of people who reacted to a message with a specific emoji.",\n      "id": "EmojiReactionSummary",\n      "properties": {\n        "emoji": {\n          "$ref": "Emoji",\n          "description": "Emoji associated with the reactions."\n        },\n        "reactionCount": {\n          "description": "The total number of reactions using the associated emoji.",\n          "format": "int32",\n          "type": "integer"\n        }\n      },\n      "type": "object"\n    },\n    "Empty": {\n      "description": "A generic empty message that you can re-use to avoid defining duplicated empty messages in your APIs. A typical example is to use it as the request or the response type of an API method. For instance: service Foo { rpc Bar(google.protobuf.Empty) returns (google.protobuf.Empty); }",\n      "id": "Empty",\n      "properties": {},\n      "type": "object"\n    },\n    "FormAction": {\n      "description": "A form action describes the behavior when the form is submitted. For example, you can invoke Apps Script to handle the form.",\n      "id": "FormAction",\n      "properties": {\n        "actionMethodName": {\n          "description": "The method name is used to identify which part of the form triggered the form submission. This information is echoed back to the Chat app as part of the card click event. You can use the same method name for several elements that trigger a common behavior.",\n          "type": "string"\n        },\n        "parameters": {\n          "description": "List of action parameters.",\n          "items": {\n            "$ref": "ActionParameter"\n          },\n          "type": "array"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1Action": {\n      "description": "An action that describes the behavior when the form is submitted. For example, you can invoke an Apps Script script to handle the form. If the action is triggered, the form values are sent to the server.",\n      "id": "GoogleAppsCardV1Action",\n      "properties": {\n        "function": {\n          "description": "A custom function to invoke when the containing element is clicked or othrwise activated. For example usage, see [Create interactive cards](https://developers.google.com/chat/how-tos/cards-onclick).",\n          "type": "string"\n        },\n        "interaction": {\n          "description": "Optional. Required when opening a [dialog](https://developers.google.com/chat/how-tos/dialogs). What to do in response to an interaction with a user, such as a user clicking a button in a card message. If unspecified, the app responds by executing an `action`\\u2014like opening a link or running a function\\u2014as normal. By specifying an `interaction`, the app can respond in special interactive ways. For example, by setting `interaction` to `OPEN_DIALOG`, the app can open a [dialog](https://developers.google.com/chat/how-tos/dialogs). When specified, a loading indicator isn\'t shown. Supported by Chat apps, but not Google Workspace Add-ons. If specified for an add-on, the entire card is stripped and nothing is shown in the client.",\n          "enum": [\n            "INTERACTION_UNSPECIFIED",\n            "OPEN_DIALOG"\n          ],\n          "enumDescriptions": [\n            "Default value. The `action` executes as normal.",\n            "Opens a [dialog](https://developers.google.com/chat/how-tos/dialogs), a windowed, card-based interface that Chat apps use to interact with users. Only supported by Chat apps in response to button-clicks on card messages. Not supported by Google Workspace Add-ons. If specified for an add-on, the entire card is stripped and nothing is shown in the client."\n          ],\n          "type": "string"\n        },\n        "loadIndicator": {\n          "description": "Specifies the loading indicator that the action displays while making the call to the action.",\n          "enum": [\n            "SPINNER",\n            "NONE"\n          ],\n          "enumDescriptions": [\n            "Displays a spinner to indicate that content is loading.",\n            "Nothing is displayed."\n          ],\n          "type": "string"\n        },\n        "parameters": {\n          "description": "List of action parameters.",\n          "items": {\n            "$ref": "GoogleAppsCardV1ActionParameter"\n          },\n          "type": "array"\n        },\n        "persistValues": {\n          "description": "Indicates whether form values persist after the action. The default value is `false`. If `true`, form values remain after the action is triggered. To let the user make changes while the action is being processed, set [`LoadIndicator`](https://developers.google.com/workspace/add-ons/reference/rpc/google.apps.card.v1#loadindicator) to `NONE`. For [card messages](https://developers.google.com/chat/api/guides/message-formats/cards) in Chat apps, you must also set the action\'s [`ResponseType`](https://developers.google.com/chat/api/reference/rest/v1/spaces.messages#responsetype) to `UPDATE_MESSAGE` and use the same [`card_id`](https://developers.google.com/chat/api/reference/rest/v1/spaces.messages#CardWithId) from the card that contained the action. If `false`, the form values are cleared when the action is triggered. To prevent the user from making changes while the action is being processed, set [`LoadIndicator`](https://developers.google.com/workspace/add-ons/reference/rpc/google.apps.card.v1#loadindicator) to `SPINNER`.",\n          "type": "boolean"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1ActionParameter": {\n      "description": "List of string parameters to supply when the action method is invoked. For example, consider three snooze buttons: snooze now, snooze one day, or snooze next week. You might use `action method = snooze()`, passing the snooze type and snooze time in the list of string parameters. To learn more, see [`CommonEventObject`](https://developers.google.com/chat/api/reference/rest/v1/Event#commoneventobject).",\n      "id": "GoogleAppsCardV1ActionParameter",\n      "properties": {\n        "key": {\n          "description": "The name of the parameter for the action script.",\n          "type": "string"\n        },\n        "value": {\n          "description": "The value of the parameter.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1BorderStyle": {\n      "description": "The style options for the border of a card or widget, including the border type and color.",\n      "id": "GoogleAppsCardV1BorderStyle",\n      "properties": {\n        "cornerRadius": {\n          "description": "The corner radius for the border.",\n          "format": "int32",\n          "type": "integer"\n        },\n        "strokeColor": {\n          "$ref": "Color",\n          "description": "The colors to use when the type is `BORDER_TYPE_STROKE`."\n        },\n        "type": {\n          "description": "The border type.",\n          "enum": [\n            "BORDER_TYPE_UNSPECIFIED",\n            "NO_BORDER",\n            "STROKE"\n          ],\n          "enumDescriptions": [\n            "Don\'t use. Unspecified.",\n            "Default value. No border.",\n            "Outline."\n          ],\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1Button": {\n      "description": "A text, icon, or text and icon button that users can click. To make an image a clickable button, specify an `Image` (not an `ImageComponent`) and set an `onClick` action.",\n      "id": "GoogleAppsCardV1Button",\n      "properties": {\n        "altText": {\n          "description": "The alternative text that\'s used for accessibility. Set descriptive text that lets users know what the button does. For example, if a button opens a hyperlink, you might write: \\"Opens a new browser tab and navigates to the Google Chat developer documentation at https://developers.google.com/chat\\".",\n          "type": "string"\n        },\n        "color": {\n          "$ref": "Color",\n          "description": "If set, the button is filled with a solid background color and the font color changes to maintain contrast with the background color. For example, setting a blue background likely results in white text. If unset, the image background is white and the font color is blue. For red, green, and blue, the value of each field is a `float` number that you can express in either of two ways: as a number between 0 and 255 divided by 255 (153/255), or as a value between 0 and 1 (0.6). 0 represents the absence of a color and 1 or 255/255 represent the full presence of that color on the RGB scale. Optionally set `alpha`, which sets a level of transparency using this equation: ``` pixel color = alpha * (this color) + (1.0 - alpha) * (background color) ``` For `alpha`, a value of `1` corresponds with a solid color, and a value of `0` corresponds with a completely transparent color. For example, the following color represents a half transparent red: ``` \\"color\\": { \\"red\\": 1, \\"green\\": 0, \\"blue\\": 0, \\"alpha\\": 0.5 } ```"\n        },\n        "disabled": {\n          "description": "If `true`, the button is displayed in an inactive state and doesn\'t respond to user actions.",\n          "type": "boolean"\n        },\n        "icon": {\n          "$ref": "GoogleAppsCardV1Icon",\n          "description": "The icon image. If both `icon` and `text` are set, then the icon appears before the text."\n        },\n        "onClick": {\n          "$ref": "GoogleAppsCardV1OnClick",\n          "description": "Required. The action to perform when a user clicks the button, such as opening a hyperlink or running a custom function."\n        },\n        "text": {\n          "description": "The text displayed inside the button.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1ButtonList": {\n      "description": "A list of buttons layed out horizontally.",\n      "id": "GoogleAppsCardV1ButtonList",\n      "properties": {\n        "buttons": {\n          "description": "An array of buttons.",\n          "items": {\n            "$ref": "GoogleAppsCardV1Button"\n          },\n          "type": "array"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1Card": {\n      "description": "Cards support a defined layout, interactive UI elements like buttons, and rich media like images. Use cards to present detailed information, gather information from users, and guide users to take a next step. In Google Chat, cards appear in several places: - As stand-alone messages. - Accompanying a text message, just beneath the text message. - As a [dialog](https://developers.google.com/chat/how-tos/dialogs). The following example JSON creates a \\"contact card\\" that features: - A header with the contact\'s name, job title, and avatar picture. - A section with the contact information, including formatted text. - Buttons that users can click to share the contact, or see more or less information. ![Example contact card](https://developers.google.com/chat/images/card_api_reference.png) ``` { \\"cardsV2\\": [ { \\"cardId\\": \\"unique-card-id\\", \\"card\\": { \\"header\\": { \\"title\\": \\"Sasha\\", \\"subtitle\\": \\"Software Engineer\\", \\"imageUrl\\": \\"https://developers.google.com/chat/images/quickstart-app-avatar.png\\", \\"imageType\\": \\"CIRCLE\\", \\"imageAltText\\": \\"Avatar for Sasha\\", }, \\"sections\\": [ { \\"header\\": \\"Contact Info\\", \\"collapsible\\": true, \\"uncollapsibleWidgetsCount\\": 1, \\"widgets\\": [ { \\"decoratedText\\": { \\"startIcon\\": { \\"knownIcon\\": \\"EMAIL\\", }, \\"text\\": \\"sasha@example.com\\", } }, { \\"decoratedText\\": { \\"startIcon\\": { \\"knownIcon\\": \\"PERSON\\", }, \\"text\\": \\"Online\\", }, }, { \\"decoratedText\\": { \\"startIcon\\": { \\"knownIcon\\": \\"PHONE\\", }, \\"text\\": \\"+1 (555) 555-1234\\", } }, { \\"buttonList\\": { \\"buttons\\": [ { \\"text\\": \\"Share\\", \\"onClick\\": { \\"openLink\\": { \\"url\\": \\"https://example.com/share\\", } } }, { \\"text\\": \\"Edit\\", \\"onClick\\": { \\"action\\": { \\"function\\": \\"goToView\\", \\"parameters\\": [ { \\"key\\": \\"viewType\\", \\"value\\": \\"EDIT\\", } ], } } }, ], } }, ], }, ], }, } ], } ```",\n      "id": "GoogleAppsCardV1Card",\n      "properties": {\n        "cardActions": {\n          "description": "The card\'s actions. Actions are added to the card\'s toolbar menu. Because Chat app cards have no toolbar, `cardActions[]` isn\'t supported by Chat apps. For example, the following JSON constructs a card action menu with `Settings` and `Send Feedback` options: ``` \\"card_actions\\": [ { \\"actionLabel\\": \\"Settings\\", \\"onClick\\": { \\"action\\": { \\"functionName\\": \\"goToView\\", \\"parameters\\": [ { \\"key\\": \\"viewType\\", \\"value\\": \\"SETTING\\" } ], \\"loadIndicator\\": \\"LoadIndicator.SPINNER\\" } } }, { \\"actionLabel\\": \\"Send Feedback\\", \\"onClick\\": { \\"openLink\\": { \\"url\\": \\"https://example.com/feedback\\" } } } ] ```",\n          "items": {\n            "$ref": "GoogleAppsCardV1CardAction"\n          },\n          "type": "array"\n        },\n        "displayStyle": {\n          "description": "In Google Workspace add-ons, sets the display properties of the `peekCardHeader`. Not supported by Chat apps.",\n          "enum": [\n            "DISPLAY_STYLE_UNSPECIFIED",\n            "PEEK",\n            "REPLACE"\n          ],\n          "enumDescriptions": [\n            "Don\'t use. Unspecified.",\n            "The header of the card appears at the bottom of the sidebar, partially covering the current top card of the stack. Clicking the header pops the card into the card stack. If the card has no header, a generated header is used instead.",\n            "Default value. The card is shown by replacing the view of the top card in the card stack."\n          ],\n          "type": "string"\n        },\n        "fixedFooter": {\n          "$ref": "GoogleAppsCardV1CardFixedFooter",\n          "description": "The fixed footer shown at the bottom of this card. Setting `fixedFooter` without specifying a `primaryButton` or a `secondaryButton` causes an error. Supported by Google Workspace Add-ons and Chat apps. For Chat apps, you can use fixed footers in [dialogs](https://developers.google.com/chat/how-tos/dialogs), but not [card messages](https://developers.google.com/chat/api/guides/message-formats/cards)."\n        },\n        "header": {\n          "$ref": "GoogleAppsCardV1CardHeader",\n          "description": "The header of the card. A header usually contains a leading image and a title. Headers always appear at the top of a card."\n        },\n        "name": {\n          "description": "Name of the card. Used as a card identifier in card navigation. Because Chat apps don\'t support card navigation, they ignore this field.",\n          "type": "string"\n        },\n        "peekCardHeader": {\n          "$ref": "GoogleAppsCardV1CardHeader",\n          "description": "When displaying contextual content, the peek card header acts as a placeholder so that the user can navigate forward between the homepage cards and the contextual cards. Not supported by Chat apps."\n        },\n        "sections": {\n          "description": "Contains a collection of widgets. Each section has its own, optional header. Sections are visually separated by a line divider.",\n          "items": {\n            "$ref": "GoogleAppsCardV1Section"\n          },\n          "type": "array"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1CardAction": {\n      "description": "A card action is the action associated with the card. For example, an invoice card might include actions such as delete invoice, email invoice, or open the invoice in a browser. Not supported by Chat apps.",\n      "id": "GoogleAppsCardV1CardAction",\n      "properties": {\n        "actionLabel": {\n          "description": "The label that displays as the action menu item.",\n          "type": "string"\n        },\n        "onClick": {\n          "$ref": "GoogleAppsCardV1OnClick",\n          "description": "The `onClick` action for this action item."\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1CardFixedFooter": {\n      "description": "A persistent (sticky) footer that that appears at the bottom of the card. Setting `fixedFooter` without specifying a `primaryButton` or a `secondaryButton` causes an error. Supported by Google Workspace Add-ons and Chat apps. For Chat apps, you can use fixed footers in [dialogs](https://developers.google.com/chat/how-tos/dialogs), but not [card messages](https://developers.google.com/chat/api/guides/message-formats/cards).",\n      "id": "GoogleAppsCardV1CardFixedFooter",\n      "properties": {\n        "primaryButton": {\n          "$ref": "GoogleAppsCardV1Button",\n          "description": "The primary button of the fixed footer. The button must be a text button with text and color set."\n        },\n        "secondaryButton": {\n          "$ref": "GoogleAppsCardV1Button",\n          "description": "The secondary button of the fixed footer. The button must be a text button with text and color set. If `secondaryButton` is set, you must also set `primaryButton`."\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1CardHeader": {\n      "description": "Represents a card header.",\n      "id": "GoogleAppsCardV1CardHeader",\n      "properties": {\n        "imageAltText": {\n          "description": "The alternative text of this image that\'s used for accessibility.",\n          "type": "string"\n        },\n        "imageType": {\n          "description": "The shape used to crop the image.",\n          "enum": [\n            "SQUARE",\n            "CIRCLE"\n          ],\n          "enumDescriptions": [\n            "Default value. Applies a square mask to the image. For example, a 4x3 image becomes 3x3.",\n            "Applies a circular mask to the image. For example, a 4x3 image becomes a circle with a diameter of 3."\n          ],\n          "type": "string"\n        },\n        "imageUrl": {\n          "description": "The HTTPS URL of the image in the card header.",\n          "type": "string"\n        },\n        "subtitle": {\n          "description": "The subtitle of the card header. If specified, appears on its own line below the `title`.",\n          "type": "string"\n        },\n        "title": {\n          "description": "Required. The title of the card header. The header has a fixed height: if both a title and subtitle are specified, each takes up one line. If only the title is specified, it takes up both lines.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1Column": {\n      "description": "A column.",\n      "id": "GoogleAppsCardV1Column",\n      "properties": {\n        "horizontalAlignment": {\n          "description": "Specifies whether widgets align to the left, right, or center of a column.",\n          "enum": [\n            "HORIZONTAL_ALIGNMENT_UNSPECIFIED",\n            "START",\n            "CENTER",\n            "END"\n          ],\n          "enumDescriptions": [\n            "Don\'t use. Unspecified.",\n            "Default value. Aligns widgets to the start position of the column. For left-to-right layouts, aligns to the left. For right-to-left layouts, aligns to the right.",\n            "Aligns widgets to the center of the column.",\n            "Aligns widgets to the end position of the column. For left-to-right layouts, aligns widgets to the right. For right-to-left layouts, aligns widgets to the left."\n          ],\n          "type": "string"\n        },\n        "horizontalSizeStyle": {\n          "description": "Specifies how a column fills the width of the card.",\n          "enum": [\n            "HORIZONTAL_SIZE_STYLE_UNSPECIFIED",\n            "FILL_AVAILABLE_SPACE",\n            "FILL_MINIMUM_SPACE"\n          ],\n          "enumDescriptions": [\n            "Don\'t use. Unspecified.",\n            "Default value. Column fills the available space, up to 70% of the card\'s width. If both columns are set to `FILL_AVAILABLE_SPACE`, each column fills 50% of the space.",\n            "Column fills the least amount of space possible and no more than 30% of the card\'s width."\n          ],\n          "type": "string"\n        },\n        "verticalAlignment": {\n          "description": "Specifies whether widgets align to the top, bottom, or center of a column.",\n          "enum": [\n            "VERTICAL_ALIGNMENT_UNSPECIFIED",\n            "CENTER",\n            "TOP",\n            "BOTTOM"\n          ],\n          "enumDescriptions": [\n            "Don\'t use. Unspecified.",\n            "Default value. Aligns widgets to the center of a column.",\n            "Aligns widgets to the top of a column.",\n            "Aligns widgets to the bottom of a column."\n          ],\n          "type": "string"\n        },\n        "widgets": {\n          "description": "An array of widgets included in a column. Widgets appear in the order that they are specified.",\n          "items": {\n            "$ref": "GoogleAppsCardV1Widgets"\n          },\n          "type": "array"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1Columns": {\n      "description": "The `Columns` widget displays up to 2 columns in a card message or dialog. You can add widgets to each column; the widgets appear in the order that they are specified. The height of each column is determined by the taller column. For example, if the first column is taller than the second column, both columns have the height of the first column. Because each column can contain a different number of widgets, you can\'t define rows or align widgets between the columns. Columns are displayed side-by-side. You can customize the width of each column using the `HorizontalSizeStyle` field. If the user\'s screen width is too narrow, the second column wraps below the first: * On web, the second column wraps if the screen width is less than or equal to 480 pixels. * On iOS devices, the second column wraps if the screen width is less than or equal to 300 pt. * On Android devices, the second column wraps if the screen width is less than or equal to 320 dp. To include more than 2 columns, or to use rows, use the `Grid` widget. Supported by Chat apps, but not Google Workspace Add-ons.",\n      "id": "GoogleAppsCardV1Columns",\n      "properties": {\n        "columnItems": {\n          "description": "An array of columns. You can include up to 2 columns in a card or dialog.",\n          "items": {\n            "$ref": "GoogleAppsCardV1Column"\n          },\n          "type": "array"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1DateTimePicker": {\n      "description": "Lets users input a date, a time, or both a date and a time. Users can input text or use the picker to select dates and times. If users input an invalid date or time, the picker shows an error that prompts users to input the information correctly.",\n      "id": "GoogleAppsCardV1DateTimePicker",\n      "properties": {\n        "label": {\n          "description": "The text that prompts users to input a date, a time, or a date and time. For example, if users are scheduling an appointment, use a label such as `Appointment date` or `Appointment date and time`.",\n          "type": "string"\n        },\n        "name": {\n          "description": "The name by which the `DateTimePicker` is identified in a form input event. For details about working with form inputs, see [Receive form data](https://developers.google.com/chat/how-tos/dialogs#receive_form_data_from_dialogs).",\n          "type": "string"\n        },\n        "onChangeAction": {\n          "$ref": "GoogleAppsCardV1Action",\n          "description": "Triggered when the user clicks **Save** or **Clear** from the `DateTimePicker` interface."\n        },\n        "timezoneOffsetDate": {\n          "description": "The number representing the time zone offset from UTC, in minutes. If set, the `value_ms_epoch` is displayed in the specified time zone. If unset, the value defaults to the user\'s time zone setting.",\n          "format": "int32",\n          "type": "integer"\n        },\n        "type": {\n          "description": "Whether the widget supports inputting a date, a time, or the date and time.",\n          "enum": [\n            "DATE_AND_TIME",\n            "DATE_ONLY",\n            "TIME_ONLY"\n          ],\n          "enumDescriptions": [\n            "Users input a date and time.",\n            "Users input a date.",\n            "Users input a time."\n          ],\n          "type": "string"\n        },\n        "valueMsEpoch": {\n          "description": "The default value displayed in the widget, in milliseconds since [Unix epoch time](https://en.wikipedia.org/wiki/Unix_time). Specify the value based on the type of picker (`DateTimePickerType`): * `DATE_AND_TIME`: a calendar date and time in UTC. For example, to represent January 1, 2023 at 12:00 PM UTC, use `1672574400000`. * `DATE_ONLY`: a calendar date at 00:00:00 UTC. For example, to represent January 1, 2023, use `1672531200000`. * `TIME_ONLY`: a time in UTC. For example, to represent 12:00 PM, use `43200000` (or `12 * 60 * 60 * 1000`).",\n          "format": "int64",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1DecoratedText": {\n      "description": "A widget that displays text with optional decorations such as a label above or below the text, an icon in front of the text, a selection widget, or a button after the text.",\n      "id": "GoogleAppsCardV1DecoratedText",\n      "properties": {\n        "bottomLabel": {\n          "description": "The text that appears below `text`. Always wraps.",\n          "type": "string"\n        },\n        "button": {\n          "$ref": "GoogleAppsCardV1Button",\n          "description": "A button that a user can click to trigger an action."\n        },\n        "endIcon": {\n          "$ref": "GoogleAppsCardV1Icon",\n          "description": "An icon displayed after the text. Supports [built-in](https://developers.google.com/chat/api/guides/message-formats/cards#builtinicons) and [custom](https://developers.google.com/chat/api/guides/message-formats/cards#customicons) icons."\n        },\n        "icon": {\n          "$ref": "GoogleAppsCardV1Icon",\n          "deprecated": true,\n          "description": "Deprecated in favor of `startIcon`."\n        },\n        "onClick": {\n          "$ref": "GoogleAppsCardV1OnClick",\n          "description": "This action is triggered when users click `topLabel` or `bottomLabel`."\n        },\n        "startIcon": {\n          "$ref": "GoogleAppsCardV1Icon",\n          "description": "The icon displayed in front of the text."\n        },\n        "switchControl": {\n          "$ref": "GoogleAppsCardV1SwitchControl",\n          "description": "A switch widget that a user can click to change its state and trigger an action."\n        },\n        "text": {\n          "description": "Required. The primary text. Supports simple formatting. For more information about formatting text, see [Formatting text in Google Chat apps](https://developers.google.com/chat/api/guides/message-formats/cards#card_text_formatting) and [Formatting text in Google Workspace Add-ons](https://developers.google.com/apps-script/add-ons/concepts/widgets#text_formatting).",\n          "type": "string"\n        },\n        "topLabel": {\n          "description": "The text that appears above `text`. Always truncates.",\n          "type": "string"\n        },\n        "wrapText": {\n          "description": "The wrap text setting. If `true`, the text wraps and displays on multiple lines. Otherwise, the text is truncated. Only applies to `text`, not `topLabel` and `bottomLabel`.",\n          "type": "boolean"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1Divider": {\n      "description": "Displays a divider between widgets as a horizontal line. For example, the following JSON creates a divider: ``` \\"divider\\": {} ```",\n      "id": "GoogleAppsCardV1Divider",\n      "properties": {},\n      "type": "object"\n    },\n    "GoogleAppsCardV1Grid": {\n      "description": "Displays a grid with a collection of items. Items can only include text or images. A grid supports any number of columns and items. The number of rows is determined by items divided by columns. A grid with 10 items and 2 columns has 5 rows. A grid with 11 items and 2 columns has 6 rows. For responsive columns, or to include more than text or images, use `Columns`. For example, the following JSON creates a 2 column grid with a single item: ``` \\"grid\\": { \\"title\\": \\"A fine collection of items\\", \\"columnCount\\": 2, \\"borderStyle\\": { \\"type\\": \\"STROKE\\", \\"cornerRadius\\": 4 }, \\"items\\": [ { \\"image\\": { \\"imageUri\\": \\"https://www.example.com/image.png\\", \\"cropStyle\\": { \\"type\\": \\"SQUARE\\" }, \\"borderStyle\\": { \\"type\\": \\"STROKE\\" } }, \\"title\\": \\"An item\\", \\"textAlignment\\": \\"CENTER\\" } ], \\"onClick\\": { \\"openLink\\": { \\"url\\": \\"https://www.example.com\\" } } } ```",\n      "id": "GoogleAppsCardV1Grid",\n      "properties": {\n        "borderStyle": {\n          "$ref": "GoogleAppsCardV1BorderStyle",\n          "description": "The border style to apply to each grid item."\n        },\n        "columnCount": {\n          "description": "The number of columns to display in the grid. A default value is used if this field isn\'t specified, and that default value is different depending on where the grid is shown (dialog versus companion).",\n          "format": "int32",\n          "type": "integer"\n        },\n        "items": {\n          "description": "The items to display in the grid.",\n          "items": {\n            "$ref": "GoogleAppsCardV1GridItem"\n          },\n          "type": "array"\n        },\n        "onClick": {\n          "$ref": "GoogleAppsCardV1OnClick",\n          "description": "This callback is reused by each individual grid item, but with the item\'s identifier and index in the items list added to the callback\'s parameters."\n        },\n        "title": {\n          "description": "The text that displays in the grid header.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1GridItem": {\n      "description": "Represents an item in a grid layout. Items can contain text, an image, or both text and an image.",\n      "id": "GoogleAppsCardV1GridItem",\n      "properties": {\n        "id": {\n          "description": "A user-specified identifier for this grid item. This identifier is returned in the parent grid\'s `onClick` callback parameters.",\n          "type": "string"\n        },\n        "image": {\n          "$ref": "GoogleAppsCardV1ImageComponent",\n          "description": "The image that displays in the grid item."\n        },\n        "layout": {\n          "description": "The layout to use for the grid item.",\n          "enum": [\n            "GRID_ITEM_LAYOUT_UNSPECIFIED",\n            "TEXT_BELOW",\n            "TEXT_ABOVE"\n          ],\n          "enumDescriptions": [\n            "Don\'t use. Unspecified.",\n            "The title and subtitle are shown below the grid item\'s image.",\n            "The title and subtitle are shown above the grid item\'s image."\n          ],\n          "type": "string"\n        },\n        "subtitle": {\n          "description": "The grid item\'s subtitle.",\n          "type": "string"\n        },\n        "title": {\n          "description": "The grid item\'s title.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1Icon": {\n      "description": "An icon displayed in a widget on a card. Supports [built-in](https://developers.google.com/chat/api/guides/message-formats/cards#builtinicons) and [custom](https://developers.google.com/chat/api/guides/message-formats/cards#customicons) icons.",\n      "id": "GoogleAppsCardV1Icon",\n      "properties": {\n        "altText": {\n          "description": "Optional. A description of the icon used for accessibility. If unspecified, the default value `Button` is provided. As a best practice, you should set a helpful description for what the icon displays, and if applicable, what it does. For example, `A user\'s account portrait`, or `Opens a new browser tab and navigates to the Google Chat developer documentation at https://developers.google.com/chat`. If the icon is set in a `Button`, the `altText` appears as helper text when the user hovers over the button. However, if the button also sets `text`, the icon\'s `altText` is ignored.",\n          "type": "string"\n        },\n        "iconUrl": {\n          "description": "Display a custom icon hosted at an HTTPS URL. For example: ``` \\"iconUrl\\": \\"https://developers.google.com/chat/images/quickstart-app-avatar.png\\" ``` Supported file types include `.png` and `.jpg`.",\n          "type": "string"\n        },\n        "imageType": {\n          "description": "The crop style applied to the image. In some cases, applying a `CIRCLE` crop causes the image to be drawn larger than a built-in icon.",\n          "enum": [\n            "SQUARE",\n            "CIRCLE"\n          ],\n          "enumDescriptions": [\n            "Default value. Applies a square mask to the image. For example, a 4x3 image becomes 3x3.",\n            "Applies a circular mask to the image. For example, a 4x3 image becomes a circle with a diameter of 3."\n          ],\n          "type": "string"\n        },\n        "knownIcon": {\n          "description": "Display one of the built-in icons provided by Google Workspace. For example, to display an airplane icon, specify `AIRPLANE`. For a bus, specify `BUS`. For a full list of supported icons, see [built-in icons](https://developers.google.com/chat/api/guides/message-formats/cards#builtinicons).",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1Image": {\n      "description": "An image that is specified by a URL and can have an `onClick` action.",\n      "id": "GoogleAppsCardV1Image",\n      "properties": {\n        "altText": {\n          "description": "The alternative text of this image that\'s used for accessibility.",\n          "type": "string"\n        },\n        "imageUrl": {\n          "description": "The HTTPS URL that hosts the image. For example: ``` https://developers.google.com/chat/images/quickstart-app-avatar.png ```",\n          "type": "string"\n        },\n        "onClick": {\n          "$ref": "GoogleAppsCardV1OnClick",\n          "description": "When a user clicks the image, the click triggers this action."\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1ImageComponent": {\n      "description": "Represents an image.",\n      "id": "GoogleAppsCardV1ImageComponent",\n      "properties": {\n        "altText": {\n          "description": "The accessibility label for the image.",\n          "type": "string"\n        },\n        "borderStyle": {\n          "$ref": "GoogleAppsCardV1BorderStyle",\n          "description": "The border style to apply to the image."\n        },\n        "cropStyle": {\n          "$ref": "GoogleAppsCardV1ImageCropStyle",\n          "description": "The crop style to apply to the image."\n        },\n        "imageUri": {\n          "description": "The image URL.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1ImageCropStyle": {\n      "description": "Represents the crop style applied to an image. For example, here\'s how to apply a 16:9 aspect ratio: ``` cropStyle { \\"type\\": \\"RECTANGLE_CUSTOM\\", \\"aspectRatio\\": 16/9 } ```",\n      "id": "GoogleAppsCardV1ImageCropStyle",\n      "properties": {\n        "aspectRatio": {\n          "description": "The aspect ratio to use if the crop type is `RECTANGLE_CUSTOM`. For example, here\'s how to apply a 16:9 aspect ratio: ``` cropStyle { \\"type\\": \\"RECTANGLE_CUSTOM\\", \\"aspectRatio\\": 16/9 } ```",\n          "format": "double",\n          "type": "number"\n        },\n        "type": {\n          "description": "The crop type.",\n          "enum": [\n            "IMAGE_CROP_TYPE_UNSPECIFIED",\n            "SQUARE",\n            "CIRCLE",\n            "RECTANGLE_CUSTOM",\n            "RECTANGLE_4_3"\n          ],\n          "enumDescriptions": [\n            "Don\'t use. Unspecified.",\n            "Default value. Applies a square crop.",\n            "Applies a circular crop.",\n            "Applies a rectangular crop with a custom aspect ratio. Set the custom aspect ratio with `aspectRatio`.",\n            "Applies a rectangular crop with a 4:3 aspect ratio."\n          ],\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1OnClick": {\n      "description": "Represents how to respond when users click an interactive element on a card, such as a button.",\n      "id": "GoogleAppsCardV1OnClick",\n      "properties": {\n        "action": {\n          "$ref": "GoogleAppsCardV1Action",\n          "description": "If specified, an action is triggered by this `onClick`."\n        },\n        "card": {\n          "$ref": "GoogleAppsCardV1Card",\n          "description": "A new card is pushed to the card stack after clicking if specified. Supported by Google Workspace Add-ons, but not Chat apps."\n        },\n        "openDynamicLinkAction": {\n          "$ref": "GoogleAppsCardV1Action",\n          "description": "An add-on triggers this action when the action needs to open a link. This differs from the `open_link` above in that this needs to talk to server to get the link. Thus some preparation work is required for web client to do before the open link action response comes back."\n        },\n        "openLink": {\n          "$ref": "GoogleAppsCardV1OpenLink",\n          "description": "If specified, this `onClick` triggers an open link action."\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1OpenLink": {\n      "description": "Represents an `onClick` event that opens a hyperlink.",\n      "id": "GoogleAppsCardV1OpenLink",\n      "properties": {\n        "onClose": {\n          "description": "Whether the client forgets about a link after opening it, or observes it until the window closes. Not supported by Chat apps.",\n          "enum": [\n            "NOTHING",\n            "RELOAD"\n          ],\n          "enumDescriptions": [\n            "Default value. The card doesn\'t reload; nothing happens.",\n            "Reloads the card after the child window closes. If used in conjunction with [`OpenAs.OVERLAY`](https://developers.google.com/workspace/add-ons/reference/rpc/google.apps.card.v1#openas), the child window acts as a modal dialog and the parent card is blocked until the child window closes."\n          ],\n          "type": "string"\n        },\n        "openAs": {\n          "description": "How to open a link. Not supported by Chat apps.",\n          "enum": [\n            "FULL_SIZE",\n            "OVERLAY"\n          ],\n          "enumDescriptions": [\n            "The link opens as a full-size window (if that\'s the frame used by the client).",\n            "The link opens as an overlay, such as a pop-up."\n          ],\n          "type": "string"\n        },\n        "url": {\n          "description": "The URL to open.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1Section": {\n      "description": "A section contains a collection of widgets that are rendered vertically in the order that they\'re specified.",\n      "id": "GoogleAppsCardV1Section",\n      "properties": {\n        "collapsible": {\n          "description": "Indicates whether this section is collapsible. Collapsible sections hide some or all widgets, but users can expand the section to reveal the hidden widgets by clicking **Show more**. Users can hide the widgets again by clicking **Show less**. To determine which widgets are hidden, specify `uncollapsibleWidgetsCount`.",\n          "type": "boolean"\n        },\n        "header": {\n          "description": "Text that appears at the top of a section. Supports simple HTML formatted text. For more information about formatting text, see [Formatting text in Google Chat apps](https://developers.google.com/chat/api/guides/message-formats/cards#card_text_formatting) and [Formatting text in Google Workspace Add-ons](https://developers.google.com/apps-script/add-ons/concepts/widgets#text_formatting).",\n          "type": "string"\n        },\n        "uncollapsibleWidgetsCount": {\n          "description": "The number of uncollapsible widgets which remain visible even when a section is collapsed. For example, when a section contains five widgets and the `uncollapsibleWidgetsCount` is set to `2`, the first two widgets are always shown and the last three are collapsed by default. The `uncollapsibleWidgetsCount` is taken into account only when `collapsible` is `true`.",\n          "format": "int32",\n          "type": "integer"\n        },\n        "widgets": {\n          "description": "All the widgets in the section. Must contain at least one widget.",\n          "items": {\n            "$ref": "GoogleAppsCardV1Widget"\n          },\n          "type": "array"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1SelectionInput": {\n      "description": "A widget that creates one or more UI items that users can select. For example, a dropdown menu or checkboxes. You can use this widget to collect data that can be predicted or enumerated. Chat apps can process the value of items that users select or input. For details about working with form inputs, see [Receive form data](https://developers.google.com/chat/how-tos/dialogs#receive_form_data_from_dialogs). To collect undefined or abstract data from users, use the TextInput widget.",\n      "id": "GoogleAppsCardV1SelectionInput",\n      "properties": {\n        "items": {\n          "description": "An array of selectable items. For example, an array of radio buttons or checkboxes. Supports up to 100 items.",\n          "items": {\n            "$ref": "GoogleAppsCardV1SelectionItem"\n          },\n          "type": "array"\n        },\n        "label": {\n          "description": "The text that appears above the selection input field in the user interface. Specify text that helps the user enter the information your app needs. For example, if users are selecting the urgency of a work ticket from a drop-down menu, the label might be \\"Urgency\\" or \\"Select urgency\\".",\n          "type": "string"\n        },\n        "name": {\n          "description": "The name that identifies the selection input in a form input event. For details about working with form inputs, see [Receive form data](https://developers.google.com/chat/how-tos/dialogs#receive_form_data_from_dialogs).",\n          "type": "string"\n        },\n        "onChangeAction": {\n          "$ref": "GoogleAppsCardV1Action",\n          "description": "If specified, the form is submitted when the selection changes. If not specified, you must specify a separate button that submits the form. For details about working with form inputs, see [Receive form data](https://developers.google.com/chat/how-tos/dialogs#receive_form_data_from_dialogs)."\n        },\n        "type": {\n          "description": "The type of items that are displayed to users in a `SelectionInput` widget. Selection types support different types of interactions. For example, users can select one or more checkboxes, but they can only select one value from a dropdown menu.",\n          "enum": [\n            "CHECK_BOX",\n            "RADIO_BUTTON",\n            "SWITCH",\n            "DROPDOWN"\n          ],\n          "enumDescriptions": [\n            "A set of checkboxes. Users can select one or more checkboxes.",\n            "A set of radio buttons. Users can select one radio button.",\n            "A set of switches. Users can turn on one or more switches.",\n            "A dropdown menu. Users can select one item from the menu."\n          ],\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1SelectionItem": {\n      "description": "An item that users can select in a selection input, such as a checkbox or switch.",\n      "id": "GoogleAppsCardV1SelectionItem",\n      "properties": {\n        "selected": {\n          "description": "Whether the item is selected by default. If the selection input only accepts one value (such as for radio buttons or a dropdown menu), only set this field for one item.",\n          "type": "boolean"\n        },\n        "text": {\n          "description": "The text that identifies or describes the item to users.",\n          "type": "string"\n        },\n        "value": {\n          "description": "The value associated with this item. The client should use this as a form input value. For details about working with form inputs, see [Receive form data](https://developers.google.com/chat/how-tos/dialogs#receive_form_data_from_dialogs).",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1SuggestionItem": {\n      "description": "One suggested value that users can enter in a text input field.",\n      "id": "GoogleAppsCardV1SuggestionItem",\n      "properties": {\n        "text": {\n          "description": "The value of a suggested input to a text input field. This is equivalent to what users enter themselves.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1Suggestions": {\n      "description": "Suggested values that users can enter. These values appear when users click inside the text input field. As users type, the suggested values dynamically filter to match what the users have typed. For example, a text input field for programming language might suggest Java, JavaScript, Python, and C++. When users start typing `Jav`, the list of suggestions filters to show `Java` and `JavaScript`. Suggested values help guide users to enter values that your app can make sense of. When referring to JavaScript, some users might enter `javascript` and others `java script`. Suggesting `JavaScript` can standardize how users interact with your app. When specified, `TextInput.type` is always `SINGLE_LINE`, even if it\'s set to `MULTIPLE_LINE`.",\n      "id": "GoogleAppsCardV1Suggestions",\n      "properties": {\n        "items": {\n          "description": "A list of suggestions used for autocomplete recommendations in text input fields.",\n          "items": {\n            "$ref": "GoogleAppsCardV1SuggestionItem"\n          },\n          "type": "array"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1SwitchControl": {\n      "description": "Either a toggle-style switch or a checkbox inside a `decoratedText` widget. Only supported in the `decoratedText` widget.",\n      "id": "GoogleAppsCardV1SwitchControl",\n      "properties": {\n        "controlType": {\n          "description": "How the switch appears in the user interface.",\n          "enum": [\n            "SWITCH",\n            "CHECKBOX",\n            "CHECK_BOX"\n          ],\n          "enumDescriptions": [\n            "A toggle-style switch.",\n            "Deprecated in favor of `CHECK_BOX`.",\n            "A checkbox."\n          ],\n          "type": "string"\n        },\n        "name": {\n          "description": "The name by which the switch widget is identified in a form input event. For details about working with form inputs, see [Receive form data](https://developers.google.com/chat/how-tos/dialogs#receive_form_data_from_dialogs).",\n          "type": "string"\n        },\n        "onChangeAction": {\n          "$ref": "GoogleAppsCardV1Action",\n          "description": "The action to perform when the switch state is changed, such as what function to run."\n        },\n        "selected": {\n          "description": "When `true`, the switch is selected.",\n          "type": "boolean"\n        },\n        "value": {\n          "description": "The value entered by a user, returned as part of a form input event. For details about working with form inputs, see [Receive form data](https://developers.google.com/chat/how-tos/dialogs#receive_form_data_from_dialogs).",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1TextInput": {\n      "description": "A field in which users can enter text. Supports suggestions and on-change actions. Chat apps receive and can process the value of entered text during form input events. For details about working with form inputs, see [Receive form data](https://developers.google.com/chat/how-tos/dialogs#receive_form_data_from_dialogs). When you need to collect undefined or abstract data from users, use a text input. To collect defined or enumerated data from users, use the SelectionInput widget.",\n      "id": "GoogleAppsCardV1TextInput",\n      "properties": {\n        "autoCompleteAction": {\n          "$ref": "GoogleAppsCardV1Action",\n          "description": "Optional. Specify what action to take when the text input field provides suggestions to users who interact with it. If unspecified, the suggestions are set by `initialSuggestions` and are processed by the client. If specified, the app takes the action specified here, such as running a custom function. Supported by Google Workspace Add-ons, but not Chat apps."\n        },\n        "hintText": {\n          "description": "Text that appears below the text input field meant to assist users by prompting them to enter a certain value. This text is always visible. Required if `label` is unspecified. Otherwise, optional.",\n          "type": "string"\n        },\n        "initialSuggestions": {\n          "$ref": "GoogleAppsCardV1Suggestions",\n          "description": "Suggested values that users can enter. These values appear when users click inside the text input field. As users type, the suggested values dynamically filter to match what the users have typed. For example, a text input field for programming language might suggest Java, JavaScript, Python, and C++. When users start typing `Jav`, the list of suggestions filters to show just `Java` and `JavaScript`. Suggested values help guide users to enter values that your app can make sense of. When referring to JavaScript, some users might enter `javascript` and others `java script`. Suggesting `JavaScript` can standardize how users interact with your app. When specified, `TextInput.type` is always `SINGLE_LINE`, even if it\'s set to `MULTIPLE_LINE`."\n        },\n        "label": {\n          "description": "The text that appears above the text input field in the user interface. Specify text that helps the user enter the information your app needs. For example, if you are asking someone\'s name, but specifically need their surname, write `surname` instead of `name`. Required if `hintText` is unspecified. Otherwise, optional.",\n          "type": "string"\n        },\n        "name": {\n          "description": "The name by which the text input is identified in a form input event. For details about working with form inputs, see [Receive form data](https://developers.google.com/chat/how-tos/dialogs#receive_form_data_from_dialogs).",\n          "type": "string"\n        },\n        "onChangeAction": {\n          "$ref": "GoogleAppsCardV1Action",\n          "description": "What to do when a change occurs in the text input field. For example, a user adding to the field or deleting text. Examples of actions to take include running a custom function or opening a [dialog](https://developers.google.com/chat/how-tos/dialogs) in Google Chat."\n        },\n        "type": {\n          "description": "How a text input field appears in the user interface. For example, whether the field is single or multi-line.",\n          "enum": [\n            "SINGLE_LINE",\n            "MULTIPLE_LINE"\n          ],\n          "enumDescriptions": [\n            "The text input field has a fixed height of one line.",\n            "The text input field has a fixed height of multiple lines."\n          ],\n          "type": "string"\n        },\n        "value": {\n          "description": "The value entered by a user, returned as part of a form input event. For details about working with form inputs, see [Receive form data](https://developers.google.com/chat/how-tos/dialogs#receive_form_data_from_dialogs).",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1TextParagraph": {\n      "description": "A paragraph of text that supports formatting. For more information about formatting text, see [Formatting text in Google Chat apps](https://developers.google.com/chat/api/guides/message-formats/cards#card_text_formatting) and [Formatting text in Google Workspace Add-ons](https://developers.google.com/apps-script/add-ons/concepts/widgets#text_formatting).",\n      "id": "GoogleAppsCardV1TextParagraph",\n      "properties": {\n        "text": {\n          "description": "The text that\'s shown in the widget.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1Widget": {\n      "description": "Each card is made up of widgets. A widget is a composite object that can represent one of text, images, buttons, and other object types.",\n      "id": "GoogleAppsCardV1Widget",\n      "properties": {\n        "buttonList": {\n          "$ref": "GoogleAppsCardV1ButtonList",\n          "description": "A list of buttons. For example, the following JSON creates two buttons. The first is a blue text button and the second is an image button that opens a link: ``` \\"buttonList\\": { \\"buttons\\": [ { \\"text\\": \\"Edit\\", \\"color\\": { \\"red\\": 0, \\"green\\": 0, \\"blue\\": 1, \\"alpha\\": 1 }, \\"disabled\\": true, }, { \\"icon\\": { \\"knownIcon\\": \\"INVITE\\", \\"altText\\": \\"check calendar\\" }, \\"onClick\\": { \\"openLink\\": { \\"url\\": \\"https://example.com/calendar\\" } } } ] } ```"\n        },\n        "columns": {\n          "$ref": "GoogleAppsCardV1Columns",\n          "description": "Displays up to 2 columns. To include more than 2 columns, or to use rows, use the `Grid` widget. For example, the following JSON creates 2 columns that each contain text paragraphs: ``` \\"columns\\": { \\"columnItems\\": [ { \\"horizontalSizeStyle\\": \\"FILL_AVAILABLE_SPACE\\", \\"horizontalAlignment\\": \\"CENTER\\", \\"verticalAlignment\\": \\"CENTER\\", \\"widgets\\": [ { \\"textParagraph\\": { \\"text\\": \\"First column text paragraph\\" } } ] }, { \\"horizontalSizeStyle\\": \\"FILL_AVAILABLE_SPACE\\", \\"horizontalAlignment\\": \\"CENTER\\", \\"verticalAlignment\\": \\"CENTER\\", \\"widgets\\": [ { \\"textParagraph\\": { \\"text\\": \\"Second column text paragraph\\" } } ] } ] } ```"\n        },\n        "dateTimePicker": {\n          "$ref": "GoogleAppsCardV1DateTimePicker",\n          "description": "Displays a widget that lets users input a date, time, or date and time. For example, the following JSON creates a date time picker to schedule an appointment: ``` \\"dateTimePicker\\": { \\"name\\": \\"appointment_time\\", \\"label\\": \\"Book your appointment at:\\", \\"type\\": \\"DATE_AND_TIME\\", \\"valueMsEpoch\\": \\"796435200000\\" } ```"\n        },\n        "decoratedText": {\n          "$ref": "GoogleAppsCardV1DecoratedText",\n          "description": "Displays a decorated text item. For example, the following JSON creates a decorated text widget showing email address: ``` \\"decoratedText\\": { \\"icon\\": { \\"knownIcon\\": \\"EMAIL\\" }, \\"topLabel\\": \\"Email Address\\", \\"text\\": \\"sasha@example.com\\", \\"bottomLabel\\": \\"This is a new Email address!\\", \\"switchControl\\": { \\"name\\": \\"has_send_welcome_email_to_sasha\\", \\"selected\\": false, \\"controlType\\": \\"CHECKBOX\\" } } ```"\n        },\n        "divider": {\n          "$ref": "GoogleAppsCardV1Divider",\n          "description": "Displays a horizontal line divider between widgets. For example, the following JSON creates a divider: ``` \\"divider\\": { } ```"\n        },\n        "grid": {\n          "$ref": "GoogleAppsCardV1Grid",\n          "description": "Displays a grid with a collection of items. A grid supports any number of columns and items. The number of rows is determined by the upper bounds of the number items divided by the number of columns. A grid with 10 items and 2 columns has 5 rows. A grid with 11 items and 2 columns has 6 rows. For example, the following JSON creates a 2 column grid with a single item: ``` \\"grid\\": { \\"title\\": \\"A fine collection of items\\", \\"columnCount\\": 2, \\"borderStyle\\": { \\"type\\": \\"STROKE\\", \\"cornerRadius\\": 4 }, \\"items\\": [ { \\"image\\": { \\"imageUri\\": \\"https://www.example.com/image.png\\", \\"cropStyle\\": { \\"type\\": \\"SQUARE\\" }, \\"borderStyle\\": { \\"type\\": \\"STROKE\\" } }, \\"title\\": \\"An item\\", \\"textAlignment\\": \\"CENTER\\" } ], \\"onClick\\": { \\"openLink\\": { \\"url\\": \\"https://www.example.com\\" } } } ```"\n        },\n        "horizontalAlignment": {\n          "description": "Specifies whether widgets align to the left, right, or center of a column.",\n          "enum": [\n            "HORIZONTAL_ALIGNMENT_UNSPECIFIED",\n            "START",\n            "CENTER",\n            "END"\n          ],\n          "enumDescriptions": [\n            "Don\'t use. Unspecified.",\n            "Default value. Aligns widgets to the start position of the column. For left-to-right layouts, aligns to the left. For right-to-left layouts, aligns to the right.",\n            "Aligns widgets to the center of the column.",\n            "Aligns widgets to the end position of the column. For left-to-right layouts, aligns widgets to the right. For right-to-left layouts, aligns widgets to the left."\n          ],\n          "type": "string"\n        },\n        "image": {\n          "$ref": "GoogleAppsCardV1Image",\n          "description": "Displays an image. For example, the following JSON creates an image with alternative text: ``` \\"image\\": { \\"imageUrl\\": \\"https://developers.google.com/chat/images/quickstart-app-avatar.png\\", \\"altText\\": \\"Chat app avatar\\" } ```"\n        },\n        "selectionInput": {\n          "$ref": "GoogleAppsCardV1SelectionInput",\n          "description": "Displays a selection control that lets users select items. Selection controls can be checkboxes, radio buttons, switches, or dropdown menus. For example, the following JSON creates a dropdown menu that lets users choose a size: ``` \\"selectionInput\\": { \\"name\\": \\"size\\", \\"label\\": \\"Size\\" \\"type\\": \\"DROPDOWN\\", \\"items\\": [ { \\"text\\": \\"S\\", \\"value\\": \\"small\\", \\"selected\\": false }, { \\"text\\": \\"M\\", \\"value\\": \\"medium\\", \\"selected\\": true }, { \\"text\\": \\"L\\", \\"value\\": \\"large\\", \\"selected\\": false }, { \\"text\\": \\"XL\\", \\"value\\": \\"extra_large\\", \\"selected\\": false } ] } ```"\n        },\n        "textInput": {\n          "$ref": "GoogleAppsCardV1TextInput",\n          "description": "Displays a text box that users can type into. For example, the following JSON creates a text input for an email address: ``` \\"textInput\\": { \\"name\\": \\"mailing_address\\", \\"label\\": \\"Mailing Address\\" } ``` As another example, the following JSON creates a text input for a programming language with static suggestions: ``` \\"textInput\\": { \\"name\\": \\"preferred_programing_language\\", \\"label\\": \\"Preferred Language\\", \\"initialSuggestions\\": { \\"items\\": [ { \\"text\\": \\"C++\\" }, { \\"text\\": \\"Java\\" }, { \\"text\\": \\"JavaScript\\" }, { \\"text\\": \\"Python\\" } ] } } ```"\n        },\n        "textParagraph": {\n          "$ref": "GoogleAppsCardV1TextParagraph",\n          "description": "Displays a text paragraph. Supports simple HTML formatted text. For more information about formatting text, see [Formatting text in Google Chat apps](https://developers.google.com/chat/api/guides/message-formats/cards#card_text_formatting) and [Formatting text in Google Workspace Add-ons](https://developers.google.com/apps-script/add-ons/concepts/widgets#text_formatting). For example, the following JSON creates a bolded text: ``` \\"textParagraph\\": { \\"text\\": \\" *bold text*\\" } ```"\n        }\n      },\n      "type": "object"\n    },\n    "GoogleAppsCardV1Widgets": {\n      "description": "The supported widgets that you can include in a column.",\n      "id": "GoogleAppsCardV1Widgets",\n      "properties": {\n        "buttonList": {\n          "$ref": "GoogleAppsCardV1ButtonList",\n          "description": "ButtonList widget."\n        },\n        "dateTimePicker": {\n          "$ref": "GoogleAppsCardV1DateTimePicker",\n          "description": "DateTimePicker widget."\n        },\n        "decoratedText": {\n          "$ref": "GoogleAppsCardV1DecoratedText",\n          "description": "DecoratedText widget."\n        },\n        "image": {\n          "$ref": "GoogleAppsCardV1Image",\n          "description": "Image widget."\n        },\n        "selectionInput": {\n          "$ref": "GoogleAppsCardV1SelectionInput",\n          "description": "SelectionInput widget."\n        },\n        "textInput": {\n          "$ref": "GoogleAppsCardV1TextInput",\n          "description": "TextInput widget."\n        },\n        "textParagraph": {\n          "$ref": "GoogleAppsCardV1TextParagraph",\n          "description": "TextParagraph widget."\n        }\n      },\n      "type": "object"\n    },\n    "Image": {\n      "description": "An image that\'s specified by a URL and can have an `onclick` action.",\n      "id": "Image",\n      "properties": {\n        "aspectRatio": {\n          "description": "The aspect ratio of this image (width and height). This field lets you reserve the right height for the image while waiting for it to load. It\'s not meant to override the built-in aspect ratio of the image. If unset, the server fills it by prefetching the image.",\n          "format": "double",\n          "type": "number"\n        },\n        "imageUrl": {\n          "description": "The URL of the image.",\n          "type": "string"\n        },\n        "onClick": {\n          "$ref": "OnClick",\n          "description": "The `onclick` action."\n        }\n      },\n      "type": "object"\n    },\n    "ImageButton": {\n      "description": "An image button with an `onclick` action.",\n      "id": "ImageButton",\n      "properties": {\n        "icon": {\n          "description": "The icon specified by an `enum` that indices to an icon provided by Chat API.",\n          "enum": [\n            "ICON_UNSPECIFIED",\n            "AIRPLANE",\n            "BOOKMARK",\n            "BUS",\n            "CAR",\n            "CLOCK",\n            "CONFIRMATION_NUMBER_ICON",\n            "DOLLAR",\n            "DESCRIPTION",\n            "EMAIL",\n            "EVENT_PERFORMER",\n            "EVENT_SEAT",\n            "FLIGHT_ARRIVAL",\n            "FLIGHT_DEPARTURE",\n            "HOTEL",\n            "HOTEL_ROOM_TYPE",\n            "INVITE",\n            "MAP_PIN",\n            "MEMBERSHIP",\n            "MULTIPLE_PEOPLE",\n            "OFFER",\n            "PERSON",\n            "PHONE",\n            "RESTAURANT_ICON",\n            "SHOPPING_CART",\n            "STAR",\n            "STORE",\n            "TICKET",\n            "TRAIN",\n            "VIDEO_CAMERA",\n            "VIDEO_PLAY"\n          ],\n          "enumDescriptions": [\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            ""\n          ],\n          "type": "string"\n        },\n        "iconUrl": {\n          "description": "The icon specified by a URL.",\n          "type": "string"\n        },\n        "name": {\n          "description": "The name of this `image_button` that\'s used for accessibility. Default value is provided if this name isn\'t specified.",\n          "type": "string"\n        },\n        "onClick": {\n          "$ref": "OnClick",\n          "description": "The `onclick` action."\n        }\n      },\n      "type": "object"\n    },\n    "Inputs": {\n      "description": "Types of data inputs for widgets. Users enter data with these inputs.",\n      "id": "Inputs",\n      "properties": {\n        "dateInput": {\n          "$ref": "DateInput",\n          "description": "Date input values."\n        },\n        "dateTimeInput": {\n          "$ref": "DateTimeInput",\n          "description": "Date and time input values."\n        },\n        "stringInputs": {\n          "$ref": "StringInputs",\n          "description": "Input parameter for regular widgets. For single-valued widgets, it is a single value list. For multi-valued widgets, such as checkbox, all the values are presented."\n        },\n        "timeInput": {\n          "$ref": "TimeInput",\n          "description": "Time input values."\n        }\n      },\n      "type": "object"\n    },\n    "KeyValue": {\n      "description": "A UI element contains a key (label) and a value (content). This element can also contain some actions such as `onclick` button.",\n      "id": "KeyValue",\n      "properties": {\n        "bottomLabel": {\n          "description": "The text of the bottom label. Formatted text supported. For more information about formatting text, see [Formatting text in Google Chat apps](https://developers.google.com/chat/api/guides/message-formats/cards#card_text_formatting) and [Formatting text in Google Workspace Add-ons](https://developers.google.com/apps-script/add-ons/concepts/widgets#text_formatting).",\n          "type": "string"\n        },\n        "button": {\n          "$ref": "Button",\n          "description": "A button that can be clicked to trigger an action."\n        },\n        "content": {\n          "description": "The text of the content. Formatted text supported and always required. For more information about formatting text, see [Formatting text in Google Chat apps](https://developers.google.com/chat/api/guides/message-formats/cards#card_text_formatting) and [Formatting text in Google Workspace Add-ons](https://developers.google.com/apps-script/add-ons/concepts/widgets#text_formatting).",\n          "type": "string"\n        },\n        "contentMultiline": {\n          "description": "If the content should be multiline.",\n          "type": "boolean"\n        },\n        "icon": {\n          "description": "An enum value that\'s replaced by the Chat API with the corresponding icon image.",\n          "enum": [\n            "ICON_UNSPECIFIED",\n            "AIRPLANE",\n            "BOOKMARK",\n            "BUS",\n            "CAR",\n            "CLOCK",\n            "CONFIRMATION_NUMBER_ICON",\n            "DOLLAR",\n            "DESCRIPTION",\n            "EMAIL",\n            "EVENT_PERFORMER",\n            "EVENT_SEAT",\n            "FLIGHT_ARRIVAL",\n            "FLIGHT_DEPARTURE",\n            "HOTEL",\n            "HOTEL_ROOM_TYPE",\n            "INVITE",\n            "MAP_PIN",\n            "MEMBERSHIP",\n            "MULTIPLE_PEOPLE",\n            "OFFER",\n            "PERSON",\n            "PHONE",\n            "RESTAURANT_ICON",\n            "SHOPPING_CART",\n            "STAR",\n            "STORE",\n            "TICKET",\n            "TRAIN",\n            "VIDEO_CAMERA",\n            "VIDEO_PLAY"\n          ],\n          "enumDescriptions": [\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            "",\n            ""\n          ],\n          "type": "string"\n        },\n        "iconUrl": {\n          "description": "The icon specified by a URL.",\n          "type": "string"\n        },\n        "onClick": {\n          "$ref": "OnClick",\n          "description": "The `onclick` action. Only the top label, bottom label, and content region are clickable."\n        },\n        "topLabel": {\n          "description": "The text of the top label. Formatted text supported. For more information about formatting text, see [Formatting text in Google Chat apps](https://developers.google.com/chat/api/guides/message-formats/cards#card_text_formatting) and [Formatting text in Google Workspace Add-ons](https://developers.google.com/apps-script/add-ons/concepts/widgets#text_formatting).",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "ListMembershipsResponse": {\n      "id": "ListMembershipsResponse",\n      "properties": {\n        "memberships": {\n          "description": "List of memberships in the requested (or first) page.",\n          "items": {\n            "$ref": "Membership"\n          },\n          "type": "array"\n        },\n        "nextPageToken": {\n          "description": "A token that you can send as `pageToken` to retrieve the next page of results. If empty, there are no subsequent pages.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "ListMessagesResponse": {\n      "id": "ListMessagesResponse",\n      "properties": {\n        "messages": {\n          "description": "List of messages.",\n          "items": {\n            "$ref": "Message"\n          },\n          "type": "array"\n        },\n        "nextPageToken": {\n          "description": "You can send a token as `pageToken` to retrieve the next page of results. If empty, there are no subsequent pages.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "ListReactionsResponse": {\n      "id": "ListReactionsResponse",\n      "properties": {\n        "nextPageToken": {\n          "description": "Continuation token to retrieve the next page of results. It\'s empty for the last page of results.",\n          "type": "string"\n        },\n        "reactions": {\n          "description": "List of reactions in the requested (or first) page.",\n          "items": {\n            "$ref": "Reaction"\n          },\n          "type": "array"\n        }\n      },\n      "type": "object"\n    },\n    "ListSpacesResponse": {\n      "id": "ListSpacesResponse",\n      "properties": {\n        "nextPageToken": {\n          "description": "You can send a token as `pageToken` to retrieve the next page of results. If empty, there are no subsequent pages.",\n          "type": "string"\n        },\n        "spaces": {\n          "description": "List of spaces in the requested (or first) page.",\n          "items": {\n            "$ref": "Space"\n          },\n          "type": "array"\n        }\n      },\n      "type": "object"\n    },\n    "MatchedUrl": {\n      "description": "A matched URL in a Chat message. Chat apps can preview matched URLs. For more information, see [Preview links](https://developers.google.com/chat/how-tos/preview-links).",\n      "id": "MatchedUrl",\n      "properties": {\n        "url": {\n          "description": "Output only. The URL that was matched.",\n          "readOnly": true,\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "Media": {\n      "description": "Media resource.",\n      "id": "Media",\n      "properties": {\n        "resourceName": {\n          "description": "Name of the media resource.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "Membership": {\n      "description": "Represents a membership relation in Google Chat, such as whether a user or Chat app is invited to, part of, or absent from a space.",\n      "id": "Membership",\n      "properties": {\n        "createTime": {\n          "description": "Output only. The creation time of the membership, such as when a member joined or was invited to join a space.",\n          "format": "google-datetime",\n          "readOnly": true,\n          "type": "string"\n        },\n        "member": {\n          "$ref": "User",\n          "description": "The Google Chat user or app the membership corresponds to. If your Chat app [authenticates as a user](https://developers.google.com/chat/api/guides/auth/users), the output populates the [user](https://developers.google.com/chat/api/reference/rest/v1/User) `name` and `type`."\n        },\n        "name": {\n          "description": "Resource name of the membership, assigned by the server. Format: `spaces/{space}/members/{member}`",\n          "type": "string"\n        },\n        "role": {\n          "description": "Output only. User\'s role within a Chat space, which determines their permitted actions in the space.",\n          "enum": [\n            "MEMBERSHIP_ROLE_UNSPECIFIED",\n            "ROLE_MEMBER",\n            "ROLE_MANAGER"\n          ],\n          "enumDescriptions": [\n            "Default value. For users: they aren\'t a member of the space, but can be invited. For Google Groups: they\'re always assigned this role (other enum values might be used in the future).",\n            "A member of the space. The user has basic permissions, like sending messages to the space. In 1:1 and unnamed group conversations, everyone has this role.",\n            "A space manager. The user has all basic permissions plus administrative permissions that let them manage the space, like adding or removing members. Only supported in SpaceType.SPACE."\n          ],\n          "readOnly": true,\n          "type": "string"\n        },\n        "state": {\n          "description": "Output only. State of the membership.",\n          "enum": [\n            "MEMBERSHIP_STATE_UNSPECIFIED",\n            "JOINED",\n            "INVITED",\n            "NOT_A_MEMBER"\n          ],\n          "enumDescriptions": [\n            "Default, don\'t use.",\n            "The user has joined the space.",\n            "The user has been invited, is able to join the space, but currently hasn\'t joined.",\n            "The user isn\'t a member of the space, hasn\'t been invited and isn\'t able to join the space."\n          ],\n          "readOnly": true,\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "Message": {\n      "description": "A message in Google Chat.",\n      "id": "Message",\n      "properties": {\n        "actionResponse": {\n          "$ref": "ActionResponse",\n          "description": "Input only. Parameters that a Chat app can use to configure how its response is posted."\n        },\n        "annotations": {\n          "description": "Output only. Annotations associated with the `text` in this message.",\n          "items": {\n            "$ref": "Annotation"\n          },\n          "readOnly": true,\n          "type": "array"\n        },\n        "argumentText": {\n          "description": "Output only. Plain-text body of the message with all Chat app mentions stripped out.",\n          "readOnly": true,\n          "type": "string"\n        },\n        "attachedGifs": {\n          "description": "Output only. GIF images that are attached to the message.",\n          "items": {\n            "$ref": "AttachedGif"\n          },\n          "readOnly": true,\n          "type": "array"\n        },\n        "attachment": {\n          "description": "User-uploaded attachment.",\n          "items": {\n            "$ref": "Attachment"\n          },\n          "type": "array"\n        },\n        "cards": {\n          "deprecated": true,\n          "description": "Deprecated: Use `cards_v2` instead. Rich, formatted, and interactive cards that you can use to display UI elements such as: formatted texts, buttons, and clickable images. Cards are normally displayed below the plain-text body of the message. `cards` and `cards_v2` can have a maximum size of 32 KB.",\n          "items": {\n            "$ref": "Card"\n          },\n          "type": "array"\n        },\n        "cardsV2": {\n          "description": "Richly formatted and interactive cards that display UI elements and editable widgets, such as: - Formatted text - Buttons - Clickable images - Checkboxes - Radio buttons - Input widgets. Cards are usually displayed below the text body of a Chat message, but can situationally appear other places, such as [dialogs](https://developers.google.com/chat/how-tos/dialogs). Each card can have a maximum size of 32 KB. The `cardId` is a unique identifier among cards in the same message and for identifying user input values. Currently supported widgets include: - `TextParagraph` - `DecoratedText` - `Image` - `ButtonList` - `Divider` - `TextInput` - `SelectionInput` - `Grid`",\n          "items": {\n            "$ref": "CardWithId"\n          },\n          "type": "array"\n        },\n        "clientAssignedMessageId": {\n          "description": "A custom name for a Chat message assigned at creation. Must start with `client-` and contain only lowercase letters, numbers, and hyphens up to 63 characters in length. Specify this field to get, update, or delete the message with the specified value. Assigning a custom name lets a Chat app recall the message without saving the message `name` from the [response body](/chat/api/reference/rest/v1/spaces.messages/get#response-body) returned when creating the message. Assigning a custom name doesn\'t replace the generated `name` field, the message\'s resource name. Instead, it sets the custom name as the `clientAssignedMessageId` field, which you can reference while processing later operations, like updating or deleting the message. For example usage, see [Name a created message](https://developers.google.com/chat/api/guides/v1/messages/create#name_a_created_message).",\n          "type": "string"\n        },\n        "createTime": {\n          "description": "For spaces created in Chat, the time at which the message was created. This field is output only, except when used in imported spaces. [Developer Preview](https://developers.google.com/workspace/preview): For imported spaces, set this field to the historical timestamp at which the message was created in the source in order to preserve the original creation time.",\n          "format": "google-datetime",\n          "type": "string"\n        },\n        "deleteTime": {\n          "description": "Output only. The time at which the message was deleted in Google Chat. If the message is never deleted, this field is empty.",\n          "format": "google-datetime",\n          "readOnly": true,\n          "type": "string"\n        },\n        "deletionMetadata": {\n          "$ref": "DeletionMetadata",\n          "description": "Output only. Information about a deleted message. A message is deleted when `delete_time` is set.",\n          "readOnly": true\n        },\n        "emojiReactionSummaries": {\n          "description": "Output only. The list of emoji reaction summaries on the message.",\n          "items": {\n            "$ref": "EmojiReactionSummary"\n          },\n          "readOnly": true,\n          "type": "array"\n        },\n        "fallbackText": {\n          "description": "A plain-text description of the message\'s cards, used when the actual cards can\'t be displayed\\u2014for example, mobile notifications.",\n          "type": "string"\n        },\n        "lastUpdateTime": {\n          "description": "Output only. The time at which the message was last edited by a user. If the message has never been edited, this field is empty.",\n          "format": "google-datetime",\n          "readOnly": true,\n          "type": "string"\n        },\n        "matchedUrl": {\n          "$ref": "MatchedUrl",\n          "description": "Output only. A URL in `spaces.messages.text` that matches a link preview pattern. For more information, see [Preview links](https://developers.google.com/chat/how-tos/preview-links).",\n          "readOnly": true\n        },\n        "name": {\n          "description": "Resource name in the form `spaces/*/messages/*`. Example: `spaces/AAAAAAAAAAA/messages/BBBBBBBBBBB.BBBBBBBBBBB`",\n          "type": "string"\n        },\n        "quotedMessageMetadata": {\n          "$ref": "QuotedMessageMetadata",\n          "description": "Output only. Information about a message that\'s quoted by a Google Chat user in a space. Google Chat users can quote a message to reply to it.",\n          "readOnly": true\n        },\n        "sender": {\n          "$ref": "User",\n          "description": "Output only. The user who created the message. If your Chat app [authenticates as a user](https://developers.google.com/chat/api/guides/auth/users), the output populates the [user](https://developers.google.com/chat/api/reference/rest/v1/User) `name` and `type`.",\n          "readOnly": true\n        },\n        "slashCommand": {\n          "$ref": "SlashCommand",\n          "description": "Output only. Slash command information, if applicable.",\n          "readOnly": true\n        },\n        "space": {\n          "$ref": "Space",\n          "description": "If your Chat app [authenticates as a user](https://developers.google.com/chat/api/guides/auth/users), the output populates the [space](https://developers.google.com/chat/api/reference/rest/v1/spaces) `name`."\n        },\n        "text": {\n          "description": "Plain-text body of the message. The first link to an image, video, web page, or other preview-able item generates a preview chip.",\n          "type": "string"\n        },\n        "thread": {\n          "$ref": "Thread",\n          "description": "The thread the message belongs to. For example usage, see [Start or reply to a message thread](https://developers.google.com/chat/api/guides/crudl/messages#start_or_reply_to_a_message_thread)."\n        },\n        "threadReply": {\n          "description": "Output only. When `true`, the message is a response in a reply thread. When `false`, the message is visible in the space\'s top-level conversation as either the first message of a thread or a message with no threaded replies. If the space doesn\'t support reply in threads, this field is always `false`.",\n          "readOnly": true,\n          "type": "boolean"\n        }\n      },\n      "type": "object"\n    },\n    "OnClick": {\n      "description": "An `onclick` action (for example, open a link).",\n      "id": "OnClick",\n      "properties": {\n        "action": {\n          "$ref": "FormAction",\n          "description": "A form action is triggered by this `onclick` action if specified."\n        },\n        "openLink": {\n          "$ref": "OpenLink",\n          "description": "This `onclick` action triggers an open link action if specified."\n        }\n      },\n      "type": "object"\n    },\n    "OpenLink": {\n      "description": "A link that opens a new window.",\n      "id": "OpenLink",\n      "properties": {\n        "url": {\n          "description": "The URL to open.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "QuotedMessageMetadata": {\n      "description": "Information about a quoted message.",\n      "id": "QuotedMessageMetadata",\n      "properties": {\n        "lastUpdateTime": {\n          "description": "Output only. The timestamp when the quoted message was created or when the quoted message was last updated.",\n          "format": "google-datetime",\n          "readOnly": true,\n          "type": "string"\n        },\n        "name": {\n          "description": "Output only. Resource name of the quoted message. Format: `spaces/{space}/messages/{message}`",\n          "readOnly": true,\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "Reaction": {\n      "description": "A reaction to a message.",\n      "id": "Reaction",\n      "properties": {\n        "emoji": {\n          "$ref": "Emoji",\n          "description": "The emoji used in the reaction."\n        },\n        "name": {\n          "description": "The resource name of the reaction. Format: `spaces/{space}/messages/{message}/reactions/{reaction}`",\n          "type": "string"\n        },\n        "user": {\n          "$ref": "User",\n          "description": "Output only. The user who created the reaction.",\n          "readOnly": true\n        }\n      },\n      "type": "object"\n    },\n    "Section": {\n      "description": "A section contains a collection of widgets that are rendered (vertically) in the order that they are specified. Across all platforms, cards have a narrow fixed width, so there\'s currently no need for layout properties (for example, float).",\n      "id": "Section",\n      "properties": {\n        "header": {\n          "description": "The header of the section. Formatted text is supported. For more information about formatting text, see [Formatting text in Google Chat apps](https://developers.google.com/chat/api/guides/message-formats/cards#card_text_formatting) and [Formatting text in Google Workspace Add-ons](https://developers.google.com/apps-script/add-ons/concepts/widgets#text_formatting).",\n          "type": "string"\n        },\n        "widgets": {\n          "description": "A section must contain at least one widget.",\n          "items": {\n            "$ref": "WidgetMarkup"\n          },\n          "type": "array"\n        }\n      },\n      "type": "object"\n    },\n    "SetUpSpaceRequest": {\n      "id": "SetUpSpaceRequest",\n      "properties": {\n        "memberships": {\n          "description": "Optional. The initial set of in-domain users invited to join the space. The calling user is automatically added to the space, and shouldn\'t be specified as a membership. The set currently allows up to 20 memberships (in addition to the caller). The `Membership.member` field must contain a user with `name` populated and `User.Type.HUMAN`. All other fields are ignored. Optional when setting `Space.spaceType` to `SPACE`. Required when setting `Space.spaceType` to `GROUP_CHAT`, along with at least two memberships. Required when setting `Space.spaceType` to `DIRECT_MESSAGE` with a human user, along with exactly one membership. Must be empty when creating a 1:1 conversation between a human and the calling Chat app (when setting `Space.spaceType` to `DIRECT_MESSAGE` and `Space.singleUserBotDm` to `true`). Not supported: Inviting guest users, or adding other Chat apps.",\n          "items": {\n            "$ref": "Membership"\n          },\n          "type": "array"\n        },\n        "requestId": {\n          "description": "Optional. A unique identifier for this request. A random UUID is recommended. Specifying an existing request ID returns the space created with that ID instead of creating a new space. Specifying an existing request ID from the same Chat app with a different authenticated user returns an error.",\n          "type": "string"\n        },\n        "space": {\n          "$ref": "Space",\n          "description": "Required. The `Space.spaceType` field is required. To create a space, set `Space.spaceType` to `SPACE` and set `Space.displayName`. To create a group chat, set `Space.spaceType` to `GROUP_CHAT`. Don\'t set `Space.displayName`. To create a 1:1 conversation between humans, set `Space.spaceType` to `DIRECT_MESSAGE` and set `Space.singleUserBotDm` to `false`. Don\'t set `Space.displayName` or `Space.spaceDetails`. To create an 1:1 conversation between a human and the calling Chat app, set `Space.spaceType` to `DIRECT_MESSAGE` and `Space.singleUserBotDm` to `true`. Don\'t set `Space.displayName` or `Space.spaceDetails`. If a `DIRECT_MESSAGE` space already exists, that space is returned instead of creating a new space."\n        }\n      },\n      "type": "object"\n    },\n    "SlashCommand": {\n      "description": "A [slash command](https://developers.google.com/chat/how-tos/slash-commands) in Google Chat.",\n      "id": "SlashCommand",\n      "properties": {\n        "commandId": {\n          "description": "The ID of the slash command invoked.",\n          "format": "int64",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "SlashCommandMetadata": {\n      "description": "Annotation metadata for slash commands (/).",\n      "id": "SlashCommandMetadata",\n      "properties": {\n        "bot": {\n          "$ref": "User",\n          "description": "The Chat app whose command was invoked."\n        },\n        "commandId": {\n          "description": "The command ID of the invoked slash command.",\n          "format": "int64",\n          "type": "string"\n        },\n        "commandName": {\n          "description": "The name of the invoked slash command.",\n          "type": "string"\n        },\n        "triggersDialog": {\n          "description": "Indicates whether the slash command is for a dialog.",\n          "type": "boolean"\n        },\n        "type": {\n          "description": "The type of slash command.",\n          "enum": [\n            "TYPE_UNSPECIFIED",\n            "ADD",\n            "INVOKE"\n          ],\n          "enumDescriptions": [\n            "Default value for the enum. Don\'t use.",\n            "Add Chat app to space.",\n            "Invoke slash command in space."\n          ],\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "Space": {\n      "description": "A space in Google Chat. Spaces are conversations between two or more users or 1:1 messages between a user and a Chat app.",\n      "id": "Space",\n      "properties": {\n        "adminInstalled": {\n          "description": "Output only. Whether the Chat app was installed by a Google Workspace administrator. Administrators can install a Chat app for their domain, organizational unit, or a group of users. Administrators can only install Chat apps for direct messaging between users and the app. To support admin install, your app must feature direct messaging.",\n          "readOnly": true,\n          "type": "boolean"\n        },\n        "displayName": {\n          "description": "The space\'s display name. Required when [creating a space](https://developers.google.com/chat/api/reference/rest/v1/spaces/create). For direct messages, this field might be empty. Supports up to 128 characters.",\n          "type": "string"\n        },\n        "name": {\n          "description": "Resource name of the space. Format: `spaces/{space}`",\n          "type": "string"\n        },\n        "singleUserBotDm": {\n          "description": "Optional. Whether the space is a DM between a Chat app and a single human.",\n          "type": "boolean"\n        },\n        "spaceDetails": {\n          "$ref": "SpaceDetails",\n          "description": "Details about the space including description and rules."\n        },\n        "spaceHistoryState": {\n          "description": "The message history state for messages and threads in this space.",\n          "enum": [\n            "HISTORY_STATE_UNSPECIFIED",\n            "HISTORY_OFF",\n            "HISTORY_ON"\n          ],\n          "enumDescriptions": [\n            "Default value. Do not use.",\n            "History off. [Messages and threads are kept for 24 hours](https://support.google.com/chat/answer/7664687).",\n            "History on. The organization\'s [Vault retention rules](https://support.google.com/vault/answer/7657597) specify for how long messages and threads are kept."\n          ],\n          "type": "string"\n        },\n        "spaceThreadingState": {\n          "description": "Output only. The threading state in the Chat space.",\n          "enum": [\n            "SPACE_THREADING_STATE_UNSPECIFIED",\n            "THREADED_MESSAGES",\n            "GROUPED_MESSAGES",\n            "UNTHREADED_MESSAGES"\n          ],\n          "enumDescriptions": [\n            "Reserved.",\n            "Named spaces that support message threads. When users respond to a message, they can reply in-thread, which keeps their response in the context of the original message.",\n            "Named spaces where the conversation is organized by topic. Topics and their replies are grouped together.",\n            "Direct messages (DMs) between two people and group conversations between 3 or more people."\n          ],\n          "readOnly": true,\n          "type": "string"\n        },\n        "spaceType": {\n          "description": "The type of space. Required when creating a space or updating the space type of a space. Output only for other usage.",\n          "enum": [\n            "SPACE_TYPE_UNSPECIFIED",\n            "SPACE",\n            "GROUP_CHAT",\n            "DIRECT_MESSAGE"\n          ],\n          "enumDescriptions": [\n            "Reserved.",\n            "A place where people send messages, share files, and collaborate. A `SPACE` can include Chat apps.",\n            "Group conversations between 3 or more people. A `GROUP_CHAT` can include Chat apps.",\n            "1:1 messages between two humans or a human and a Chat app."\n          ],\n          "type": "string"\n        },\n        "threaded": {\n          "deprecated": true,\n          "description": "Output only. Deprecated: Use `spaceThreadingState` instead. Whether messages are threaded in this space.",\n          "readOnly": true,\n          "type": "boolean"\n        },\n        "type": {\n          "deprecated": true,\n          "description": "Output only. Deprecated: Use `space_type` instead. The type of a space.",\n          "enum": [\n            "TYPE_UNSPECIFIED",\n            "ROOM",\n            "DM"\n          ],\n          "enumDescriptions": [\n            "",\n            "Conversations between two or more humans.",\n            "1:1 Direct Message between a human and a Chat app, where all messages are flat. Note that this doesn\'t include direct messages between two humans."\n          ],\n          "readOnly": true,\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "SpaceDetails": {\n      "description": "Details about the space including description and rules.",\n      "id": "SpaceDetails",\n      "properties": {\n        "description": {\n          "description": "Optional. A description of the space. For example, describe the space\'s discussion topic, functional purpose, or participants. Supports up to 150 characters.",\n          "type": "string"\n        },\n        "guidelines": {\n          "description": "Optional. The space\'s rules, expectations, and etiquette. Supports up to 5,000 characters.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "Status": {\n      "description": "The `Status` type defines a logical error model that is suitable for different programming environments, including REST APIs and RPC APIs. It is used by [gRPC](https://github.com/grpc). Each `Status` message contains three pieces of data: error code, error message, and error details. You can find out more about this error model and how to work with it in the [API Design Guide](https://cloud.google.com/apis/design/errors).",\n      "id": "Status",\n      "properties": {\n        "code": {\n          "description": "The status code, which should be an enum value of google.rpc.Code.",\n          "format": "int32",\n          "type": "integer"\n        },\n        "details": {\n          "description": "A list of messages that carry the error details. There is a common set of message types for APIs to use.",\n          "items": {\n            "additionalProperties": {\n              "description": "Properties of the object. Contains field @type with type URL.",\n              "type": "any"\n            },\n            "type": "object"\n          },\n          "type": "array"\n        },\n        "message": {\n          "description": "A developer-facing error message, which should be in English. Any user-facing error message should be localized and sent in the google.rpc.Status.details field, or localized by the client.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "StringInputs": {\n      "description": "Input parameter for regular widgets. For single-valued widgets, it is a single value list. For multi-valued widgets, such as checkbox, all the values are presented.",\n      "id": "StringInputs",\n      "properties": {\n        "value": {\n          "description": "An array of strings entered by the user.",\n          "items": {\n            "type": "string"\n          },\n          "type": "array"\n        }\n      },\n      "type": "object"\n    },\n    "TextButton": {\n      "description": "A button with text and `onclick` action.",\n      "id": "TextButton",\n      "properties": {\n        "onClick": {\n          "$ref": "OnClick",\n          "description": "The `onclick` action of the button."\n        },\n        "text": {\n          "description": "The text of the button.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "TextParagraph": {\n      "description": "A paragraph of text. Formatted text supported. For more information about formatting text, see [Formatting text in Google Chat apps](https://developers.google.com/chat/api/guides/message-formats/cards#card_text_formatting) and [Formatting text in Google Workspace Add-ons](https://developers.google.com/apps-script/add-ons/concepts/widgets#text_formatting).",\n      "id": "TextParagraph",\n      "properties": {\n        "text": {\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "Thread": {\n      "description": "A thread in Google Chat.",\n      "id": "Thread",\n      "properties": {\n        "name": {\n          "description": "Resource name of the thread. Example: `spaces/{space}/threads/{thread}`",\n          "type": "string"\n        },\n        "threadKey": {\n          "description": "Optional. Opaque thread identifier. To start or add to a thread, create a message and specify a `threadKey` or the thread.name. For example usage, see [Start or reply to a message thread](https://developers.google.com/chat/api/guides/crudl/messages#start_or_reply_to_a_message_thread). For other requests, this is an output only field.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "TimeInput": {\n      "description": "Time input values.",\n      "id": "TimeInput",\n      "properties": {\n        "hours": {\n          "description": "The hour on a 24-hour clock.",\n          "format": "int32",\n          "type": "integer"\n        },\n        "minutes": {\n          "description": "The number of minutes past the hour. Valid values are 0 to 59.",\n          "format": "int32",\n          "type": "integer"\n        }\n      },\n      "type": "object"\n    },\n    "TimeZone": {\n      "description": "The timezone ID and offset from Coordinated Universal Time (UTC). Only supported for the event types [`CARD_CLICKED`](https://developers.google.com/chat/api/reference/rest/v1/EventType#ENUM_VALUES.CARD_CLICKED) and [`SUBMIT_DIALOG`](https://developers.google.com/chat/api/reference/rest/v1/DialogEventType#ENUM_VALUES.SUBMIT_DIALOG).",\n      "id": "TimeZone",\n      "properties": {\n        "id": {\n          "description": "The [IANA TZ](https://www.iana.org/time-zones) time zone database code, such as \\"America/Toronto\\".",\n          "type": "string"\n        },\n        "offset": {\n          "description": "The user timezone offset, in milliseconds, from Coordinated Universal Time (UTC).",\n          "format": "int32",\n          "type": "integer"\n        }\n      },\n      "type": "object"\n    },\n    "UploadAttachmentRequest": {\n      "id": "UploadAttachmentRequest",\n      "properties": {\n        "filename": {\n          "description": "Required. The filename of the attachment, including the file extension.",\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "UploadAttachmentResponse": {\n      "id": "UploadAttachmentResponse",\n      "properties": {\n        "attachmentDataRef": {\n          "$ref": "AttachmentDataRef",\n          "description": "Reference to the uploaded attachment."\n        }\n      },\n      "type": "object"\n    },\n    "User": {\n      "description": "A user in Google Chat.",\n      "id": "User",\n      "properties": {\n        "displayName": {\n          "description": "Output only. The user\'s display name.",\n          "readOnly": true,\n          "type": "string"\n        },\n        "domainId": {\n          "description": "Unique identifier of the user\'s Google Workspace domain.",\n          "type": "string"\n        },\n        "isAnonymous": {\n          "description": "Output only. When `true`, the user is deleted or their profile is not visible.",\n          "readOnly": true,\n          "type": "boolean"\n        },\n        "name": {\n          "description": "Resource name for a Google Chat user. Format: `users/{user}`. `users/app` can be used as an alias for the calling app bot user. For human users, `{user}` is the same user identifier as: - the `{person_id`} for the [Person](https://developers.google.com/people/api/rest/v1/people) in the People API, where the Person `resource_name` is `people/{person_id}`. For example, `users/123456789` in Chat API represents the same person as `people/123456789` in People API. - the `id` for a [user](https://developers.google.com/admin-sdk/directory/reference/rest/v1/users) in the Admin SDK Directory API.",\n          "type": "string"\n        },\n        "type": {\n          "description": "User type.",\n          "enum": [\n            "TYPE_UNSPECIFIED",\n            "HUMAN",\n            "BOT"\n          ],\n          "enumDescriptions": [\n            "Default value for the enum. DO NOT USE.",\n            "Human user.",\n            "Chat app user."\n          ],\n          "type": "string"\n        }\n      },\n      "type": "object"\n    },\n    "UserMentionMetadata": {\n      "description": "Annotation metadata for user mentions (@).",\n      "id": "UserMentionMetadata",\n      "properties": {\n        "type": {\n          "description": "The type of user mention.",\n          "enum": [\n            "TYPE_UNSPECIFIED",\n            "ADD",\n            "MENTION"\n          ],\n          "enumDescriptions": [\n            "Default value for the enum. Don\'t use.",\n            "Add user to space.",\n            "Mention user in space."\n          ],\n          "type": "string"\n        },\n        "user": {\n          "$ref": "User",\n          "description": "The user mentioned."\n        }\n      },\n      "type": "object"\n    },\n    "WidgetMarkup": {\n      "description": "A widget is a UI element that presents text and images.",\n      "id": "WidgetMarkup",\n      "properties": {\n        "buttons": {\n          "description": "A list of buttons. Buttons is also `oneof data` and only one of these fields should be set.",\n          "items": {\n            "$ref": "Button"\n          },\n          "type": "array"\n        },\n        "image": {\n          "$ref": "Image",\n          "description": "Display an image in this widget."\n        },\n        "keyValue": {\n          "$ref": "KeyValue",\n          "description": "Display a key value item in this widget."\n        },\n        "textParagraph": {\n          "$ref": "TextParagraph",\n          "description": "Display a text paragraph in this widget."\n        }\n      },\n      "type": "object"\n    }\n  },\n  "servicePath": "",\n  "title": "Google Chat API",\n  "version": "v1",\n  "version_module": true\n}'        
        if content:
            return content
        else:
            raise UnknownApiNameOrVersion(
                "name: %s  version: %s" % (serviceName, version)
            )
    actual_url = url
    if "REMOTE_ADDR" in os.environ:
        actual_url = _add_query_parameter(url, "userIp", os.environ["REMOTE_ADDR"])
    if developerKey:
        actual_url = _add_query_parameter(url, "key", developerKey)
    logger.debug("URL being requested: GET %s", actual_url)
    req = HttpRequest(http, HttpRequest.null_postproc, actual_url)
    resp, content = req.execute(num_retries=num_retries)
    try:
        content = content.decode("utf-8")
    except AttributeError:
        pass
    try:
        service = json.loads(content)
    except ValueError as e:
        logger.error("Failed to parse as JSON: " + content)
        raise InvalidJsonError()
    if cache_discovery and cache:
        cache.set(url, content)
    return content
@positional(1)
def build_from_document(
    service,
    base=None,
    future=None,
    http=None,
    developerKey=None,
    model=None,
    requestBuilder=HttpRequest,
    credentials=None,
    client_options=None,
    adc_cert_path=None,
    adc_key_path=None,
    always_use_jwt_access=False,
):
    if client_options is None:
        client_options = google.api_core.client_options.ClientOptions()
    if isinstance(client_options, collections.abc.Mapping):
        client_options = google.api_core.client_options.from_dict(client_options)
    if http is not None:
        banned_options = [
            (credentials, "credentials"),
            (client_options.credentials_file, "client_options.credentials_file"),
        ]
        for option, name in banned_options:
            if option is not None:
                raise ValueError(
                    "Arguments http and {} are mutually exclusive".format(name)
                )
    if isinstance(service, str):
        service = json.loads(service)
    elif isinstance(service, bytes):
        service = json.loads(service.decode("utf-8"))
    if "rootUrl" not in service and isinstance(http, (HttpMock, HttpMockSequence)):
        logger.error(
            "You are using HttpMock or HttpMockSequence without"
            + "having the service discovery doc in cache. Try calling "
            + "build() without mocking once first to populate the "
            + "cache."
        )
        raise InvalidJsonError()
    base = urllib.parse.urljoin(service["rootUrl"], service["servicePath"])
    audience_for_self_signed_jwt = base
    if client_options.api_endpoint:
        base = client_options.api_endpoint
    schema = Schemas(service)
    if http is None:
        scopes = list(
            service.get("auth", {}).get("oauth2", {}).get("scopes", {}).keys()
        )
        if scopes and not developerKey:
            if client_options.credentials_file and credentials:
                raise google.api_core.exceptions.DuplicateCredentialArgs(
                    "client_options.credentials_file and credentials are mutually exclusive."
                )
            if client_options.credentials_file:
                credentials = credentials_from_file(
                    client_options.credentials_file,
                    scopes=client_options.scopes,
                    quota_project_id=client_options.quota_project_id,
                )
            if credentials is None:
                credentials = default_credentials(
                    scopes=client_options.scopes,
                    quota_project_id=client_options.quota_project_id,
                )
            if not client_options.scopes:
                credentials = with_scopes(credentials, scopes)
        if (
            credentials
            and isinstance(credentials, service_account.Credentials)
            and always_use_jwt_access
            and hasattr(service_account.Credentials, "with_always_use_jwt_access")
        ):
            credentials = credentials.with_always_use_jwt_access(always_use_jwt_access)
            credentials._create_self_signed_jwt(audience_for_self_signed_jwt)
        if credentials:
            http = authorized_http(credentials)
        else:
            http = build_http()
        client_cert_to_use = None
        use_client_cert = os.getenv(GOOGLE_API_USE_CLIENT_CERTIFICATE, "false")
        if not use_client_cert in ("true", "false"):
            raise MutualTLSChannelError(
                "Unsupported GOOGLE_API_USE_CLIENT_CERTIFICATE value. Accepted values: true, false"
            )
        if client_options and client_options.client_cert_source:
            raise MutualTLSChannelError(
                "ClientOptions.client_cert_source is not supported, please use ClientOptions.client_encrypted_cert_source."
            )
        if use_client_cert == "true":
            if (
                client_options
                and hasattr(client_options, "client_encrypted_cert_source")
                and client_options.client_encrypted_cert_source
            ):
                client_cert_to_use = client_options.client_encrypted_cert_source
            elif (
                adc_cert_path and adc_key_path and mtls.has_default_client_cert_source()
            ):
                client_cert_to_use = mtls.default_client_encrypted_cert_source(
                    adc_cert_path, adc_key_path
                )
        if client_cert_to_use:
            cert_path, key_path, passphrase = client_cert_to_use()
            http_channel = (
                http.http
                if google_auth_httplib2
                and isinstance(http, google_auth_httplib2.AuthorizedHttp)
                else http
            )
            http_channel.add_certificate(key_path, cert_path, "", passphrase)
        if "mtlsRootUrl" in service and (
            not client_options or not client_options.api_endpoint
        ):
            mtls_endpoint = urllib.parse.urljoin(
                service["mtlsRootUrl"], service["servicePath"]
            )
            use_mtls_endpoint = os.getenv(GOOGLE_API_USE_MTLS_ENDPOINT, "auto")
            if not use_mtls_endpoint in ("never", "auto", "always"):
                raise MutualTLSChannelError(
                    "Unsupported GOOGLE_API_USE_MTLS_ENDPOINT value. Accepted values: never, auto, always"
                )
            if use_mtls_endpoint == "always" or (
                use_mtls_endpoint == "auto" and client_cert_to_use
            ):
                base = mtls_endpoint
    if model is None:
        features = service.get("features", [])
        model = JsonModel("dataWrapper" in features)
    return Resource(
        http=http,
        baseUrl=base,
        model=model,
        developerKey=developerKey,
        requestBuilder=requestBuilder,
        resourceDesc=service,
        rootDesc=service,
        schema=schema,
    )
def _cast(value, schema_type):
    if schema_type == "string":
        if type(value) == type("") or type(value) == type(""):
            return value
        else:
            return str(value)
    elif schema_type == "integer":
        return str(int(value))
    elif schema_type == "number":
        return str(float(value))
    elif schema_type == "boolean":
        return str(bool(value)).lower()
    else:
        if type(value) == type("") or type(value) == type(""):
            return value
        else:
            return str(value)
def _media_size_to_long(maxSize):
    if len(maxSize) < 2:
        return 0
    units = maxSize[-2:].upper()
    bit_shift = _MEDIA_SIZE_BIT_SHIFTS.get(units)
    if bit_shift is not None:
        return int(maxSize[:-2]) << bit_shift
    else:
        return int(maxSize)
def _media_path_url_from_info(root_desc, path_url):
    return "%(root)supload/%(service_path)s%(path)s" % {
        "root": root_desc["rootUrl"],
        "service_path": root_desc["servicePath"],
        "path": path_url,
    }
def _fix_up_parameters(method_desc, root_desc, http_method, schema):
    parameters = method_desc.setdefault("parameters", {})
    for name, description in root_desc.get("parameters", {}).items():
        parameters[name] = description
    for name in STACK_QUERY_PARAMETERS:
        parameters[name] = STACK_QUERY_PARAMETER_DEFAULT_VALUE.copy()
    if http_method in HTTP_PAYLOAD_METHODS and "request" in method_desc:
        body = BODY_PARAMETER_DEFAULT_VALUE.copy()
        body.update(method_desc["request"])
        parameters["body"] = body
    return parameters
def _fix_up_media_upload(method_desc, root_desc, path_url, parameters):
    media_upload = method_desc.get("mediaUpload", {})
    accept = media_upload.get("accept", [])
    max_size = _media_size_to_long(media_upload.get("maxSize", ""))
    media_path_url = None
    if media_upload:
        media_path_url = _media_path_url_from_info(root_desc, path_url)
        parameters["media_body"] = MEDIA_BODY_PARAMETER_DEFAULT_VALUE.copy()
        parameters["media_mime_type"] = MEDIA_MIME_TYPE_PARAMETER_DEFAULT_VALUE.copy()
    return accept, max_size, media_path_url
def _fix_up_method_description(method_desc, root_desc, schema):
    path_url = method_desc["path"]
    http_method = method_desc["httpMethod"]
    method_id = method_desc["id"]
    parameters = _fix_up_parameters(method_desc, root_desc, http_method, schema)
    accept, max_size, media_path_url = _fix_up_media_upload(
        method_desc, root_desc, path_url, parameters
    )
    return path_url, http_method, method_id, accept, max_size, media_path_url
def _fix_up_media_path_base_url(media_path_url, base_url):
    parsed_media_url = urllib.parse.urlparse(media_path_url)
    parsed_base_url = urllib.parse.urlparse(base_url)
    if parsed_media_url.netloc == parsed_base_url.netloc:
        return media_path_url
    return urllib.parse.urlunparse(
        parsed_media_url._replace(netloc=parsed_base_url.netloc)
    )
def _urljoin(base, url):
    if url.startswith("http://") or url.startswith("https://"):
        return urllib.parse.urljoin(base, url)
    new_base = base if base.endswith("/") else base + "/"
    new_url = url[1:] if url.startswith("/") else url
    return new_base + new_url
class ResourceMethodParameters(object):
    def __init__(self, method_desc):
        self.argmap = {}
        self.required_params = []
        self.repeated_params = []
        self.pattern_params = {}
        self.query_params = []
        self.path_params = set()
        self.param_types = {}
        self.enum_params = {}
        self.set_parameters(method_desc)
    def set_parameters(self, method_desc):
        parameters = method_desc.get("parameters", {})
        sorted_parameters = OrderedDict(sorted(parameters.items()))
        for arg, desc in sorted_parameters.items():
            param = key2param(arg)
            self.argmap[param] = arg
            if desc.get("pattern"):
                self.pattern_params[param] = desc["pattern"]
            if desc.get("enum"):
                self.enum_params[param] = desc["enum"]
            if desc.get("required"):
                self.required_params.append(param)
            if desc.get("repeated"):
                self.repeated_params.append(param)
            if desc.get("location") == "query":
                self.query_params.append(param)
            if desc.get("location") == "path":
                self.path_params.add(param)
            self.param_types[param] = desc.get("type", "string")
        for match in URITEMPLATE.finditer(method_desc["path"]):
            for namematch in VARNAME.finditer(match.group(0)):
                name = key2param(namematch.group(0))
                self.path_params.add(name)
                if name in self.query_params:
                    self.query_params.remove(name)
def createMethod(methodName, methodDesc, rootDesc, schema):
    methodName = fix_method_name(methodName)
    (
        pathUrl,
        httpMethod,
        methodId,
        accept,
        maxSize,
        mediaPathUrl,
    ) = _fix_up_method_description(methodDesc, rootDesc, schema)
    parameters = ResourceMethodParameters(methodDesc)
    def method(self, **kwargs):
        for name in kwargs:
            if name not in parameters.argmap:
                raise TypeError("Got an unexpected keyword argument {}".format(name))
        keys = list(kwargs.keys())
        for name in keys:
            if kwargs[name] is None:
                del kwargs[name]
        for name in parameters.required_params:
            if name not in kwargs:
                if name not in _PAGE_TOKEN_NAMES or _findPageTokenName(
                    _methodProperties(methodDesc, schema, "response")
                ):
                    raise TypeError('Missing required parameter "%s"' % name)
        for name, regex in parameters.pattern_params.items():
            if name in kwargs:
                if isinstance(kwargs[name], str):
                    pvalues = [kwargs[name]]
                else:
                    pvalues = kwargs[name]
                for pvalue in pvalues:
                    if re.match(regex, pvalue) is None:
                        raise TypeError(
                            'Parameter "%s" value "%s" does not match the pattern "%s"'
                            % (name, pvalue, regex)
                        )
        for name, enums in parameters.enum_params.items():
            if name in kwargs:
                if name in parameters.repeated_params and not isinstance(
                    kwargs[name], str
                ):
                    values = kwargs[name]
                else:
                    values = [kwargs[name]]
                for value in values:
                    if value not in enums:
                        raise TypeError(
                            'Parameter "%s" value "%s" is not an allowed value in "%s"'
                            % (name, value, str(enums))
                        )
        actual_query_params = {}
        actual_path_params = {}
        for key, value in kwargs.items():
            to_type = parameters.param_types.get(key, "string")
            if key in parameters.repeated_params and type(value) == type([]):
                cast_value = [_cast(x, to_type) for x in value]
            else:
                cast_value = _cast(value, to_type)
            if key in parameters.query_params:
                actual_query_params[parameters.argmap[key]] = cast_value
            if key in parameters.path_params:
                actual_path_params[parameters.argmap[key]] = cast_value
        body_value = kwargs.get("body", None)
        media_filename = kwargs.get("media_body", None)
        media_mime_type = kwargs.get("media_mime_type", None)
        if self._developerKey:
            actual_query_params["key"] = self._developerKey
        model = self._model
        if methodName.endswith("_media"):
            model = MediaModel()
        elif "response" not in methodDesc:
            model = RawModel()
        headers = {}
        headers, params, query, body = model.request(
            headers, actual_path_params, actual_query_params, body_value
        )
        expanded_url = uritemplate.expand(pathUrl, params)
        url = _urljoin(self._baseUrl, expanded_url + query)
        resumable = None
        multipart_boundary = ""
        if media_filename:
            if isinstance(media_filename, str):
                if media_mime_type is None:
                    logger.warning(
                        "media_mime_type argument not specified: trying to auto-detect for %s",
                        media_filename,
                    )
                    media_mime_type, _ = mimetypes.guess_type(media_filename)
                if media_mime_type is None:
                    raise UnknownFileType(media_filename)
                if not best_match([media_mime_type], ",".join(accept)):
                    raise UnacceptableMimeTypeError(media_mime_type)
                media_upload = MediaFileUpload(media_filename, mimetype=media_mime_type)
            elif isinstance(media_filename, MediaUpload):
                media_upload = media_filename
            else:
                raise TypeError("media_filename must be str or MediaUpload.")
            if media_upload.size() is not None and media_upload.size() > maxSize > 0:
                raise MediaUploadSizeError("Media larger than: %s" % maxSize)
            expanded_url = uritemplate.expand(mediaPathUrl, params)
            url = _urljoin(self._baseUrl, expanded_url + query)
            url = _fix_up_media_path_base_url(url, self._baseUrl)
            if media_upload.resumable():
                url = _add_query_parameter(url, "uploadType", "resumable")
            if media_upload.resumable():
                resumable = media_upload
            else:
                if body is None:
                    headers["content-type"] = media_upload.mimetype()
                    body = media_upload.getbytes(0, media_upload.size())
                    url = _add_query_parameter(url, "uploadType", "media")
                else:
                    msgRoot = MIMEMultipart("related")
                    setattr(msgRoot, "_write_headers", lambda self: None)
                    msg = MIMENonMultipart(*headers["content-type"].split("/"))
                    msg.set_payload(body)
                    msgRoot.attach(msg)
                    msg = MIMENonMultipart(*media_upload.mimetype().split("/"))
                    msg["Content-Transfer-Encoding"] = "binary"
                    payload = media_upload.getbytes(0, media_upload.size())
                    msg.set_payload(payload)
                    msgRoot.attach(msg)
                    fp = io.BytesIO()
                    g = _BytesGenerator(fp, mangle_from_=False)
                    g.flatten(msgRoot, unixfrom=False)
                    body = fp.getvalue()
                    multipart_boundary = msgRoot.get_boundary()
                    headers["content-type"] = (
                        "multipart/related; " 'boundary="%s"'
                    ) % multipart_boundary
                    url = _add_query_parameter(url, "uploadType", "multipart")
        logger.debug("URL being requested: %s %s" % (httpMethod, url))
        return self._requestBuilder(
            self._http,
            model.response,
            url,
            method=httpMethod,
            body=body,
            headers=headers,
            methodId=methodId,
            resumable=resumable,
        )
    docs = [methodDesc.get("description", DEFAULT_METHOD_DOC), "\n\n"]
    if len(parameters.argmap) > 0:
        docs.append("Args:\n")
    skip_parameters = list(rootDesc.get("parameters", {}).keys())
    skip_parameters.extend(STACK_QUERY_PARAMETERS)
    all_args = list(parameters.argmap.keys())
    args_ordered = [key2param(s) for s in methodDesc.get("parameterOrder", [])]
    if "body" in all_args:
        args_ordered.append("body")
    for name in sorted(all_args):
        if name not in args_ordered:
            args_ordered.append(name)
    for arg in args_ordered:
        if arg in skip_parameters:
            continue
        repeated = ""
        if arg in parameters.repeated_params:
            repeated = " (repeated)"
        required = ""
        if arg in parameters.required_params:
            required = " (required)"
        paramdesc = methodDesc["parameters"][parameters.argmap[arg]]
        paramdoc = paramdesc.get("description", "A parameter")
        if "$ref" in paramdesc:
            docs.append(
                ("  %s: object, %s%s%s\n    The object takes the form of:\n\n%s\n\n")
                % (
                    arg,
                    paramdoc,
                    required,
                    repeated,
                    schema.prettyPrintByName(paramdesc["$ref"]),
                )
            )
        else:
            paramtype = paramdesc.get("type", "string")
            docs.append(
                "  %s: %s, %s%s%s\n" % (arg, paramtype, paramdoc, required, repeated)
            )
        enum = paramdesc.get("enum", [])
        enumDesc = paramdesc.get("enumDescriptions", [])
        if enum and enumDesc:
            docs.append("    Allowed values\n")
            for (name, desc) in zip(enum, enumDesc):
                docs.append("      %s - %s\n" % (name, desc))
    if "response" in methodDesc:
        if methodName.endswith("_media"):
            docs.append("\nReturns:\n  The media object as a string.\n\n    ")
        else:
            docs.append("\nReturns:\n  An object of the form:\n\n    ")
            docs.append(schema.prettyPrintSchema(methodDesc["response"]))
    setattr(method, "__doc__", "".join(docs))
    return (methodName, method)
def createNextMethod(
    methodName,
    pageTokenName="pageToken",
    nextPageTokenName="nextPageToken",
    isPageTokenParameter=True,
):
    methodName = fix_method_name(methodName)
    def methodNext(self, previous_request, previous_response):
        nextPageToken = previous_response.get(nextPageTokenName, None)
        if not nextPageToken:
            return None
        request = copy.copy(previous_request)
        if isPageTokenParameter:
            request.uri = _add_query_parameter(
                request.uri, pageTokenName, nextPageToken
            )
            logger.debug("Next page request URL: %s %s" % (methodName, request.uri))
        else:
            model = self._model
            body = model.deserialize(request.body)
            body[pageTokenName] = nextPageToken
            request.body = model.serialize(body)
            request.body_size = len(request.body)
            if "content-length" in request.headers:
                del request.headers["content-length"]
            logger.debug("Next page request body: %s %s" % (methodName, body))
        return request
    return (methodName, methodNext)
class Resource(object):
    def __init__(
        self,
        http,
        baseUrl,
        model,
        requestBuilder,
        developerKey,
        resourceDesc,
        rootDesc,
        schema,
    ):
        self._dynamic_attrs = []
        self._http = http
        self._baseUrl = baseUrl
        self._model = model
        self._developerKey = developerKey
        self._requestBuilder = requestBuilder
        self._resourceDesc = resourceDesc
        self._rootDesc = rootDesc
        self._schema = schema
        self._set_service_methods()
    def _set_dynamic_attr(self, attr_name, value):
        self._dynamic_attrs.append(attr_name)
        self.__dict__[attr_name] = value
    def __getstate__(self):
        state_dict = copy.copy(self.__dict__)
        for dynamic_attr in self._dynamic_attrs:
            del state_dict[dynamic_attr]
        del state_dict["_dynamic_attrs"]
        return state_dict
    def __setstate__(self, state):
        self.__dict__.update(state)
        self._dynamic_attrs = []
        self._set_service_methods()
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, exc_tb):
        self.close()
    def close(self):
        self._http.close()
    def _set_service_methods(self):
        self._add_basic_methods(self._resourceDesc, self._rootDesc, self._schema)
        self._add_nested_resources(self._resourceDesc, self._rootDesc, self._schema)
        self._add_next_methods(self._resourceDesc, self._schema)
    def _add_basic_methods(self, resourceDesc, rootDesc, schema):
        if resourceDesc == rootDesc:
            batch_uri = "%s%s" % (
                rootDesc["rootUrl"],
                rootDesc.get("batchPath", "batch"),
            )
            def new_batch_http_request(callback=None):
                return BatchHttpRequest(callback=callback, batch_uri=batch_uri)
            self._set_dynamic_attr("new_batch_http_request", new_batch_http_request)
        if "methods" in resourceDesc:
            for methodName, methodDesc in resourceDesc["methods"].items():
                fixedMethodName, method = createMethod(
                    methodName, methodDesc, rootDesc, schema
                )
                self._set_dynamic_attr(
                    fixedMethodName, method.__get__(self, self.__class__)
                )
                if methodDesc.get("supportsMediaDownload", False):
                    fixedMethodName, method = createMethod(
                        methodName + "_media", methodDesc, rootDesc, schema
                    )
                    self._set_dynamic_attr(
                        fixedMethodName, method.__get__(self, self.__class__)
                    )
    def _add_nested_resources(self, resourceDesc, rootDesc, schema):
        if "resources" in resourceDesc:
            def createResourceMethod(methodName, methodDesc):
                methodName = fix_method_name(methodName)
                def methodResource(self):
                    return Resource(
                        http=self._http,
                        baseUrl=self._baseUrl,
                        model=self._model,
                        developerKey=self._developerKey,
                        requestBuilder=self._requestBuilder,
                        resourceDesc=methodDesc,
                        rootDesc=rootDesc,
                        schema=schema,
                    )
                setattr(methodResource, "__doc__", "A collection resource.")
                setattr(methodResource, "__is_resource__", True)
                return (methodName, methodResource)
            for methodName, methodDesc in resourceDesc["resources"].items():
                fixedMethodName, method = createResourceMethod(methodName, methodDesc)
                self._set_dynamic_attr(
                    fixedMethodName, method.__get__(self, self.__class__)
                )
    def _add_next_methods(self, resourceDesc, schema):
        if "methods" not in resourceDesc:
            return
        for methodName, methodDesc in resourceDesc["methods"].items():
            nextPageTokenName = _findPageTokenName(
                _methodProperties(methodDesc, schema, "response")
            )
            if not nextPageTokenName:
                continue
            isPageTokenParameter = True
            pageTokenName = _findPageTokenName(methodDesc.get("parameters", {}))
            if not pageTokenName:
                isPageTokenParameter = False
                pageTokenName = _findPageTokenName(
                    _methodProperties(methodDesc, schema, "request")
                )
            if not pageTokenName:
                continue
            fixedMethodName, method = createNextMethod(
                methodName + "_next",
                pageTokenName,
                nextPageTokenName,
                isPageTokenParameter,
            )
            self._set_dynamic_attr(
                fixedMethodName, method.__get__(self, self.__class__)
            )
def _findPageTokenName(fields):
    return next(
        (tokenName for tokenName in _PAGE_TOKEN_NAMES if tokenName in fields), None
    )
def _methodProperties(methodDesc, schema, name):
    desc = methodDesc.get(name, {})
    if "$ref" in desc:
        desc = schema.get(desc["$ref"], {})
    return desc.get("properties", {})

class Schemas(object):
    def __init__(self, discovery):
        self.schemas = discovery.get("schemas", {})
        self.pretty = {}
    @positional(2)
    def _prettyPrintByName(self, name, seen=None, dent=0):
        if seen is None:
            seen = []
        if name in seen:
            return "# Object with schema name: %s" % name
        seen.append(name)
        if name not in self.pretty:
            self.pretty[name] = _SchemaToStruct(
                self.schemas[name], seen, dent=dent
            ).to_str(self._prettyPrintByName)
        seen.pop()
        return self.pretty[name]
    def prettyPrintByName(self, name):
        return self._prettyPrintByName(name, seen=[], dent=0)[:-2]
    @positional(2)
    def _prettyPrintSchema(self, schema, seen=None, dent=0):
        if seen is None:
            seen = []
        return _SchemaToStruct(schema, seen, dent=dent).to_str(self._prettyPrintByName)
    def prettyPrintSchema(self, schema):
        return self._prettyPrintSchema(schema, dent=0)[:-2]
    def get(self, name, default=None):
        return self.schemas.get(name, default)
class _SchemaToStruct(object):
    @positional(3)
    def __init__(self, schema, seen, dent=0):
        self.value = []
        self.string = None
        self.schema = schema
        self.dent = dent
        self.from_cache = None
        self.seen = seen
    def emit(self, text):
        self.value.extend(["  " * self.dent, text, "\n"])
    def emitBegin(self, text):
        self.value.extend(["  " * self.dent, text])
    def emitEnd(self, text, comment):
        if comment:
            divider = "\n" + "  " * (self.dent + 2) + "# "
            lines = comment.splitlines()
            lines = [x.rstrip() for x in lines]
            comment = divider.join(lines)
            self.value.extend([text, " # ", comment, "\n"])
        else:
            self.value.extend([text, "\n"])
    def indent(self):
        self.dent += 1
    def undent(self):
        self.dent -= 1
    def _to_str_impl(self, schema):
        stype = schema.get("type")
        if stype == "object":
            self.emitEnd("{", schema.get("description", ""))
            self.indent()
            if "properties" in schema:
                properties = schema.get("properties", {})
                sorted_properties = OrderedDict(sorted(properties.items()))
                for pname, pschema in sorted_properties.items():
                    self.emitBegin('"%s": ' % pname)
                    self._to_str_impl(pschema)
            elif "additionalProperties" in schema:
                self.emitBegin('"a_key": ')
                self._to_str_impl(schema["additionalProperties"])
            self.undent()
            self.emit("},")
        elif "$ref" in schema:
            schemaName = schema["$ref"]
            description = schema.get("description", "")
            s = self.from_cache(schemaName, seen=self.seen)
            parts = s.splitlines()
            self.emitEnd(parts[0], description)
            for line in parts[1:]:
                self.emit(line.rstrip())
        elif stype == "boolean":
            value = schema.get("default", "True or False")
            self.emitEnd("%s," % str(value), schema.get("description", ""))
        elif stype == "string":
            value = schema.get("default", "A String")
            self.emitEnd('"%s",' % str(value), schema.get("description", ""))
        elif stype == "integer":
            value = schema.get("default", "42")
            self.emitEnd("%s," % str(value), schema.get("description", ""))
        elif stype == "number":
            value = schema.get("default", "3.14")
            self.emitEnd("%s," % str(value), schema.get("description", ""))
        elif stype == "null":
            self.emitEnd("None,", schema.get("description", ""))
        elif stype == "any":
            self.emitEnd('"",', schema.get("description", ""))
        elif stype == "array":
            self.emitEnd("[", schema.get("description"))
            self.indent()
            self.emitBegin("")
            self._to_str_impl(schema["items"])
            self.undent()
            self.emit("],")
        else:
            self.emit("Unknown type! %s" % stype)
            self.emitEnd("", "")
        self.string = "".join(self.value)
        return self.string
    def to_str(self, from_cache):
        self.from_cache = from_cache
        return self._to_str_impl(self.schema)

_LIBRARY_VERSION = "2.93.0"
_PY_VERSION = platform.python_version()
LOGGER = logging.getLogger(__name__)
dump_request_response = False
def _abstract():
    raise NotImplementedError("You need to override this function")
class Model(object):
    def request(self, headers, path_params, query_params, body_value):
        _abstract()
    def response(self, resp, content):
        _abstract()
class BaseModel(Model):
    accept = None
    content_type = None
    no_content_response = None
    alt_param = None
    def _log_request(self, headers, path_params, query, body):
        if dump_request_response:
            LOGGER.info("--request-start--")
            LOGGER.info("-headers-start-")
            for h, v in headers.items():
                LOGGER.info("%s: %s", h, v)
            LOGGER.info("-headers-end-")
            LOGGER.info("-path-parameters-start-")
            for h, v in path_params.items():
                LOGGER.info("%s: %s", h, v)
            LOGGER.info("-path-parameters-end-")
            LOGGER.info("body: %s", body)
            LOGGER.info("query: %s", query)
            LOGGER.info("--request-end--")
    def request(self, headers, path_params, query_params, body_value):
        query = self._build_query(query_params)
        headers["accept"] = self.accept
        headers["accept-encoding"] = "gzip, deflate"
        if "user-agent" in headers:
            headers["user-agent"] += " "
        else:
            headers["user-agent"] = ""
        headers["user-agent"] += "(gzip)"
        if "x-goog-api-client" in headers:
            headers["x-goog-api-client"] += " "
        else:
            headers["x-goog-api-client"] = ""
        headers["x-goog-api-client"] += "gdcl/%s gl-python/%s" % (
            _LIBRARY_VERSION,
            _PY_VERSION,
        )
        if body_value is not None:
            headers["content-type"] = self.content_type
            body_value = self.serialize(body_value)
        self._log_request(headers, path_params, query, body_value)
        return (headers, path_params, query, body_value)
    def _build_query(self, params):
        if self.alt_param is not None:
            params.update({"alt": self.alt_param})
        astuples = []
        for key, value in params.items():
            if type(value) == type([]):
                for x in value:
                    x = x.encode("utf-8")
                    astuples.append((key, x))
            else:
                if isinstance(value, str) and callable(value.encode):
                    value = value.encode("utf-8")
                astuples.append((key, value))
        return "?" + urllib.parse.urlencode(astuples)
    def _log_response(self, resp, content):
        if dump_request_response:
            LOGGER.info("--response-start--")
            for h, v in resp.items():
                LOGGER.info("%s: %s", h, v)
            if content:
                LOGGER.info(content)
            LOGGER.info("--response-end--")
    def response(self, resp, content):
        self._log_response(resp, content)
        if resp.status < 300:
            if resp.status == 204:
                return self.no_content_response
            return self.deserialize(content)
        else:
            LOGGER.debug("Content from bad request was: %r" % content)
            raise HttpError(resp, content)
    def serialize(self, body_value):
        _abstract()
    def deserialize(self, content):
        _abstract()
class JsonModel(BaseModel):
    accept = "application/json"
    content_type = "application/json"
    alt_param = "json"
    def __init__(self, data_wrapper=False):
        self._data_wrapper = data_wrapper
    def serialize(self, body_value):
        if (
            isinstance(body_value, dict)
            and "data" not in body_value
            and self._data_wrapper
        ):
            body_value = {"data": body_value}
        return json.dumps(body_value)
    def deserialize(self, content):
        try:
            content = content.decode("utf-8")
        except AttributeError:
            pass
        try:
            body = json.loads(content)
        except json.decoder.JSONDecodeError:
            body = content
        else:
            if self._data_wrapper and "data" in body:
                body = body["data"]
        return body
    @property
    def no_content_response(self):
        return {}
class RawModel(JsonModel):
    accept = "*/*"
    content_type = "application/json"
    alt_param = None
    def deserialize(self, content):
        return content
    @property
    def no_content_response(self):
        return ""
class MediaModel(JsonModel):
    accept = "*/*"
    content_type = "application/json"
    alt_param = "media"
    def deserialize(self, content):
        return content
    @property
    def no_content_response(self):
        return ""
class ProtocolBufferModel(BaseModel):
    accept = "application/x-protobuf"
    content_type = "application/x-protobuf"
    alt_param = "proto"
    def __init__(self, protocol_buffer):
        self._protocol_buffer = protocol_buffer
    def serialize(self, body_value):
        return body_value.SerializeToString()
    def deserialize(self, content):
        return self._protocol_buffer.FromString(content)
    @property
    def no_content_response(self):
        return self._protocol_buffer()
def makepatch(original, modified):
    patch = {}
    for key, original_value in original.items():
        modified_value = modified.get(key, None)
        if modified_value is None:
            patch[key] = None
        elif original_value != modified_value:
            if type(original_value) == type({}):
                patch[key] = makepatch(original_value, modified_value)
            else:
                patch[key] = modified_value
        else:
            pass
    for key in modified:
        if key not in original:
            patch[key] = modified[key]
    return patch

class Error(Exception):
    pass
class HttpError(Error):
    @positional(3)
    def __init__(self, resp, content, uri=None):
        self.resp = resp
        if not isinstance(content, bytes):
            raise TypeError("HTTP content should be bytes")
        self.content = content
        self.uri = uri
        self.error_details = ""
        self.reason = self._get_reason()
    @property
    def status_code(self):
        return self.resp.status
    def _get_reason(self):
        reason = self.resp.reason
        try:
            try:
                data = json.loads(self.content.decode("utf-8"))
            except json.JSONDecodeError:
                data = self.content.decode("utf-8")
            if isinstance(data, dict):
                reason = data["error"]["message"]
                error_detail_keyword = next(
                    (
                        kw
                        for kw in ["detail", "details", "errors", "message"]
                        if kw in data["error"]
                    ),
                    "",
                )
                if error_detail_keyword:
                    self.error_details = data["error"][error_detail_keyword]
            elif isinstance(data, list) and len(data) > 0:
                first_error = data[0]
                reason = first_error["error"]["message"]
                if "details" in first_error["error"]:
                    self.error_details = first_error["error"]["details"]
            else:
                self.error_details = data
        except (ValueError, KeyError, TypeError):
            pass
        if reason is None:
            reason = ""
        return reason.strip()
    def __repr__(self):
        if self.error_details:
            return '<HttpError %s when requesting %s returned "%s". Details: "%s">' % (
                self.resp.status,
                self.uri,
                self.reason,
                self.error_details,
            )
        elif self.uri:
            return '<HttpError %s when requesting %s returned "%s">' % (
                self.resp.status,
                self.uri,
                self.reason,
            )
        else:
            return '<HttpError %s "%s">' % (self.resp.status, self.reason)
    __str__ = __repr__
class InvalidJsonError(Error):
    pass
class UnknownFileType(Error):
    pass
class UnknownLinkType(Error):
    pass
class UnknownApiNameOrVersion(Error):
    pass
class UnacceptableMimeTypeError(Error):
    pass
class MediaUploadSizeError(Error):
    pass
class ResumableUploadError(HttpError):
    pass
class InvalidChunkSizeError(Error):
    pass
class InvalidNotificationError(Error):
    pass
class BatchError(HttpError):
    @positional(2)
    def __init__(self, reason, resp=None, content=None):
        self.resp = resp
        self.content = content
        self.reason = reason
    def __repr__(self):
        if getattr(self.resp, "status", None) is None:
            return '<BatchError "%s">' % (self.reason)
        else:
            return '<BatchError %s "%s">' % (self.resp.status, self.reason)
    __str__ = __repr__
class UnexpectedMethodError(Error):
    @positional(1)
    def __init__(self, methodId=None):
        super(UnexpectedMethodError, self).__init__(
            "Received unexpected call %s" % methodId
        )
class UnexpectedBodyError(Error):
    def __init__(self, expected, provided):
        super(UnexpectedBodyError, self).__init__(
            "Expected: [%s] - Provided: [%s]" % (expected, provided)
        )

try:
    import google.auth
    import google.auth.credentials
    HAS_GOOGLE_AUTH = True
except ImportError:  
    HAS_GOOGLE_AUTH = False

try:
    import oauth2client
    import oauth2client.client
    HAS_OAUTH2CLIENT = True
except ImportError:  
    HAS_OAUTH2CLIENT = False
def credentials_from_file(filename, scopes=None, quota_project_id=None):
    if HAS_GOOGLE_AUTH:
        credentials, _ = google.auth.load_credentials_from_file(
            filename, scopes=scopes, quota_project_id=quota_project_id
        )
        return credentials
    else:
        raise EnvironmentError(
            "client_options.credentials_file is only supported in google-auth."
        )
def default_credentials(scopes=None, quota_project_id=None):
    if HAS_GOOGLE_AUTH:
        credentials, _ = google.auth.default(
            scopes=scopes, quota_project_id=quota_project_id
        )
        return credentials
    elif HAS_OAUTH2CLIENT:
        if scopes is not None or quota_project_id is not None:
            raise EnvironmentError(
                "client_options.scopes and client_options.quota_project_id are not supported in oauth2client."
                "Please install google-auth."
            )
        return oauth2client.client.GoogleCredentials.get_application_default()
    else:
        raise EnvironmentError(
            "No authentication library is available. Please install either "
            "google-auth or oauth2client."
        )
def with_scopes(credentials, scopes):
    if HAS_GOOGLE_AUTH and isinstance(credentials, google.auth.credentials.Credentials):
        return google.auth.credentials.with_scopes_if_required(credentials, scopes)
    else:
        try:
            if credentials.create_scoped_required():
                return credentials.create_scoped(scopes)
            else:
                return credentials
        except AttributeError:
            return credentials
def authorized_http(credentials):
    if HAS_GOOGLE_AUTH and isinstance(credentials, google.auth.credentials.Credentials):
        if google_auth_httplib2 is None:
            raise ValueError(
                "Credentials from google.auth specified, but "
                "google-api-python-client is unable to use these credentials "
                "unless google-auth-httplib2 is installed. Please install "
                "google-auth-httplib2."
            )
        return google_auth_httplib2.AuthorizedHttp(credentials, http=build_http())
    else:
        return credentials.authorize(build_http())
def refresh_credentials(credentials):
    refresh_http = httplib2.Http()
    if HAS_GOOGLE_AUTH and isinstance(credentials, google.auth.credentials.Credentials):
        request = google_auth_httplib2.Request(refresh_http)
        return credentials.refresh(request)
    else:
        return credentials.refresh(refresh_http)
def apply_credentials(credentials, headers):
    if not is_valid(credentials):
        refresh_credentials(credentials)
    return credentials.apply(headers)
def is_valid(credentials):
    if HAS_GOOGLE_AUTH and isinstance(credentials, google.auth.credentials.Credentials):
        return credentials.valid
    else:
        return (
            credentials.access_token is not None
            and not credentials.access_token_expired
        )
def get_credentials_from_http(http):
    if http is None:
        return None
    elif hasattr(http.request, "credentials"):
        return http.request.credentials
    elif hasattr(http, "credentials") and not isinstance(
        http.credentials, httplib2.Credentials
    ):
        return http.credentials
    else:
        return None

def parse_mime_type(mime_type):
    parts = mime_type.split(";")
    params = dict(
        [tuple([s.strip() for s in param.split("=", 1)]) for param in parts[1:]]
    )
    full_type = parts[0].strip()
    if full_type == "*":
        full_type = "*/*"
    (type, subtype) = full_type.split("/")
    return (type.strip(), subtype.strip(), params)
def parse_media_range(range):
    (type, subtype, params) = parse_mime_type(range)
    if (
        "q" not in params
        or not params["q"]
        or not float(params["q"])
        or float(params["q"]) > 1
        or float(params["q"]) < 0
    ):
        params["q"] = "1"
    return (type, subtype, params)
def fitness_and_quality_parsed(mime_type, parsed_ranges):
    best_fitness = -1
    best_fit_q = 0
    (target_type, target_subtype, target_params) = parse_media_range(mime_type)
    for (type, subtype, params) in parsed_ranges:
        type_match = type == target_type or type == "*" or target_type == "*"
        subtype_match = (
            subtype == target_subtype or subtype == "*" or target_subtype == "*"
        )
        if type_match and subtype_match:
            param_matches = reduce(
                lambda x, y: x + y,
                [
                    1
                    for (key, value) in target_params.items()
                    if key != "q" and key in params and value == params[key]
                ],
                0,
            )
            fitness = (type == target_type) and 100 or 0
            fitness += (subtype == target_subtype) and 10 or 0
            fitness += param_matches
            if fitness > best_fitness:
                best_fitness = fitness
                best_fit_q = params["q"]
    return best_fitness, float(best_fit_q)
def quality_parsed(mime_type, parsed_ranges):
    return fitness_and_quality_parsed(mime_type, parsed_ranges)[1]
def quality(mime_type, ranges):
    parsed_ranges = [parse_media_range(r) for r in ranges.split(",")]
    return quality_parsed(mime_type, parsed_ranges)
def best_match(supported, header):
    split_header = _filter_blank(header.split(","))
    parsed_header = [parse_media_range(r) for r in split_header]
    weighted_matches = []
    pos = 0
    for mime_type in supported:
        weighted_matches.append(
            (fitness_and_quality_parsed(mime_type, parsed_header), pos, mime_type)
        )
        pos += 1
    weighted_matches.sort()
    return weighted_matches[-1][0][1] and weighted_matches[-1][2] or ""
def _filter_blank(i):
    for s in i:
        if s.strip():
            yield s