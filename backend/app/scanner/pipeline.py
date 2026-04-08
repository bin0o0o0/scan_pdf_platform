from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

import cv2
import numpy as np
from PIL import Image


DETECTION_MAX_DIMENSION = 1600
RENDER_MAX_DIMENSION = 2200
PDF_DPI = 300
A4_WIDTH_INCH = 8.27
A4_HEIGHT_INCH = 11.69
A4_WIDTH_PX = int(round(A4_WIDTH_INCH * PDF_DPI))
A4_HEIGHT_PX = int(round(A4_HEIGHT_INCH * PDF_DPI))
PDF_PAGE_MARGIN_PX = int(round(0.12 * PDF_DPI))


@dataclass(frozen=True)
class DetectorOptions:
    # 这一组参数基本来自 OSS-DocumentScanner 的文档检测默认值，
    # 目的是先尽量复用成熟项目已经验证过的搜索节奏，而不是继续拍脑袋调参。
    use_channel: int = -1
    border_size: int = 10
    canny_factor: float = 2.0
    morphology_anchor_size: int = 4
    dilate_anchor_size: int = 3
    thresh: int = 160
    thresh_max: int = 255
    median_blur_value: int = 9
    contours_approx_epsilon_factor: float = 0.02
    expected_max_cosine: float = 0.4
    expected_optimal_max_cosine: float = 0.3
    expected_area_factor: float = 0.20
    area_scale_min_factor: float = 0.04
    min_distance_from_border_factor: float = 0.0


@dataclass(frozen=True)
class WhitePaperOptions:
    # 这一组参数对应 OSS-DocumentScanner 的 whitepaper2 默认值。
    cs_black_per: float = 2.0
    cs_white_per: float = 99.5
    gauss_ksize: int = 3
    gauss_sigma: float = 1.0
    gamma_value: float = 1.1
    cb_black_per: float = 2.0
    cb_white_per: float = 1.0
    dog_ksize: int = 15
    dog_sigma1: float = 100.0
    dog_sigma2: float = 0.0


DEFAULT_DETECTOR_OPTIONS = DetectorOptions()
DEFAULT_WHITE_PAPER_OPTIONS = WhitePaperOptions()


def order_points(points: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype="float32")
    sums = points.sum(axis=1)
    rect[0] = points[np.argmin(sums)]
    rect[2] = points[np.argmax(sums)]

    diffs = np.diff(points, axis=1)
    rect[1] = points[np.argmin(diffs)]
    rect[3] = points[np.argmax(diffs)]
    return rect


def sort_points_like_detector(points: np.ndarray) -> np.ndarray:
    # 上游项目的点排序是先按 y，再分别整理顶部和底部的 x，
    # 这样得到的顺序和透视变换更稳定。
    ordered = np.array(sorted(points.tolist(), key=lambda point: point[1]), dtype="float32")
    top = ordered[:2][np.argsort(ordered[:2, 0])]
    bottom = ordered[2:][np.argsort(-ordered[2:, 0])]
    return np.vstack([top, bottom]).astype("float32")


def polygon_area(points: np.ndarray) -> float:
    x_coords = points[:, 0]
    y_coords = points[:, 1]
    return 0.5 * abs(np.dot(x_coords, np.roll(y_coords, -1)) - np.dot(y_coords, np.roll(x_coords, -1)))


def quad_dimensions(points: np.ndarray) -> tuple[float, float]:
    rect = order_points(points)
    (top_left, top_right, bottom_right, bottom_left) = rect
    width_a = np.linalg.norm(bottom_right - bottom_left)
    width_b = np.linalg.norm(top_right - top_left)
    height_a = np.linalg.norm(top_right - bottom_right)
    height_b = np.linalg.norm(top_left - bottom_left)
    return max(width_a, width_b), max(height_a, height_b)


def angle_cosine(pt1: np.ndarray, pt2: np.ndarray, pt0: np.ndarray) -> float:
    dx1 = pt1[0] - pt0[0]
    dy1 = pt1[1] - pt0[1]
    dx2 = pt2[0] - pt0[0]
    dy2 = pt2[1] - pt0[1]
    denominator = np.sqrt((dx1 * dx1 + dy1 * dy1) * (dx2 * dx2 + dy2 * dy2) + 1e-10)
    return float((dx1 * dx2 + dy1 * dy2) / denominator)


