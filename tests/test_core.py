from app.core import classify_document, extract_fields, validate_fields


TEXT = """University Malaya\nFull Name: Nur Aisyah Ahmad\nEmail: aisyah@example.com\nPhone: 012-3456789\nProgramme: Bachelor of Computer Science\nCGPA: 3.72\n"""


def test_extracts_common_fields():
    fields = extract_fields(TEXT)
    assert fields["name"]["value"] == "Nur Aisyah Ahmad"
    assert fields["cgpa"]["value"] == "3.72"
    assert fields["email"]["value"] == "aisyah@example.com"


def test_classifies_university_form():
    assert classify_document(TEXT)["type"] == "university"


def test_flags_missing_and_invalid_cgpa():
    issues = validate_fields({"cgpa": {"value": "4.8"}})
    assert any(issue["field"] == "cgpa" and issue["severity"] == "error" for issue in issues)
    assert any(issue["field"] == "name" for issue in issues)
