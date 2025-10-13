import hmac
import hashlib
import base64
import bcrypt

# The plain-text password from user input (e.g., a login form)
# Note: The bcrypt library requires it to be in bytes.
password_to_check_1 = b'swadbotpass123'
password_to_check_2 = b'JdFNDZRS3FbVvxx'
# The full hash string copied directly from the WordPress database
hash_from_db_1 = b'$wp$2y$10$gF47sr.RlPd9s4wzbUkhw.BvHk2cqFA9rmePir1Dgu/FgO0Gpf5Iu'
hash_from_db_2 = b'$wp$2y$10$Ks..BjKcsPdadUOBNDoG/OcoH819/flELmNCuy6RyOLMSyYyWtK9u'


def check_wordpress_password(pw: bytes, pw_hash: bytes) -> bool:
    """
    Verifies a plaintext password against a modern WordPress hash
    that starts with '$wp'.
    """
    if not pw_hash.startswith(b'$wp'):
        # This function is only for modern WordPress hashes.
        # You would need other logic for older '$P$' hashes.
        return False

    if len(pw) > 4096:
        return False

    # Strip the '$wp' prefix to get the pure bcrypt hash.
    bcrypt_hash = pw_hash[3:]

    # Step 1: Perform the exact same pre-hashing on the password attempt.
    password_to_verify = base64.b64encode(
        hmac.new(
            b'wp-sha384',
            pw.strip(),
            hashlib.sha384
        ).digest()
    )

    # Step 2: Use bcrypt's checkpw to securely compare the pre-hashed
    # password with the database hash. It handles extracting the salt.
    return bcrypt.checkpw(password_to_verify, bcrypt_hash)


# --- Example Usage ---
if check_wordpress_password(password_to_check_1, hash_from_db_1):
    print("✅ First: Password is correct!")
else:
    print("❌ First: Invalid password.")
if check_wordpress_password(password_to_check_2, hash_from_db_2):
    print("✅ Second: Password is correct!")
else:
    print("❌ Second: Invalid password.")