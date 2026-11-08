from unittest.mock import patch, Mock
from pathlib import Path
import fetch_unity


def test_fetch_new_document(tmp_path):
    # Create a fake HTML response
    html = """
    <html>
        <article>
            <h1>Rigidbody2D</h1>
            <p>Controls 2D physics.</p>
        </article>
    </html>
    """

    # Simulate the website's response
    fake_response = Mock()
    fake_response.text = html

    # Replace the real output directory with a temporary one
    with patch.object(fetch_unity, "OUTPUT_DIR", tmp_path):

        # Replace requests.get() with a fake response
        with patch("fetch_unity.requests.get", return_value=fake_response):

            fetch_unity.fetch_documentation(
                "Rigidbody2D",
                "https://example.com"
            )

    # Verify that the documentation file was created
    output_file = tmp_path / "Rigidbody2D.txt"

    assert output_file.exists()

    # Verify that the extracted content was saved
    content = output_file.read_text(encoding="utf-8")

    assert "Rigidbody2D" in content
    assert "Controls 2D physics." in content

def test_fetch_unchanged_document(tmp_path):
    html = """
    <article>
        <h1>Rigidbody2D</h1>
        <p>Controls 2D physics.</p>
    </article>
    """

    # Create an existing documentation file
    output_file = tmp_path / "Rigidbody2D.txt"
    original_content = "Rigidbody2D\nControls 2D physics."
    output_file.write_text(original_content, encoding="utf-8")

    # Create a fake website response
    fake_response = Mock()
    fake_response.text = html

    with patch.object(fetch_unity, "OUTPUT_DIR", tmp_path):
        with patch("fetch_unity.requests.get", return_value=fake_response):

            # Monitor whether the file is rewritten
            with patch.object(
                Path,
                "write_text",
                autospec=True,
                wraps=None
            ) as mock_write:

                result = fetch_unity.fetch_documentation(
                    "Rigidbody2D",
                    "https://example.com"
                )

                # The file should not be rewritten
                mock_write.assert_not_called()

    assert result == original_content
    assert output_file.read_text(encoding="utf-8") == original_content

def test_fetch_updated_document(tmp_path):
    # Create an existing file with old documentation
    output_file = tmp_path / "Rigidbody2D.txt"
    output_file.write_text(
        "Rigidbody2D\nOld documentation.",
        encoding="utf-8"
    )

    # Simulate updated documentation from Unity
    html = """
    <article>
        <h1>Rigidbody2D</h1>
        <p>Updated documentation with new features.</p>
    </article>
    """

    fake_response = Mock()
    fake_response.text = html

    # Replace the real output directory and HTTP request
    with patch.object(fetch_unity, "OUTPUT_DIR", tmp_path):
        with patch(
            "fetch_unity.requests.get",
            return_value=fake_response
        ):
            result = fetch_unity.fetch_documentation(
                "Rigidbody2D",
                "https://example.com"
            )

    # Verify the file contains updated documentation
    updated_content = output_file.read_text(encoding="utf-8")

    assert "Updated documentation with new features." in updated_content
    assert "Old documentation." not in updated_content
    assert result == updated_content