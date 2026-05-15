from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_roundtrip() -> None:
    password_hash = hash_password("correct-password")

    assert verify_password("correct-password", password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_access_token_roundtrip() -> None:
    token = create_access_token("123", {"role": "CASHIER"})

    payload = decode_access_token(token)

    assert payload["sub"] == "123"
    assert payload["role"] == "CASHIER"
