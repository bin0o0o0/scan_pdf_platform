from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from flask import Blueprint, send_file, request

from ..auth.decorators import current_user_required
from ..core.errors import ApiError
from ..scanner.service import build_pdf_from_uploads

scan_bp = Blueprint("scan", __name__)


@scan_bp.post("/scan")
@current_user_required
def scan_files():
    files = request.files.getlist("files[]")
    if not files:
        raise ApiError("至少需要上传一张图片。", 400)

    with TemporaryDirectory(prefix="scan-pdf-") as temp_dir:
        upload_dir = Path(temp_dir)
        pdf_stream = build_pdf_from_uploads(files, upload_dir)

    pdf_stream.seek(0)
    return send_file(
        BytesIO(pdf_stream.read()),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="scanned-document.pdf",
    )

