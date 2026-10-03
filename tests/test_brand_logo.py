import base64
import hashlib

from aegislog.brand_logo import report_logo_uri
from aegislog.reporting import _summary_brand


def test_report_logo_preserves_approved_image_and_embeds_offline():
    uri = report_logo_uri()
    assert uri.startswith('data:image/png;base64,')
    image = base64.b64decode(uri.partition(',')[2], validate=True)
    assert image.startswith(b'\x89PNG\r\n\x1a\n')
    assert hashlib.sha256(image).hexdigest() == '35c2e526661e8823d59e97b3645ed608d0d45d0229675a446d35878039643ec8'
    assert image[25] == 6  # PNG RGBA: retain the transparent background.
    html = _summary_brand()
    assert uri in html
    assert 'alt="AegisLog terminal mark logo"' in html
    assert '@media print' in html
    assert 'width:110px' in html
