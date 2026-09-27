import json
from html import escape
from pathlib import Path

import streamlit as st

from app.core import MAX_FILE_BYTES, process_document, recent_documents, save_metadata

st.set_page_config(page_title="FormPilot · Document workspace", page_icon="◈", layout="wide")
st.html("<style>" + Path(__file__).with_name("ui.css").read_text(encoding="utf-8") + "</style>")


def reset_document():
    for key in ("result", "export_json"):
        st.session_state.pop(key, None)


st.html('<div class="topbar"><div class="brand"><span class="brand-icon">◈</span> FormPilot</div>'
        '<span class="local-badge"><span></span> Local workspace</span></div>')
st.html('<div class="hero"><p class="eyebrow">LESS PAPERWORK. MORE POSSIBILITY.</p>'
        '<h1>Your next chapter.<br><span>Ready for review.</span></h1>'
        '<p>Turn academic forms into clear fields and a practical checklist.<br>'
        'University, scholarship, and internship documents, all in one place.</p></div>')

workspace, history_tab = st.tabs(["Document workspace", "Recent activity"])
with workspace:
    upload_col, review_col = st.columns([1, 1.65], gap="large")
    with upload_col:
        with st.container(border=True, key="upload_panel"):
            st.markdown("### 01 / Add a document")
            st.caption("PDF, PNG, JPG or WEBP · Up to 15 MB")
            uploaded = st.file_uploader("Choose your document", type=["pdf", "png", "jpg", "jpeg", "webp"],
                                        key="upload", on_change=reset_document)
            oversize = uploaded is not None and uploaded.size > MAX_FILE_BYTES
            if oversize:
                st.error("This file exceeds 15 MB. Choose a smaller document.")
            analyzed = st.session_state.get("result") is not None
            if st.button("Analyze document", type="primary", use_container_width=True,
                         disabled=uploaded is None or oversize or analyzed):
                with st.spinner("Reading and checking your document…"):
                    try:
                        result = process_document(uploaded.getvalue(), uploaded.name, uploaded.type)
                    except Exception as error:
                        st.error(f"Could not read this document. {error}")
                        st.caption("Try a clearer scan. Scanned pages require Tesseract on this computer.")
                    else:
                        st.session_state.result = result
                        st.session_state.export_json = json.dumps(result, indent=2)
                        try:
                            save_metadata(result)
                        except Exception:
                            st.warning("Your result is ready, but local history could not be saved.")
            st.html('<div class="privacy-note"><strong>Private by design</strong><br>'
                    'Documents are processed on the machine running FormPilot. '
                    'No cloud extraction service is used.</div>')
        st.html('<div class="how-it-works"><p class="eyebrow">A LITTLE PREPARATION HELPS</p>'
                '<p>Use a clear, upright scan with visible labels. Review every extracted '
                'value before using it in an application.</p></div>')

    with review_col:
        result = st.session_state.get("result")
        with st.container(border=True, key="review_panel"):
            st.markdown("### 02 / Review your results")
            if not result:
                st.html('<div class="empty-state"><div class="document-symbol">≡</div>'
                        '<h2>A clearer view of your form.</h2>'
                        '<p>Add a document, then select Analyze document.<br>'
                        'Your fields and checklist will appear here.</p>'
                        '<div class="steps"><span>01 · Extract</span><span>02 · Check</span>'
                        '<span>03 · Export</span></div></div>')
            else:
                st.caption(result["filename"])
                a, b, c = st.columns(3)
                a.metric("Document type", result["document"]["type"].title())
                b.metric("Fields found", f'{sum(bool(v["value"]) for v in result["fields"].values())} / {len(result["fields"])}')
                c.metric("Reading time", f'{result["ocr_seconds"]:.2f}s')
                st.caption("Confidence scores are heuristic estimates, not verified accuracy.")
                fields_tab, checks_tab, text_tab = st.tabs(["Extracted fields", f'Checklist ({len(result["issues"])})', "Source text"])
                with fields_tab:
                    rows = "".join(
                        '<div class="field-row"><span class="field-label">' + escape(key.replace("_", " ").title()) +
                        '</span><strong>' + escape(str(value["value"] or "Not found")) +
                        '</strong><span class="field-score">' + f'{value["confidence"]:.0%}' + '</span></div>'
                        for key, value in result["fields"].items()
                    )
                    st.html('<div class="fields">' + rows + '</div>')
                with checks_tab:
                    if not result["text"].strip():
                        st.warning("No readable text found. Try a sharper scan.")
                    if not result["issues"]:
                        st.success("No rule-based issues found. Review the extracted values before submitting.")
                    for issue in result["issues"]:
                        (st.error if issue["severity"] == "error" else st.warning)(issue["message"])
                with text_tab:
                    st.text(result["text"] or "No text detected.")
                st.download_button("Export result as JSON", st.session_state.export_json,
                                   file_name="formpilot-result.json", mime="application/json",
                                   use_container_width=True)

with history_tab:
    st.markdown("### Recent activity")
    st.caption("The last 10 processing records on this machine. Original documents are not retained.")
    try:
        history = recent_documents()
    except Exception:
        st.warning("Local history is unavailable. You can still analyze documents.")
    else:
        if history:
            st.dataframe(history, use_container_width=True, hide_index=True)
        else:
            st.info("Your workspace is fresh. Analyze a document to create the first record.")

st.html('<div class="footer">FormPilot <span>Made for the next step in your student journey.</span></div>')
