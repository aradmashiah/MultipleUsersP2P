import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding

class Protocol:
    # In a mesh, everyone uses the same 'Room Key' to communicate
    SHARED_KEY = b'sixteen_byte_key'
    SHARED_IV = b'sixteen_byte_iv_'

    @staticmethod
    def prepare_packet(plain_text):
        """Encrypts a string into a base64 packet ending with a newline."""
        encrypted = Protocol._encrypt_aes_to_base64(plain_text, Protocol.SHARED_KEY, Protocol.SHARED_IV)
        return encrypted + b"\n"

    @staticmethod
    def _encrypt_aes_to_base64(plain_text, key, iv):
        if isinstance(plain_text, str): plain_text = plain_text.encode()
        padder = sym_padding.PKCS7(128).padder()
        padded_data = padder.update(plain_text) + padder.finalize()
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        return base64.b64encode(encryptor.update(padded_data) + encryptor.finalize())

    @staticmethod
    def _decrypt_aes_from_base64(base64_data, key, iv):
        encrypted_bytes = base64.b64decode(base64_data)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted_bytes) + decryptor.finalize()
        unpadder = sym_padding.PKCS7(128).unpadder()
        return (unpadder.update(padded_data) + unpadder.finalize()).decode()