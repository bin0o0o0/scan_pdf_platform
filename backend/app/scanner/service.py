from pathlib import Path

from flask import current_app
from PIL import Image
from werkzeug.datastructures import FileStorage

from ..core.errors import ApiError
from .pipeline import images_to_pdf, scan_image


ALLOWED_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}


def build_pdf_from_uploads(files: list[FileStorage], upload_dir: Path):
    """把上传文件转换成扫描后的多页 PDF。

    这里单独抽成 service，是为了把 HTTP 层和图像处理层解耦。
    以后无论入口来自 Flask、CLI 还是异步任务，都可以复用这段核心流程。
    """

    scanned_images = []

    for index, storage in enumerate(files, start=1):
        suffix = Path(storage.filename or "").suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            raise ApiError(f"第 {index} 个文件格式不受支持。", 400)

        target_path = upload_dir / f"{index:02d}{suffix}"
        storage.save(target_path)

        try:
            # Pillow 负责读取图片，真正的“扫描矫正”则交给 pipeline 里的算法函数。
            with Image.open(target_path) as image:
                scanned_images.append(scan_image(image))
        except Exception as error:
            current_app.logger.warning("scan_file_failed", exc_info=error)
            raise ApiError(f"第 {index} 个文件处理失败，请确认图片内容完整且格式正确。") from error

    return images_to_pdf(scanned_images)
