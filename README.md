# DiscordGSM
![screenshot](https://github.com/BattlefieldDuck/DiscordGSM/raw/master/images/online.png)

## Introduction
Monitor your game servers on Discord, tracking your game servers live data. Python 3.6 is used.

## Installing
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/BattlefieldDuck/DiscordGSM)

## Commands
`!dgsm` `!serveradd <type> <game> <addr> <port> <channel>` `!serverdel <id>` `!servers` `!serversrefresh`

## Get Started
1. Create two text channels - `server-list`, `temp`

    ![screenshot](https://github.com/BattlefieldDuck/DiscordGSM/raw/master/images/server-list.png)

2. Switch to `temp` channel, add servers by `!serveradd` command, channel id can be get by `Copy ID`

    ![screenshot](https://github.com/BattlefieldDuck/DiscordGSM/raw/master/images/copy-id.png)

    Usage: ```!serveradd <type> <game> <addr> <port> <channel>```

    Example: ```!serveradd "SourceQuery" "Team Fortress 2" "123.456.789.0" 27015 680901361659150526```

3. Refresh server list by `!serversrefresh` command, in `server-list` channel should display the server messages.
4. Delete `temp` channel
