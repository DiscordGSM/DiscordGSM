import os
import base64

from settings import Settings

settings = Settings.get()
TOKEN = os.getenv('DGSM_TOKEN', settings['token'])

# validate token
segs = TOKEN.split('.')
assert len(segs) == 3, "invalid token"

botid = base64.b64decode(segs[0]).decode()
print(f"https://discord.com/api/oauth2/authorize?client_id={botid}&permissions=26894704&scope=bot")
