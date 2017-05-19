# coding: utf-8
# Copied from weasyprint/urls.py

import email
import gzip
import io
import mimetypes
import os.path
import re
import zlib
from base64 import decodebytes as base64_decode
from gzip import GzipFile
from urllib.parse import quote, unquote, unquote_to_bytes, urljoin, urlsplit
from urllib.request import Request, pathname2url, urlopen


class StreamingGzipFile(GzipFile):
    def __init__(self, fileobj):
        GzipFile.__init__(self, fileobj=fileobj)
        self.fileobj_to_close = fileobj

    def close(self):
        GzipFile.close(self)
        self.fileobj_to_close.close()

    # Inform html5lib to not rely on these:
    seek = tell = None


# Unlinke HTML, CSS and PNG, the SVG MIME type is not always builtin
# in some Python version and therefore not reliable.
mimetypes.add_type('image/svg+xml', '.svg')


# See http://stackoverflow.com/a/11687993/1162888
# Both are needed in Python 3 as the re module does not like to mix
# http://tools.ietf.org/html/rfc3986#section-3.1
UNICODE_SCHEME_RE = re.compile('^([a-zA-Z][a-zA-Z0-9.+-]+):')
BYTES_SCHEME_RE = re.compile(b'^([a-zA-Z][a-zA-Z0-9.+-]+):')

TIMEOUT = 3


def iri_to_uri(url):
    """Turn an IRI that can contain any Unicode character into an ASCII-only
    URI that conforms to RFC 3986.
    """
    if url.startswith('data:'):
        # Data URIs can be huge, but don’t need this anyway.
        return url
    # Use UTF-8 as per RFC 3987 (IRI), except for file://
    url = url.encode('utf-8')
    # This is a full URI, not just a component. Only %-encode characters
    # that are not allowed at all in URIs. Everthing else is "safe":
    # * Reserved characters: /:?#[]@!$&'()*+,;=
    # * Unreserved characters: ASCII letters, digits and -._~
    #   Of these, only '~' is not in urllib’s "always safe" list.
    # * '%' to avoid double-encoding
    return quote(url, safe=b"/:?#[]@!$&'()*+,;=~%")


def path2url(path):
    """Return file URL of `path`"""
    path = os.path.abspath(path)
    if os.path.isdir(path):
        # Make sure directory names have a trailing slash.
        # Otherwise relative URIs are resolved from the parent directory.
        path += os.path.sep
    path = pathname2url(path)
    if path.startswith('///'):
        # On Windows pathname2url(r'C:\foo') is apparently '///C:/foo'
        # That enough slashes already.
        return 'file:' + path
    else:
        return 'file://' + path


def url_is_absolute(url):
    return bool(
        (UNICODE_SCHEME_RE if isinstance(url, str) else BYTES_SCHEME_RE)
        .match(url))


def element_base_url(element):
    """Return the URL associated with a lxml document.

    This is the same as the HtmlElement.base_url property, but dont’t want
    to require HtmlElement.

    """
    return element.getroottree().docinfo.URL


def get_url_attribute(element, attr_name, allow_relative=False):
    """Get the URI corresponding to the ``attr_name`` attribute.

    Return ``None`` if:

    * the attribute is empty or missing or,
    * the value is a relative URI but the document has no base URI and
      ``allow_relative`` is ``False``.

    Otherwise return an URI, absolute if possible.

    """
    value = element.get(attr_name, '').strip()
    if value:
        return url_join(
            element_base_url(element), value, allow_relative,
            '<%s %s="%s"> at line %s',
            (element.tag, attr_name, value, element.sourceline))


def url_join(base_url, url, allow_relative, context, context_args):
    """Like urllib.urljoin, but warn if base_url is required but missing."""
    if url_is_absolute(url):
        return iri_to_uri(url)
    elif base_url:
        return iri_to_uri(urljoin(base_url, url))
    elif allow_relative:
        return iri_to_uri(url)
    else:
        return None