def resize_for_detection(
    image: np.ndarray,
    border_size: int = DEFAULT_DETECTOR_OPTIONS.border_size,
) -> tuple[np.ndarray, float]:
    height, width = image.shape[:2]
    longest_side = max(height, width)
    scale = 1.0
    resized = image

    if longest_side > DETECTION_MAX_DIMENSION:
        scale = longest_side / float(DETECTION_MAX_DIMENSION)
        resized_width = max(1, int(np.floor(width / scale)))
        resized_height = max(1, int(np.floor(height / scale)))
        resized = cv2.resize(image, (resized_width, resized_height), interpolation=cv2.INTER_AREA)

    if border_size > 0:
        resized = cv2.copyMakeBorder(
            resized,
            border_size,
            border_size,
            border_size,
            border_size,
            cv2.BORDER_CONSTANT,
            value=(0, 0, 0),
        )

    return resized, scale


def resize_longest_side(
    image: np.ndarray,
    max_dimension: int,
) -> np.ndarray:
    height, width = image.shape[:2]
    longest_side = max(height, width)
    if longest_side <= max_dimension:
        return image

    scale = max_dimension / float(longest_side)
    resized_width = max(1, int(round(width * scale)))
    resized_height = max(1, int(round(height * scale)))
    return cv2.resize(image, (resized_width, resized_height), interpolation=cv2.INTER_AREA)


def trim_outer_whitespace(image: Image.Image) -> Image.Image:
    prepared = image.convert("RGB")
    grayscale = np.array(prepared.convert("L"))

    # 对扫描图来说，外层留白通常接近纯白。
    # 这里用一个偏保守的阈值先找“真正有内容”的区域，
    # 再加一点点安全边距，避免把纸边附近的浅色印迹切掉。
    content_mask = grayscale < 245
    if not np.any(content_mask):
        return prepared

    ys, xs = np.where(content_mask)
    pad = max(12, int(min(prepared.size) * 0.01))

    left = max(0, int(xs.min()) - pad)
    top = max(0, int(ys.min()) - pad)
    right = min(prepared.width, int(xs.max()) + pad + 1)
    bottom = min(prepared.height, int(ys.max()) + pad + 1)
    return prepared.crop((left, top, right, bottom))


def prepare_pdf_page(image: Image.Image) -> Image.Image:
    # PDF 页面的物理尺寸统一成 A4，避免不同原图像素直接写入 PDF 后，
    # 每一页的 MediaBox 都不一样，导致阅读器里看起来纸张大小忽大忽小。
    page = Image.new("RGB", (A4_WIDTH_PX, A4_HEIGHT_PX), "white")
    content_width = A4_WIDTH_PX - (PDF_PAGE_MARGIN_PX * 2)
    content_height = A4_HEIGHT_PX - (PDF_PAGE_MARGIN_PX * 2)

    prepared = trim_outer_whitespace(image)

    scale = min(content_width / prepared.width, content_height / prepared.height)
    resized_width = max(1, int(round(prepared.width * scale)))
    resized_height = max(1, int(round(prepared.height * scale)))
    prepared = prepared.resize((resized_width, resized_height), Image.Resampling.LANCZOS)

    offset_x = (A4_WIDTH_PX - prepared.width) // 2
    offset_y = (A4_HEIGHT_PX - prepared.height) // 2
    page.paste(prepared, (offset_x, offset_y))
    return page


def compute_max_cosine(points: np.ndarray) -> tuple[float, float]:
    max_cosine = 0.0
    mean_cosine = 0.0
    for index in range(2, 6):
        cosine = abs(
            angle_cosine(
                points[index % 4],
                points[index - 2],
                points[(index - 1) % 4],
            )
        )
        max_cosine = max(max_cosine, cosine)
        mean_cosine += cosine
    return max_cosine, mean_cosine / 4.0


def contour_to_quad(contour: np.ndarray, epsilon_factor: float) -> np.ndarray | None:
    perimeter = cv2.arcLength(contour, True)
    approximation = cv2.approxPolyDP(contour, epsilon_factor * perimeter, True)
    if len(approximation) != 4:
        return None
    if not cv2.isContourConvex(approximation):
        return None
    return approximation.reshape(4, 2).astype("float32")


def _is_reasonable_document_quad(
    candidate: np.ndarray,
    image_shape: tuple[int, int],
) -> bool:
    height, width = image_shape[:2]
    area = polygon_area(candidate)
    area_ratio = area / float(height * width)
    quad_width, quad_height = quad_dimensions(candidate)
    short_side_ratio = min(quad_width, quad_height) / max(quad_width, quad_height, 1.0)

    if area_ratio < 0.08:
        return False
    if short_side_ratio < 0.35:
        return False
    return True


