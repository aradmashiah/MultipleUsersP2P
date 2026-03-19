import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding

class Protocol:
    SHARED_KEY = b'sixteen_byte_key'
    SHARED_IV = b'sixteen_byte_iv_'

    @staticmethod
    def prepare_packet(plain_text):
        """Encrypts data and strictly appends a newline."""
        try:
            if isinstance(plain_text, str): plain_text = plain_text.encode()
            padder = sym_padding.PKCS7(128).padder()
            padded_data = padder.update(plain_text) + padder.finalize()
            cipher = Cipher(algorithms.AES(Protocol.SHARED_KEY), modes.CBC(Protocol.SHARED_IV))
            encryptor = cipher.encryptor()
            # Append \n is CRITICAL for stream splitting
            return base64.b64encode(encryptor.update(padded_data) + encryptor.finalize()) + b"\n"
        except Exception as e:
            print(f"Encryption Error: {e}")
            return b""

    @staticmethod
    def decrypt_packet(base64_data):
        """Decrypts and ignores malformed packets to prevent crashes."""
        try:
            encrypted_bytes = base64.decode(base64_data) if isinstance(base64_data, str) else base64.b64decode(base64_data)
            cipher = Cipher(algorithms.AES(Protocol.SHARED_KEY), modes.CBC(Protocol.SHARED_IV))
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(encrypted_bytes) + decryptor.finalize()
            unpadder = sym_padding.PKCS7(128).unpadder()
            return (unpadder.update(padded_data) + unpadder.finalize()).decode()
        except:
            return None