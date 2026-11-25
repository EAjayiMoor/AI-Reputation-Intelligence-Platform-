from io import BytesIO
import asyncio
import gzip
from zipfile import ZipFile

import pytest
from streamlit.web.server.starlette.starlette_gzip_middleware import MediaAwareGZipMiddleware


@pytest.mark.parametrize('encoding', ['gzip', 'identity'])
@pytest.mark.parametrize('status', [200, 206])
def test_zip_download_sends_headers_before_body(encoding, status):
    archive = BytesIO()
    with ZipFile(archive, 'w') as z:
        z.writestr('microsite/index.html', '<html>British Airways</html>' * 200)
    content = archive.getvalue()
    messages = []
    async def endpoint(scope, receive, send):
        await send({'type': 'http.response.start', 'status': status, 'headers': [
            (b'content-type', b'application/zip'),
            (b'content-disposition', b'attachment; filename="report.zip"'),
            (b'content-length', str(len(content)).encode())]})
        await send({'type': 'http.response.body', 'body': content})
    async def send(message):
        messages.append(message)
    async def receive():
        return {'type':'http.disconnect'}
    asyncio.run(MediaAwareGZipMiddleware(endpoint)({'type':'http', 'path':'/media/report.zip',
        'headers':[(b'accept-encoding',encoding.encode())]},receive,send))
    assert messages[0]['type'] == 'http.response.start'
    assert messages[0]['status'] == status
    headers = dict(messages[0]['headers'])
    assert headers[b'content-disposition'] == b'attachment; filename="report.zip"'
    body = b''.join(m.get('body', b'') for m in messages[1:])
    if headers.get(b'content-encoding') == b'gzip':
        body = gzip.decompress(body)
    assert body == content
    with ZipFile(BytesIO(body)) as z:
        assert z.testzip() is None
        assert 'British Airways' in z.read('microsite/index.html').decode()
