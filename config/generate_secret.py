import secrets

key_bytes = secrets.token_bytes(32)
hex_key   = key_bytes.hex()
print(hex_key)  # 64 hex characters = 256 bits