def select_document_contour(candidates: list[np.ndarray], image_shape: tuple[int, int]) -> np.ndarray | None:
    if not candidates:
        return None

    image_height, image_width = image_shape[:2]
    image_area = float(image_height * image_width)
    best_candidate: np.ndarray | None = None
    best_score = float("-inf")

    for candidate in candidates:
        ordered = order_points(candidate.astype("float32"))
        if not _is_reasonable_document_quad(ordered, image_shape):
            continue

        area = polygon_area(ordered)
        area_ratio = area / image_area
        width, height = quad_dimensions(ordered)
        short_side_ratio = min(width, height) / max(width, height, 1.0)

        border_distances = np.array(
            [
                ordered[:, 0].min(),
                ordered[:, 1].min(),
                image_width - ordered[:, 0].max(),
                image_height - ordered[:, 1].max(),
            ],
            dtype="float32",
        )
        border_score = 1.0 - np.clip(np.mean(border_distances) / max(image_width, image_height), 0.0, 1.0)
        preferred_area_score = 1.0 - abs(area_ratio - 0.72)
        image_fill_penalty = max(0.0, area_ratio - 0.92) * 8.0

        score = (preferred_area_score * 2.2) + (short_side_ratio * 1.5) + (border_score * 0.35) - image_fill_penalty
        if score > best_score:
            best_score = score
            best_candidate = ordered

    return best_candidate


