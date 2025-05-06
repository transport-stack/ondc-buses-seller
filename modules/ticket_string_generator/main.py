import base64
import hashlib
import json
import logging
import os

from cryptography.fernet import Fernet


def json_to_base64(json_data):
    json_string = json.dumps(json_data)
    json_bytes = json_string.encode('utf-8')
    base64_string = base64.b64encode(json_bytes).decode('utf-8')
    # logging.info(f"JSON converted to base64 successfully: {base64_string}")
    return base64_string


def generate_key() -> bytes:
    """
    Generates a secure key using the salt.

    :return: A 32-byte encryption key.
    """
    salt = os.getenv("HASHING_SALT")
    key = hashlib.sha256(salt.encode()).digest()  # Convert salt to 32-byte key
    return base64.urlsafe_b64encode(key)


def encrypt_with_salt(data: str) -> str:
    """
    Encrypts a given string using a salt.

    :param data: The string to be encrypted.
    :return: Encrypted string.
    """
    key = generate_key()  # Generate encryption key
    cipher = Fernet(key)  # Create cipher object
    encrypted_data = cipher.encrypt(data.encode())  # Encrypt data
    return encrypted_data.decode()  # Return encrypted string


def decrypt_with_salt(encrypted_data: str):
    """
    Decrypts an encrypted string using the same salt.

    :param encrypted_data: The encrypted string.
    :return: Dictionary containing extracted ticket or pass details.
    """
    try:
        if not encrypted_data or not isinstance(encrypted_data, str):
            raise ValueError("Invalid encrypted data provided.")

        key = generate_key()  # Generate encryption key
        cipher = Fernet(key)  # Create cipher object

        try:
            decrypted_data = cipher.decrypt(encrypted_data.encode())  # Attempt decryption
            print(f"Decrypted data: {decrypted_data}")
        except Exception as decrypt_error:
            raise ValueError("Invalid QR") from decrypt_error

        if not decrypted_data:
            raise ValueError("No data found")

        parts = decrypted_data.decode().split('#')

        if len(parts) > 2:
            return {parts[1]: parts[2]}  # Expected output {"ticket": <pnr>} or {"pass": <pnr>}
        else:
            raise ValueError("Data format is invalid.")

    except ValueError as ve:
        logging.error(f"ValueError: {ve}")
        raise ve
    except Exception as e:
        logging.error(f"Unexpected error in decryption: {e}")
        raise RuntimeError("An unexpected error occurred during decryption.") from e
