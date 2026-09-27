from unittest.mock import patch
from streamlit.testing.v1 import AppTest


class Upload:
    size = 4
    name = "sample.pdf"
    type = "application/pdf"

    def getvalue(self):
        return b"test"


RESULT = {
    "filename": "sample.pdf", "document": {"type": "university", "confidence": .9},
    "fields": {"name": {"value": "<script>unsafe</script>", "confidence": .9}},
    "issues": [], "text": "Sample form", "ocr_seconds": .1,
}


def test_analyze_once_and_export_survives_rerun():
    with patch("streamlit.file_uploader", return_value=Upload()), patch(
        "app.core.process_document", return_value=RESULT
    ) as process, patch("app.core.save_metadata") as save, patch("app.core.recent_documents", return_value=[]):
        app = AppTest.from_file("streamlit_app.py").run()
        assert not app.exception
        app.button[0].click().run()
        assert not app.exception
        assert app.session_state["result"] == RESULT
        app.run()
        assert not app.exception
        assert app.button[0].disabled
        assert process.call_count == save.call_count == 1
        assert "unsafe" in app.session_state["export_json"]


def test_failed_processing_can_retry():
    with patch("streamlit.file_uploader", return_value=Upload()), patch(
        "app.core.process_document", side_effect=ValueError("Unreadable PDF")
    ), patch("app.core.recent_documents", return_value=[]):
        app = AppTest.from_file("streamlit_app.py").run()
        app.button[0].click().run()
        assert not app.exception
        assert "Unreadable PDF" in app.error[0].value
        assert not app.button[0].disabled
