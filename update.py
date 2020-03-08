import os
import re
import requests
import shutil
import zipfile
from distutils.dir_util import copy_tree

# get local version
with open('bot.py', 'r') as file:
    text = file.read()
local_version = re.findall("VERSION = '(.*?)'", text)
local_version = 'v' + local_version[0]
print(f'Local version:\n{local_version}')

# get remote version
url = 'https://api.github.com/repos/DiscordGSM/DiscordGSM/releases/latest'
r = requests.get(url)
remote_version = re.findall('tag_name":"(.*?)"', r.text)
remote_version = remote_version[0]
print(f'Latest version:\n{remote_version}\n')

if local_version == remote_version:
    print(f'DiscordGSM is up to date.')
else:
    response = input(f'{remote_version} is available, do you want to update DiscordGSM? [Y/n] ') or 'Y'
    if response.upper() == 'Y':
        if not os.path.exists("temp"):
            os.mkdir('temp')

        # download discordgsm   
        print(f'Download latest DiscordGSM...')
        download_url = f'https://github.com/DiscordGSM/DiscordGSM/archive/{remote_version}.zip'
        with open('temp/DiscordGSM.zip', 'wb') as file:
            r = requests.get(download_url)
            file.write(r.content)

        # download zip
        with zipfile.ZipFile('temp/DiscordGSM.zip', 'r') as zip_ref:
            zip_ref.extractall('temp')

        # remove zip
        os.remove('temp/DiscordGSM.zip')

        # backup configs file
        print(f'Copy config files...')
        files = os.listdir('temp')
        remote_dir = f'temp/{files[0]}'
        copy_tree('configs', f'{remote_dir}/configs')

        # copy backup
        copy_tree(remote_dir, '')

        # delete temp
        shutil.rmtree('temp')

        print(f'Discord updated successfully.')

input("\nPress Enter to continue...")