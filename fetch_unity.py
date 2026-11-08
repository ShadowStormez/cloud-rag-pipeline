from pathlib import Path
from utils import calculate_hash
import requests
from bs4 import BeautifulSoup

def extract_documentation(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for element in soup(["script", "style", "nav", "footer"]):
        element.decompose()

    article = soup.find("article")

    if article is None:
        raise ValueError("Documentation article not found.")

    return article.get_text(separator="\n", strip=True)

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

    text = extract_documentation(response.text)

    # Determine the output file
    output_file = OUTPUT_DIR / f"{name}.txt"

    # Calculate the hash of the downloaded content
    new_hash = calculate_hash(text)

    # Compare with the existing file
    if output_file.exists():
        old_hash = calculate_hash(
            output_file.read_text(encoding="utf-8")
        )

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