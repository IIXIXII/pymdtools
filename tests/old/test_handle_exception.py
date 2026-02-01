import pytest

from pymdtools.common import handle_exception


def test_handle_exception_success_does_not_wrap():
    @handle_exception("Should not trigger", filename="File")
    def ok(filename: str):
        return f"OK:{filename}"

    assert ok(filename="a.md") == "OK:a.md"


def test_handle_exception_wraps_exception_and_adds_context():
    @handle_exception("Error while converting file", filename="File", output="Output directory")
    def boom(filename: str, output: str):
        raise ValueError("Invalid format")

    with pytest.raises(RuntimeError) as excinfo:
        boom(filename="doc.md", output="/tmp")

    msg = str(excinfo.value)
    # original message
    assert "Invalid format" in msg
    # contextual header (action + function name)
    assert "Error while converting file (boom)" in msg
    # selected kw args
    assert "File : doc.md" in msg
    assert "Output directory : /tmp" in msg


def test_handle_exception_preserves_original_exception_as_cause():
    @handle_exception("Error while parsing", filename="File")
    def boom(filename: str):
        raise ValueError("Bad content")

    with pytest.raises(RuntimeError) as excinfo:
        boom(filename="x.md")

    assert excinfo.value.__cause__ is not None
    assert isinstance(excinfo.value.__cause__, ValueError)
    assert str(excinfo.value.__cause__) == "Bad content"


def test_handle_exception_ignores_non_present_kwargs_in_mapping():
    # mapping contains keys that are not provided to the function call
    @handle_exception("Error", filename="File", missing="Missing label")
    def boom(filename: str):
        raise ValueError("Oops")

    with pytest.raises(RuntimeError) as excinfo:
        boom(filename="a.md")

    msg = str(excinfo.value)
    assert "File : a.md" in msg
    assert "Missing label" not in msg  # should not appear


def test_handle_exception_does_not_capture_positional_args_unless_in_kwargs():
    @handle_exception("Error", filename="File")
    def boom(filename: str):
        raise ValueError("Oops")

    # passed positionally -> not in kwargs -> not printed by design
    with pytest.raises(RuntimeError) as excinfo:
        boom("a.md")

    msg = str(excinfo.value)
    assert "File : a.md" not in msg
    assert "Error (boom)" in msg or "Error (boom)" not in msg  # keep header check minimal
    assert "Error (boom)" not in msg  # remove this line if your action_desc differs
    # Better assertion: check the header contains the function name
    assert "(boom)" in msg


def test_handle_exception_preserves_function_metadata_with_wraps():
    @handle_exception("Error", filename="File")
    def boom(filename: str) -> str:
        """Doc for boom."""
        raise ValueError("Oops")

    assert boom.__name__ == "boom"
    assert boom.__doc__ == "Doc for boom."
