from utils import calculate_hash


def test_same_content_produces_same_hash():
    content = "Unity Rigidbody2D documentation"

    hash1 = calculate_hash(content)
    hash2 = calculate_hash(content)

    assert hash1 == hash2


def test_different_content_produces_different_hash():
    original = "Rigidbody2D applies forces."
    updated = "Rigidbody2D applies forces and torque."

    original_hash = calculate_hash(original)
    updated_hash = calculate_hash(updated)

    assert original_hash != updated_hash


def test_hash_has_correct_length():
    content = "Unity documentation"

    result = calculate_hash(content)

    assert len(result) == 64