def build_bright_page_mask(grayscale: np.ndarray) -> np.ndarray:
    height, width = grayscale.shape[:2]
    blurred = cv2.GaussianBlur(grayscale, (9, 9), 0)
    _, thresholded = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    close_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (max(21, width // 14), max(21, height // 14)),
    )
    open_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (max(7, width // 80), max(7, height // 80)),
    )

    mask = cv2.morphologyEx(thresholded, cv2.MORPH_CLOSE, close_kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, open_kernel)
    return mask


def normalize_document_background(grayscale: np.ndarray) -> np.ndarray:
    height, width = grayscale.shape[:2]
    kernel_size = max(31, ((min(height, width) // 12) | 1))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))

    # 这一层是我们在真实样本上验证过有效的补充：
    # 先估计低频背景，再做除法归一化，能明显减轻木桌底色、阴影和纸张褶皱。
    estimated_background = cv2.morphologyEx(grayscale, cv2.MORPH_CLOSE, kernel)
    normalized = cv2.divide(grayscale, estimated_background, scale=255)
    return cv2.normalize(normalized, None, 0, 255, cv2.NORM_MINMAX)


def build_page_mask(normalized_grayscale: np.ndarray) -> np.ndarray:
    height, width = normalized_grayscale.shape[:2]
    _, thresholded = cv2.threshold(
        normalized_grayscale,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )

    close_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (max(15, width // 18), max(15, height // 18)),
    )
    open_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

    mask = cv2.morphologyEx(thresholded, cv2.MORPH_CLOSE, close_kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, open_kernel)
    return mask


def build_edge_mask(normalized_grayscale: np.ndarray) -> np.ndarray:
    height, width = normalized_grayscale.shape[:2]
    blurred = cv2.GaussianBlur(normalized_grayscale, (5, 5), 0)
    edges = cv2.Canny(blurred, 30, 120)

    dilate_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    close_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (max(15, width // 20), max(15, height // 20)),
    )

    edges = cv2.dilate(edges, dilate_kernel, iterations=2)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, close_kernel)
    return edges


def _collect_fallback_candidates(image: np.ndarray) -> list[np.ndarray]:
    # 这条回退链不是拍脑袋，而是把我们前面在静态照片场景里更稳的几个候选源保留下来，
    # 然后让它们和 OSS 风格候选一起竞争，避免某一条链单独翻车。
    resized_image, scale = resize_for_detection(image, border_size=0)
    grayscale = cv2.cvtColor(resized_image, cv2.COLOR_BGR2GRAY)
    normalized = normalize_document_background(grayscale)
    image_area = float(grayscale.shape[0] * grayscale.shape[1])

    candidates: list[np.ndarray] = []
    masks = (
        build_bright_page_mask(grayscale),
        build_page_mask(normalized),
        build_edge_mask(normalized),
    )
    for mask in masks:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:12]:
            if cv2.contourArea(contour) < image_area * 0.08:
                continue

            perimeter = cv2.arcLength(contour, True)
            approximation = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
            if len(approximation) == 4 and cv2.isContourConvex(approximation):
                candidates.append((approximation.reshape(4, 2).astype("float32") * scale).astype("float32"))
                continue

            rectangle = cv2.minAreaRect(contour)
            candidates.append((cv2.boxPoints(rectangle).astype("float32") * scale).astype("float32"))

    return candidates


def _oss_style_detect_candidates(
    image: np.ndarray,
    options: DetectorOptions = DEFAULT_DETECTOR_OPTIONS,
) -> list[tuple[float, np.ndarray]]:
    working_image, scale = resize_for_detection(image, border_size=options.border_size)
    working_height, working_width = working_image.shape[:2]
    working_area = float(working_height * working_width)

    if options.median_blur_value > 0:
        blurred_image = cv2.medianBlur(working_image, options.median_blur_value)
    else:
        blurred_image = working_image

    morphology_struct = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (options.morphology_anchor_size, options.morphology_anchor_size),
    )
    dilate_struct = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (options.dilate_anchor_size, options.dilate_anchor_size),
    )

    channel_indices = [options.use_channel] if options.use_channel >= 0 else list(range(min(working_image.shape[2], 3) - 1, -1, -1))
    weight = 3_000_000.0
    found_candidates: list[tuple[float, np.ndarray]] = []

    def collect_from_mask(mask: np.ndarray, current_weight: float) -> list[tuple[float, np.ndarray]]:
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        candidates: list[tuple[float, np.ndarray]] = []
        max_allowed_area = (working_width - 2 * options.border_size) * (working_height - 2 * options.border_size) * 0.92
        margin = int(working_width * options.min_distance_from_border_factor) + options.border_size

        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            area = cv2.contourArea(contour)

            if perimeter < 100:
                continue
            if area < working_area * options.area_scale_min_factor:
                continue
            if area >= max_allowed_area:
                continue

            quad = contour_to_quad(contour, options.contours_approx_epsilon_factor)
            if quad is None:
                continue

            quad = sort_points_like_detector(quad)
            if np.any(quad[:, 0] < margin) or np.any(quad[:, 0] >= working_width - margin):
                continue
            if np.any(quad[:, 1] < margin) or np.any(quad[:, 1] >= working_height - margin):
                continue

            max_cosine, _ = compute_max_cosine(quad)
            if max_cosine >= options.expected_max_cosine:
                continue

            # 这里直接沿用上游项目的排序思想：
            # 大面积优先，同时更偏向较早阶段（阈值阶段）找到、且角更接近直角的候选。
            sort_factor = float(area) + current_weight * (1.0 - max_cosine)
            original_scale_quad = (quad - options.border_size) * scale
            candidates.append((sort_factor, original_scale_quad.astype("float32")))

        return candidates

    for channel_index in channel_indices:
        channel = cv2.extractChannel(blurred_image, channel_index)

        _, thresholded = cv2.threshold(channel, options.thresh, options.thresh_max, cv2.THRESH_BINARY)
        thresholded = cv2.morphologyEx(thresholded, cv2.MORPH_CLOSE, morphology_struct)
        thresholded = cv2.dilate(thresholded, dilate_struct)
        found_candidates.extend(collect_from_mask(thresholded, weight))
        weight -= 1.0

        if found_candidates:
            best_score, best_quad = max(found_candidates, key=lambda item: item[0])
            if compute_max_cosine(order_points(best_quad))[0] < options.expected_optimal_max_cosine:
                if polygon_area(best_quad) > (image.shape[0] * image.shape[1] * options.expected_area_factor):
                    break

        threshold = 60
        while threshold >= 10:
            edges = cv2.Canny(channel, threshold * options.canny_factor, options.canny_factor * threshold * 2)
            edges = cv2.dilate(edges, dilate_struct)
            found_candidates.extend(collect_from_mask(edges, weight))
            weight -= 1.0

            if found_candidates:
                best_score, best_quad = max(found_candidates, key=lambda item: item[0])
                if compute_max_cosine(order_points(best_quad))[0] < options.expected_optimal_max_cosine:
                    if polygon_area(best_quad) > (image.shape[0] * image.shape[1] * options.expected_area_factor):
                        threshold = 0
                        break
            threshold -= 10

    return found_candidates


def detect_document_contour(
    image: np.ndarray,
    options: DetectorOptions = DEFAULT_DETECTOR_OPTIONS,
) -> np.ndarray | None:
    ranked_oss_candidates = _oss_style_detect_candidates(image, options)
    oss_candidates = [candidate for _, candidate in ranked_oss_candidates]
    fallback_candidates = _collect_fallback_candidates(image)
    selected = select_document_contour(oss_candidates + fallback_candidates, image.shape[:2])
    if selected is None:
        reasonable_fallbacks = [candidate for candidate in fallback_candidates if _is_reasonable_document_quad(order_points(candidate), image.shape[:2])]
        if reasonable_fallbacks:
            return order_points(max(reasonable_fallbacks, key=polygon_area).astype("float32"))

        if ranked_oss_candidates:
            _, best_oss_candidate = max(ranked_oss_candidates, key=lambda item: item[0])
            return order_points(best_oss_candidate.astype("float32"))

        if fallback_candidates:
            return order_points(max(fallback_candidates, key=polygon_area).astype("float32"))

        return None
    return order_points(selected.astype("float32"))


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
    return cv2.warpPerspective(
        image,
        matrix,
        (max_width, max_height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE,
    )


def _accumulate_histogram_bounds(channel: np.ndarray, low_percent: float, high_percent: float) -> tuple[int, int]:
    histogram = cv2.calcHist([channel], [0], None, [256], [0, 256]).ravel()
    total = int(channel.size)
    low_count = int(total * (low_percent / 100.0))
    high_count = int(total * (high_percent / 100.0))

    lower_index = 0
    upper_index = 255

    cumulative = 0
    for index, value in enumerate(histogram):
        cumulative += int(value)
        if cumulative > low_count:
            lower_index = index
            break

    cumulative = 0
    for index in range(255, -1, -1):
        cumulative += int(histogram[index])
        if cumulative > high_count:
            upper_index = index
            break

    return lower_index, upper_index


def _apply_lut_stretch(channel: np.ndarray, lower_index: int, upper_index: int) -> np.ndarray:
    lut = np.zeros((256,), dtype=np.uint8)
    if upper_index > lower_index:
        scale = 255.0 / float(upper_index - lower_index)
        for value in range(256):
            if value < lower_index:
                lut[value] = 0
            elif value > upper_index:
                lut[value] = 255
            else:
                lut[value] = np.uint8(round((value - lower_index) * scale))
    return cv2.LUT(channel, lut)


def _contrast_stretch(image: np.ndarray, black_percent: float, white_percent: float) -> np.ndarray:
    channels = cv2.split(image)
    stretched_channels = []
    for channel in channels:
        lower_index, upper_index = _accumulate_histogram_bounds(channel, black_percent, 100.0 - white_percent)
        stretched_channels.append(_apply_lut_stretch(channel, lower_index, upper_index))
    return cv2.merge(stretched_channels)


def _color_balance(image: np.ndarray, low_percent: float, high_percent: float) -> np.ndarray:
    channels = cv2.split(image)
    balanced_channels = []
    for channel in channels:
        lower_index, upper_index = _accumulate_histogram_bounds(channel, low_percent, 100.0 - high_percent)
        balanced_channels.append(_apply_lut_stretch(channel, lower_index, upper_index))
    return cv2.merge(balanced_channels)


def _difference_of_gaussians(image: np.ndarray, kernel_size: int, sigma1: float, sigma2: float) -> np.ndarray:
    if sigma1 > 0:
        blurred_1 = cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma1)
    else:
        blurred_1 = image.copy()

    if sigma2 > 0:
        blurred_2 = cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma2)
    else:
        blurred_2 = image.copy()

    return cv2.subtract(blurred_1, blurred_2)


def _gamma_correction(image: np.ndarray, gamma_value: float) -> np.ndarray:
    inverse_gamma = 1.0 / gamma_value
    lut = np.array(
        [np.clip(round((value / 255.0) ** inverse_gamma * 255.0), 0, 255) for value in range(256)],
        dtype=np.uint8,
    )
    return cv2.LUT(image, lut)


def whitepaper_enhance(
    image: np.ndarray,
    options: WhitePaperOptions = DEFAULT_WHITE_PAPER_OPTIONS,
) -> np.ndarray:
    # 这里基本按 OSS-DocumentScanner 的 whitepaper2 流程走，
    # 先用 DoG 提亮纸面、压掉低频背景，再做拉伸、轻模糊、伽马和色彩平衡。
    dogged = _difference_of_gaussians(image, options.dog_ksize, options.dog_sigma1, options.dog_sigma2)
    negated = cv2.bitwise_not(dogged)
    stretched = _contrast_stretch(negated, options.cs_black_per, options.cs_white_per)

    if options.gauss_ksize > 0:
        blurred = cv2.GaussianBlur(stretched, (options.gauss_ksize, options.gauss_ksize), options.gauss_sigma)
    else:
        blurred = stretched

    gamma_corrected = _gamma_correction(blurred, options.gamma_value)
    return _color_balance(gamma_corrected, options.cb_black_per, options.cb_white_per)


def remove_small_noise(binary_image: np.ndarray) -> np.ndarray:
    inverted = 255 - binary_image
    component_count, labels, stats, _ = cv2.connectedComponentsWithStats(inverted, connectivity=8)
    cleaned = np.zeros_like(inverted)

    # 这里保留一个很轻的连通域过滤，避免输出里残留一片胡椒盐黑点。
    min_component_area = max(12, int(min(binary_image.shape[:2]) * 0.006))
    for label in range(1, component_count):
        area = stats[label, cv2.CC_STAT_AREA]
        if area >= min_component_area:
            cleaned[labels == label] = 255

    return 255 - cleaned


def clean_document_image(grayscale: np.ndarray) -> np.ndarray:
    rendered = render_document_image(grayscale)
    if rendered.ndim == 3:
        rendered_gray = cv2.cvtColor(rendered, cv2.COLOR_BGR2GRAY)
    else:
        rendered_gray = rendered

    binary = cv2.adaptiveThreshold(
        rendered_gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        35,
        9,
    )
    binary = remove_small_noise(binary)
    open_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    return cv2.morphologyEx(binary, cv2.MORPH_OPEN, open_kernel)


def render_document_image(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        color_working = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        grayscale_output = True
    else:
        color_working = image.copy()
        grayscale_output = False

    # 在 whitepaper2 之前加一层轻量去噪，主要是为了手机 JPEG 颗粒和桌面纹理。
    denoised_color = cv2.fastNlMeansDenoisingColored(color_working, None, 3, 3, 7, 21)
    whitepaper_color = whitepaper_enhance(denoised_color)

    grayscale = cv2.cvtColor(color_working, cv2.COLOR_BGR2GRAY)
    normalized = normalize_document_background(grayscale)
    denoised_gray = cv2.fastNlMeansDenoising(normalized, None, 8, 7, 21)
    background = cv2.GaussianBlur(denoised_gray, (0, 0), 61)
    flattened = denoised_gray.astype("float32") - background.astype("float32") + 228.0
    flattened = np.clip(flattened, 0, 255).astype("uint8")

    sharpen_blur = cv2.GaussianBlur(flattened, (0, 0), 1.0)
    refined_lightness = cv2.addWeighted(flattened, 1.08, sharpen_blur, -0.08, 0)

    whitepaper_lab = cv2.cvtColor(whitepaper_color, cv2.COLOR_BGR2LAB)
    _, channel_a, channel_b = cv2.split(whitepaper_lab)
    rendered = cv2.cvtColor(cv2.merge([refined_lightness, channel_a, channel_b]), cv2.COLOR_LAB2BGR)

    if grayscale_output:
        return refined_lightness
    return rendered


def scan_image(pil_image: Image.Image) -> Image.Image:
    image = cv2.cvtColor(np.array(pil_image.convert("RGB")), cv2.COLOR_RGB2BGR)
    document_contour = detect_document_contour(image)

    if document_contour is None:
        warped = image
    else:
        warped = four_point_transform(image, document_contour.astype("float32"))

    # 这里做的是性能和质量之间最关键的一层平衡：
    # 手机原图往往是 3000~6000 像素级别，如果直接在全分辨率上跑
    # 去噪、DoG、超大 sigma 的背景拉平，单页就会卡到几十秒。
    # 扫描类网页产品通常不会保留原始拍照分辨率，而是压到足够清晰、
    # 但处理时间可控的输出尺寸。
    warped = resize_longest_side(warped, RENDER_MAX_DIMENSION)

    rendered = render_document_image(warped)
    rendered_rgb = cv2.cvtColor(rendered, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rendered_rgb)


def images_to_pdf(images: list[Image.Image]) -> BytesIO:
    if not images:
        raise ValueError("images must not be empty")

    output = BytesIO()
    first_page, *other_pages = [prepare_pdf_page(image) for image in images]
    first_page.save(
        output,
        format="PDF",
        save_all=True,
        append_images=other_pages,
        resolution=PDF_DPI,
    )
    output.seek(0)
    return output
