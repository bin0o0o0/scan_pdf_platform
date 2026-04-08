import cv2
import numpy as np
from PIL import Image

from app.scanner.pipeline import (
    clean_document_image,
    detect_document_contour,
    prepare_pdf_page,
    render_document_image,
    select_document_contour,
)


def test_select_document_contour_prefers_large_page_like_quad():
    image_shape = (3000, 2200)
    large_page = np.array(
        [
            [180, 120],
            [2020, 110],
            [2090, 2860],
            [120, 2910],
        ],
        dtype="float32",
    )
    tiny_inner_box = np.array(
        [
            [900, 1100],
            [1350, 1100],
            [1350, 1450],
            [900, 1450],
        ],
        dtype="float32",
    )

    selected = select_document_contour([tiny_inner_box, large_page], image_shape)

    assert np.allclose(selected, large_page)


def test_select_document_contour_rejects_thin_strip_like_quad():
    image_shape = (3000, 2200)
    page = np.array(
        [
            [160, 140],
            [2050, 120],
            [2110, 2880],
            [110, 2920],
        ],
        dtype="float32",
    )
    thin_strip = np.array(
        [
            [300, 120],
            [1950, 120],
            [1950, 420],
            [300, 420],
        ],
        dtype="float32",
    )

    selected = select_document_contour([thin_strip, page], image_shape)

    assert np.allclose(selected, page)


def test_detect_document_contour_finds_bright_page_region():
    image = np.full((1200, 900, 3), 90, dtype=np.uint8)
    page = np.array(
        [
            [120, 110],
            [760, 95],
            [810, 1080],
            [80, 1105],
        ],
        dtype=np.int32,
    )

    cv2.fillConvexPoly(image, page, (235, 235, 235))
    cv2.rectangle(image, (240, 250), (650, 290), (40, 40, 40), thickness=-1)
    cv2.rectangle(image, (240, 370), (620, 405), (40, 40, 40), thickness=-1)

    detected = detect_document_contour(image)

    assert detected is not None
    assert np.allclose(detected, page.astype("float32"), atol=80)


def test_clean_document_image_suppresses_background_noise_without_erasing_text():
    image = np.full((900, 700), 235, dtype=np.uint8)

    # 人工制造一个从上到下变暗的阴影背景，模拟手机拍照时常见的光照不均。
    gradient = np.linspace(0, 70, image.shape[0], dtype=np.uint8).reshape(-1, 1)
    image = np.clip(image - gradient, 0, 255).astype(np.uint8)

    # 模拟两行正文。
    image[180:205, 120:560] = 45
    image[270:295, 120:520] = 45

    rng = np.random.default_rng(7)
    noise_points = rng.integers(low=[0, 0], high=[image.shape[0], image.shape[1]], size=(4500, 2))
    image[noise_points[:, 0], noise_points[:, 1]] = rng.choice([0, 255], size=len(noise_points))

    cleaned = clean_document_image(image)

    background_patch = cleaned[520:820, 120:620]
    text_patch = cleaned[180:205, 120:560]

    # 背景区域应当尽量接近纯白，避免满页黑点。
    assert np.mean(background_patch < 128) < 0.03
    # 文本区域不能被一起抹掉。
    assert np.mean(text_patch < 128) > 0.6


def test_render_document_image_flattens_background_while_keeping_text_darker():
    image = np.full((900, 700), 232, dtype=np.uint8)
    gradient = np.linspace(0, 85, image.shape[0], dtype=np.uint8).reshape(-1, 1)
    image = np.clip(image - gradient, 0, 255).astype(np.uint8)

    image[160:190, 100:580] = 55
    image[260:290, 100:530] = 55

    rng = np.random.default_rng(13)
    noise_points = rng.integers(low=[0, 0], high=[image.shape[0], image.shape[1]], size=(5000, 2))
    image[noise_points[:, 0], noise_points[:, 1]] = np.clip(
        image[noise_points[:, 0], noise_points[:, 1]] + rng.integers(-45, 45, size=len(noise_points)),
        0,
        255,
    )

    rendered = render_document_image(image)

    original_background = image[520:820, 120:620]
    rendered_background = rendered[520:820, 120:620]
    rendered_text = rendered[160:190, 100:580]

    original_row_span = np.ptp(original_background.mean(axis=1))
    rendered_row_span = np.ptp(rendered_background.mean(axis=1))

    # 背景的大尺度明暗起伏应该明显收敛。
    assert rendered_row_span < original_row_span * 0.5
    # 文字仍然应明显比背景更深，不能被磨没。
    assert rendered_text.mean() + 35 < rendered_background.mean()


def test_prepare_pdf_page_normalizes_all_pages_to_same_a4_canvas():
    portrait = np.full((1400, 900, 3), 240, dtype=np.uint8)
    landscape = np.full((900, 1400, 3), 230, dtype=np.uint8)

    portrait_page = prepare_pdf_page(Image.fromarray(portrait))
    landscape_page = prepare_pdf_page(Image.fromarray(landscape))

    assert portrait_page.size == landscape_page.size
    assert portrait_page.size == (2481, 3507)


def test_prepare_pdf_page_trims_outer_whitespace_before_fitting_a4():
    image = np.full((1600, 1200, 3), 255, dtype=np.uint8)
    image[250:1350, 180:1020] = 235
    image[360:420, 260:940] = 30
    image[520:580, 260:900] = 30

    page = np.array(prepare_pdf_page(Image.fromarray(image)))
    non_white_mask = np.any(page < 245, axis=2)
    ys, xs = np.where(non_white_mask)

    used_width = xs.max() - xs.min() + 1
    used_height = ys.max() - ys.min() + 1

    assert used_width > 1800
    assert used_height > 2600


def test_prepare_pdf_page_keeps_only_small_a4_margins_after_trim():
    image = np.full((1800, 1300, 3), 255, dtype=np.uint8)
    image[300:1500, 210:1090] = 236
    image[430:470, 280:990] = 40
    image[610:650, 280:950] = 40

    page = np.array(prepare_pdf_page(Image.fromarray(image)))
    non_white_mask = np.any(page < 245, axis=2)
    ys, xs = np.where(non_white_mask)

    top_margin = ys.min()
    bottom_margin = page.shape[0] - ys.max() - 1
    left_margin = xs.min()
    right_margin = page.shape[1] - xs.max() - 1

    assert top_margin < 180
    assert bottom_margin < 180
    assert left_margin < 180
    assert right_margin < 180
