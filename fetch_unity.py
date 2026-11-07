from pathlib import Path
import hashlib
import requests
from bs4 import BeautifulSoup

# Unity documentation pages to download
UNITY_PAGES = {
    "SpriteRenderer": (
        "https://docs.unity3d.com/6000.0/Documentation/"
        "ScriptReference/SpriteRenderer.html"
    ),
    "Rigidbody2D": (
        "https://docs.unity3d.com/6000.0/Documentation/"
        "ScriptReference/Rigidbody2D.html"
    ),
}

# Directory for downloaded documentation
OUTPUT_DIR = Path("data/unity")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def fetch_documentation(name, url):
    """Download and extract one Unity documentation page."""

    print(f"\nFetching {name} documentation...")

    # Download the HTML page
    response = requests.get(url, timeout=20)
    response.raise_for_status()

    # Parse the HTML
    soup = BeautifulSoup(response.text, "html.parser")

    # Remove unnecessary elements
    for element in soup(["script", "style", "nav", "footer"]):
        element.decompose()

    # Extract the main documentation article
    article = soup.find("article")

    if article is None:
        raise ValueError(f"Could not find article for {name}")

    text = article.get_text(separator="\n", strip=True)

    # Determine the output file
    output_file = OUTPUT_DIR / f"{name}.txt"

    # Calculate the hash of the downloaded content
    new_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

    # Compare with the existing file
    if output_file.exists():
        old_hash = hashlib.sha256(output_file.read_bytes()).hexdigest()

        if new_hash == old_hash:
            print(f"No changes detected: {name}")
            return text

    # Save new or updated documentation
    output_file.write_text(text, encoding="utf-8")

    print(f"Extracted {len(text)} characters.")
    print(f"New or updated documentation saved to: {output_file}")

    return text


def main():
    """Download all configured Unity documentation pages."""

    for name, url in UNITY_PAGES.items():
        fetch_documentation(name, url)

    print("\nAll Unity documentation pages downloaded successfully!")


if __name__ == "__main__":
    main()