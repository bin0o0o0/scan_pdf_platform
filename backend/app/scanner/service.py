from pathlib import Path
from werkzeug.datastructures import FileStorage
from PIL import Image

from ..core.errors import ApiError
from .pipeline import images_to_pdf, scan_image


ALLOWED_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}


def build_pdf_from_uploads(files: list[FileStorage], upload_dir: Path):
    """这里单独抽成 service，是为了把 HTTP 层和图像处理层解耦。
    这样以后无论接口来自 Flask、CLI 还是异步任务，都可以复用这一段核心流程。
    """

    scanned_images = []

    for index, storage in enumerate(files, start=1):
        suffix = Path(storage.filename or "").suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            raise ApiError(f"第 {index} 个文件格式不受支持。", 400)

        target_path = upload_dir / f"{index:02d}{suffix}"
        storage.save(target_path)

        try:
            with Image.open(target_path) as image:
                scanned_images.append(scan_image(image))
        except Exception as error:
            raise ApiError(f"第 {index} 个文件处理失败：{error}") from error

    return images_to_pdf(scanned_images)

