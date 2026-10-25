from app.services.sql_prompt_revision import clarify_prompt


def test_wording_identifies_provided_tables_without_changing_requirement():
    original = "Liệt kê tên sinh viên có điểm từ 8 trở lên."
    revised = clarify_prompt(original, 'CREATE TABLE students (name TEXT, score INT); CREATE TABLE classes (id INT);')
    assert revised.startswith("Cho sẵn bảng students, classes")
    assert revised.endswith(original)
    assert "Viết câu truy vấn SQL" in revised
    assert clarify_prompt(revised, 'CREATE TABLE students (id INT);') == revised
