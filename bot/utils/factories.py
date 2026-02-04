import hmac
import hashlib

def generate_telegram_oauth_hash(data: dict, bot_token: str):
    secret = hashlib.sha256(bot_token.encode()).digest()
    check_string = '\n'.join([f"{k}={v}" for k, v in sorted(data.items())])
    hash = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    return hash