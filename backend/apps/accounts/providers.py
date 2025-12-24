from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider

class TelegramAccount(ProviderAccount):
    pass

class TelegramProvider(OAuth2Provider):
    id = 'telegram'
    name = 'Telegram'
    account_class = TelegramAccount

    def extract_uid(self, data):
        return str(data["id"])
    
    def default_scope(self):
        return ['auth']
    
provider_classes = [TelegramProvider]