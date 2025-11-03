import os
import pytest

@pytest.mark.skipif(os.environ.get("CI") == "true", reason="No display on CI")
def test_app_init(app):
    assert app.title() == "Medical Inventory System"
    assert app.tree.heading("barcode")["text"] == "Barcode"