def get_link_attribute(element, attr_name):
    """Return ('external', absolute_uri) or
    ('internal', unquoted_fragment_id) or None.

    """
    attr_value = element.get(attr_name, '').strip()
    if attr_value.startswith('#') and len(attr_value) > 1:
        # Do not require a base_url when the value is just a fragment.
        return 'internal', unquote(attr_value[1:])
    uri = get_url_attribute(element, attr_name, allow_relative=True)
    if uri:
        document_url = element_base_url(element)
        if document_url:
            parsed = urlsplit(uri)
            # Compare with fragments removed
            if parsed[:-1] == urlsplit(document_url)[:-1]:
                return 'internal', unquote(parsed.fragment)
        return 'external', uri


def ensure_url(string):
    """Get a ``scheme://path`` URL from ``string``.

    If ``string`` looks like an URL, return it unchanged. Otherwise assume a
    filename and convert it to a ``file://`` URL.

    """
    return string if url_is_absolute(string) else path2url(string)


def safe_base64_decode(data):
    """Decode base64, padding being optional.

    "From a theoretical point of view, the padding character is not needed,
     since the number of missing bytes can be calculated from the number
     of Base64 digits."

    https://en.wikipedia.org/wiki/Base64#Padding

    :param data: Base64 data as an ASCII byte string
    :returns: The decoded byte string.

    """
    missing_padding = 4 - len(data) % 4
    if missing_padding:
        data += b'=' * missing_padding
    return base64_decode(data)


def open_data_url(url):
    """Decode URLs with the 'data' scheme. urllib can handle them
    in Python 2, but that is broken in Python 3.

    Inspired from Python 2.7.2’s urllib.py.

    """
    # syntax of data URLs:
    # dataurl   := "data:" [ mediatype ] [ ";base64" ] "," data
    # mediatype := [ type "/" subtype ] *( ";" parameter )
    # data      := *urlchar
    # parameter := attribute "=" value
    try:
        header, data = url.split(',', 1)
    except ValueError:
        raise IOError('bad data URL')
    header = header[5:]  # len('data:') == 5
    if header:
        semi = header.rfind(';')
        if semi >= 0 and '=' not in header[semi:]:
            content_type = header[:semi]
            encoding = header[semi + 1:]
        else:
            content_type = header
            encoding = ''

        message = email.message_from_string('Content-type: ' + content_type)
        mime_type = message.get_content_type()
        charset = message.get_content_charset()
    else:
        mime_type = 'text/plain'
        charset = 'US-ASCII'
        encoding = ''

    data = unquote_to_bytes(data)
    if encoding == 'base64':
        data = safe_base64_decode(data)

    return dict(string=data, mime_type=mime_type, encoding=charset,
                redirected_url=url)


HTTP_HEADERS = {
    'User-Agent': 'P.O.D.',
    'Accept-Encoding': 'gzip, deflate',
}


def fetcher(url):
    if url.lower().startswith('data:'):
        return open_data_url(url)
    elif UNICODE_SCHEME_RE.match(url):
        url = iri_to_uri(url)
        response = urlopen(Request(url, headers=HTTP_HEADERS), timeout=TIMEOUT)
        result = dict(redirected_url=response.geturl(),
                      mime_type=response.info().get_content_type(),
                      encoding=response.info().getparam('charset'),
                      filename=response.info().get_filename())
        content_encoding = response.info().get('Content-Encoding')
        if content_encoding == 'gzip':
            if StreamingGzipFile is None:
                result['string'] = gzip.GzipFile(
                    fileobj=io.BytesIO(response.read())).read()
                response.close()
            else:
                result['file_obj'] = StreamingGzipFile(fileobj=response)
        elif content_encoding == 'deflate':
            data = response.read()
            try:
                result['string'] = zlib.decompress(data)
            except zlib.error:
                # Try without zlib header or checksum
                result['string'] = zlib.decompress(data, -15)
        else:
            result['file_obj'] = response
        return result
    else:
        raise ValueError('Not an absolute URI: %r' % url)
