from .conftest import login


def test_scan_endpoint_returns_pdf(client, sample_image_file):
    token = login(client, "student", "student123")

    response = client.post(
        "/api/scan",
        data={"files[]": (sample_image_file, "page-1.png")},
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")
