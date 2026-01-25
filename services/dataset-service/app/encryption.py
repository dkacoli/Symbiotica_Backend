# app/encryption.py
from __future__ import annotations

import os
from secrets import token_bytes

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class DatasetEncryption:
    """
    AES-256 at rest using AES-256-GCM.

    Output format (bytes):
      b"SYMB1" + nonce(12) + ciphertext+tag
    """

    MAGIC = b"SYMB1"
    NONCE_LEN = 12
    KEY_LEN = 32  # 32 bytes = AES-256 key

    def __init__(self):
        master = os.getenv("ENCRYPTION_MASTER_KEY")
        if not master or len(master) < 16:
            raise ValueError(
                "ENCRYPTION_MASTER_KEY must be set (>=16 chars). "
                "Put it in your .env and docker-compose env."
            )
        self.master_key = master

        # For a real system: generate a random salt and store it securely (not hardcoded).
        self.salt = os.getenv("ENCRYPTION_SALT", "symbiotica_salt_v1").encode("utf-8")
        self.iterations = int(os.getenv("PBKDF2_ITERATIONS", "200000"))

    def _derive_key_32(self, dataset_id: str) -> bytes:
        """Derive a 32-byte AES key using PBKDF2-HMAC-SHA256."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_LEN,
            salt=self.salt,
            iterations=self.iterations,
        )
        material = f"{self.master_key}:{dataset_id}".encode("utf-8")
        return kdf.derive(material)

    def encrypt_file(self, file_data: bytes, dataset_id: str) -> bytes:
        """Encrypt bytes with AES-256-GCM. Returns MAGIC+nonce+ciphertext."""
        key = self._derive_key_32(dataset_id)
        aesgcm = AESGCM(key)
        nonce = token_bytes(self.NONCE_LEN)
        ciphertext = aesgcm.encrypt(nonce, file_data, None)  # includes auth tag
        return self.MAGIC + nonce + ciphertext

    def decrypt_file(self, encrypted_data: bytes, dataset_id: str) -> bytes:
        """Decrypt bytes produced by encrypt_file()."""
        if not encrypted_data.startswith(self.MAGIC):
            raise ValueError("Invalid encrypted payload (missing magic header).")

        offset = len(self.MAGIC)
        nonce = encrypted_data[offset : offset + self.NONCE_LEN]
        ciphertext = encrypted_data[offset + self.NONCE_LEN :]

        key = self._derive_key_32(dataset_id)
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)
