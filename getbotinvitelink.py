import os
import base64

TOKEN = os.getenv('DGSM_TOKEN')

# validate token
segs = TOKEN.split('.')
assert len(segs) == 3, "invalid token"

clientid = base64.b64decode(segs[0]).decode()
print(f"https://discord.com/api/oauth2/authorize?client_id={clientid}&permissions=339008&scope=bot")
