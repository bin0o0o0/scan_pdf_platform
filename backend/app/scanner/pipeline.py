from __future__ import annotations

from io import BytesIO

import cv2
import numpy as np
from PIL import Image


def order_points(points: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype="float32")
    sums = points.sum(axis=1)
    rect[0] = points[np.argmin(sums)]
    rect[2] = points[np.argmax(sums)]

    diffs = np.diff(points, axis=1)
    rect[1] = points[np.argmin(diffs)]
    rect[3] = points[np.argmax(diffs)]
    return rect


def four_point_transform(image: np.ndarray, points: np.ndarray) -> np.ndarray:
    rect = order_points(points)
    (top_left, top_right, bottom_right, bottom_left) = rect

    width_a = np.linalg.norm(bottom_right - bottom_left)
    width_b = np.linalg.norm(top_right - top_left)
    max_width = max(int(width_a), int(width_b))

    height_a = np.linalg.norm(top_right - bottom_right)
    height_b = np.linalg.norm(top_left - bottom_left)
    max_height = max(int(height_a), int(height_b))

    destination = np.array(
        [
            [0, 0],
            [max_width - 1, 0],
            [max_width - 1, max_height - 1],
            [0, max_height - 1],
        ],
        dtype="float32",
    )

    matrix = cv2.getPerspectiveTransform(rect, destination)
    return cv2.warpPerspective(image, matrix, (max_width, max_height))


def scan_image(pil_image: Image.Image) -> Image.Image:
    """这里借鉴文档扫描常见流程：
    先找近似纸张轮廓，再做透视矫正，最后转成更适合打印/阅读的高对比图。
    """

    image = cv2.cvtColor(np.array(pil_image.convert("RGB")), cv2.COLOR_RGB2BGR)
    grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(grayscale, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 200)

    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

    document_contour = None
    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        approximation = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        if len(approximation) == 4:
            document_contour = approximation.reshape(4, 2)
            break

    if document_contour is None:
        # 找不到四边形时不强行报错，而是返回原图增强版，让用户至少拿到 PDF 结果。
        processed = cv2.adaptiveThreshold(
            grayscale,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2,
        )
        return Image.fromarray(processed).convert("RGB")

    warped = four_point_transform(image, document_contour.astype("float32"))
    warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    cleaned = cv2.adaptiveThreshold(
        warped_gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2,
    )
    return Image.fromarray(cleaned).convert("RGB")


def images_to_pdf(images: list[Image.Image]) -> BytesIO:
    if not images:
        raise ValueError("images must not be empty")

    output = BytesIO()
    first_page, *other_pages = [image.convert("RGB") for image in images]
    first_page.save(output, format="PDF", save_all=True, append_images=other_pages)
    output.seek(0)
    return output

