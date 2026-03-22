from auth.password import hash_password, verify_password


def test_hash_and_verify():
    hashed = hash_password("mypassword")
    assert hashed != "mypassword"
    assert verify_password("mypassword", hashed) is True


def test_verify_wrong_password():
    hashed = hash_password("correct")
    assert verify_password("wrong", hashed) is False
