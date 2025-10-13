import hmac
import hashlib
import base64
import bcrypt

def hash_wordpress_password(password: str) -> bytes:
    """
    Creates a WordPress-compatible password hash using the modern
    pre-hashing (HMAC-SHA384) and bcrypt method.
    """
    if len(password) > 4096:
        return b'*'

    # Step 1: Pre-hash the password with HMAC-SHA384 and Base64 encode it.
    # The key is 'wp-sha384' and must be bytes.
    # The password must be trimmed and encoded to bytes.
    password_to_hash = base64.b64encode(
        hmac.new(
            b'wp-sha384',
            password.strip().encode('utf-8'),
            hashlib.sha384
        ).digest()
    )

    # Step 2: Pass the pre-hashed string to bcrypt.
    # bcrypt.gensalt() creates a new random salt for each hash.
    bcrypt_hash = bcrypt.hashpw(password_to_hash, bcrypt.gensalt())

    # Step 3: Add the '$wp' prefix.
    return b'$wp' + bcrypt_hash

# --- Example Usage ---
new_password = 'swadbotpass123'
hashed_password = hash_wordpress_password(new_password)
print(f"Generated Hash: {hashed_password.decode()}")