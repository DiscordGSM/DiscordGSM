# DiscordGSM
![screenshot](https://github.com/BattlefieldDuck/DiscordGSM/raw/master/images/thumbnail.png)

## Introduction
Monitor your game servers on Discord, tracking your game servers live data. Python 3.6 is used.

## Installing
| Branch | Heroku Deploy  |
| ------ | -------------- |
| master | [![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy) |
| v1.0.0 | [![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/BattlefieldDuck/DiscordGSM/tree/v1.0.0) |

### After Deploy
1. Click Configure Dynos
    
    ![screenshot](https://github.com/BattlefieldDuck/DiscordGSM/raw/master/images/conf-dyno.png)
    
2. Turn the worker on

    ![screenshot](https://github.com/BattlefieldDuck/DiscordGSM/raw/master/images/worker.png)
    
3. DiscordGSM is now online

## Commands
`!dgsm` `!serveradd <type> <game> <addr> <port> <channel>` `!serverdel <id>` `!servers` `!serversrefresh`

## Get Started - add game server
### Method 1 - By upload servers.json
1. Type `!getserversjson`, and download servers.json
2. Edit servers.json manually. Example:
```
[
    {
        "type": "SourceQuery",
        "game": "Team Fortress 2",
        "addr": "123.456.789.0",
        "port": 27010,
        "channel": 680969817200656387
    },
    {
        "type": "SourceQuery",
        "game": "Team Fortress 2",
        "addr": "123.456.789.0",
        "port": 27015,
        "channel": 680969817200656387
    }
]
```
#### Fields
`type`: type of query method, currently support `SourceQuery` only.

`game`: name of the game, it can be any string

`addr`: game server ip address

`port`: game server query port

`channel`: the channel id - the channel that display the server embed, you can get the channel id by right click the channel bar

3. Upload the servers.json to discord and copy the link by right click.

    ![screenshot](https://github.com/BattlefieldDuck/DiscordGSM/raw/master/images/uploadserversjson.png)

4. Type `!setserversjson <url>`, `<url>` is the link that you just copied

5. Refresh server list by `!serversrefresh` command, it should display the servers' details in the channels.

### Method 2 - By commands
1. Create two text channels - `server-list`, `temp`

    ![screenshot](https://github.com/BattlefieldDuck/DiscordGSM/raw/master/images/server-list.png)

2. Switch to `temp` channel, add servers by `!serveradd` command, channel id can be get by `Copy ID`

    ![screenshot](https://github.com/BattlefieldDuck/DiscordGSM/raw/master/images/copy-id.png)

    Usage: ```!serveradd <type> <game> <addr> <port> <channel>```

    Example: ```!serveradd "SourceQuery" "Team Fortress 2" "123.456.789.0" 27015 680901361659150526```

3. Refresh server list by `!serversrefresh` command, in `server-list` channel should display the server details.
4. Delete `temp` channel
