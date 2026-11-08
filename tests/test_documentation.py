from fetch_unity import extract_documentation


def test_extract_documentation_article():
    html = """
    <html>
        <body>
            <nav>Unity Navigation Menu</nav>

            <article>
                <h1>Rigidbody2D</h1>
                <p>Controls 2D physics in Unity.</p>
            </article>

            <footer>Unity Copyright</footer>
        </body>
    </html>
    """

    text = extract_documentation(html)

    assert "Rigidbody2D" in text
    assert "Controls 2D physics in Unity." in text
    assert "Unity Navigation Menu" not in text
    assert "Unity Copyright" not in text


def test_missing_article_raises_error():
    html = "<html><body><p>No article here.</p></body></html>"

    try:
        extract_documentation(html)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for missing article")