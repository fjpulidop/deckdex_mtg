"""Tests for the migration runner SQL splitting logic in scripts/setup_db.py."""


def strip_comment_lines(sql: str) -> str:
    """Reproduce the comment-stripping logic from setup_db.run_migrations."""
    return "\n".join(
        line for line in sql.splitlines()
        if not line.strip().startswith("--")
    )


def strip_leading_comments(s: str) -> str:
    """Reproduce the fragment cleaner from setup_db.run_migrations."""
    lines = s.strip().splitlines()
    while lines and (not lines[0].strip() or lines[0].strip().startswith("--")):
        lines.pop(0)
    return "\n".join(lines).strip()


def split_sql(sql_content: str) -> list[str]:
    """Simulate how setup_db splits and cleans SQL content."""
    sql_content = strip_comment_lines(sql_content)
    stmts = []
    for fragment in sql_content.split(";"):
        cleaned = strip_leading_comments(fragment)
        if cleaned:
            stmts.append(cleaned)
    return stmts


class TestSqlSplitting:
    def test_semicolon_inside_comment_is_ignored(self):
        """The bug: a ';' inside a '--' comment must not split the statement."""
        sql = (
            "-- Defaults to FALSE; bootstrap admin via env var\n"
            "\n"
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;\n"
        )
        stmts = split_sql(sql)
        assert len(stmts) == 1
        assert stmts[0].startswith("ALTER TABLE")

    def test_multiple_statements(self):
        sql = (
            "CREATE TABLE foo (id INT);\n"
            "CREATE INDEX idx_foo ON foo (id);\n"
        )
        stmts = split_sql(sql)
        assert len(stmts) == 2
        assert "CREATE TABLE" in stmts[0]
        assert "CREATE INDEX" in stmts[1]

    def test_comments_between_statements(self):
        sql = (
            "-- First table\n"
            "CREATE TABLE a (id INT);\n"
            "\n"
            "-- Second table; has semicolon in comment\n"
            "CREATE TABLE b (id INT);\n"
        )
        stmts = split_sql(sql)
        assert len(stmts) == 2
        assert "a" in stmts[0]
        assert "b" in stmts[1]

    def test_empty_input(self):
        assert split_sql("") == []
        assert split_sql("-- just a comment") == []

    def test_trailing_semicolon_no_extra_statement(self):
        sql = "SELECT 1;\n"
        stmts = split_sql(sql)
        assert len(stmts) == 1
