import json

import streamlit as st

from app.core import process_document, save_metadata

st.set_page_config(page_title="FormPilot", page_icon="📄", layout="wide")
st.title("FormPilot")
st.caption("Offline document extraction for Malaysian students")
st.info("🔒 Your document is processed locally. It is not uploaded to a cloud service.")

uploaded = st.file_uploader("Upload a university, scholarship, or internship form", type=["pdf", "png", "jpg", "jpeg", "webp"])
if uploaded:
    with st.spinner("Reading your document locally…"):
        try:
            result = process_document(uploaded.getvalue(), uploaded.name, uploaded.type)
            save_metadata(result)
        except Exception as error:
            st.error(str(error))
        else:
            left, right = st.columns(2)
            with left:
                st.subheader("Document")
                st.metric("Detected type", result["document"]["type"].title())
                st.metric("Confidence", f"{result['document']['confidence']:.0%}")
                st.caption(f"OCR completed in {result['ocr_seconds']}s")
            with right:
                st.subheader("Checklist")
                errors = sum(issue["severity"] == "error" for issue in result["issues"])
                warnings = sum(issue["severity"] == "warning" for issue in result["issues"])
                st.metric("Issues", f"{errors} errors · {warnings} warnings")
                for issue in result["issues"]:
                    (st.error if issue["severity"] == "error" else st.warning)(issue["message"])
            st.subheader("Extracted fields")
            st.dataframe([{"Field": key.replace("_", " ").title(), "Value": value["value"] or "—", "Confidence": f"{value['confidence']:.0%}"} for key, value in result["fields"].items()], use_container_width=True, hide_index=True)
            with st.expander("OCR text"):
                st.text(result["text"] or "No text detected.")
            st.download_button("Download JSON", json.dumps(result, indent=2), file_name="formpilot-result.json", mime="application/json")
