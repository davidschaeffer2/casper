# Casper
Casper is a [discord](https://discordapp.com) bot written in python using the 
[discord.py](https://github.com/Rapptz/discord.py/tree/rewrite) library. Started as a way 
to learn python, it's evolved into a great tool used by friends.

# Build Status
Casper is under near-constant development. I try to ensure only bug-free, working builds 
are uploaded here but nobody is perfect. 

# Features
Casper comes with a variety of sub-modules such as:

### Fitness
- Allows users to track different fitness goals and share them with each other.
- Ex: `casper progress MyUsername`
- Ex: `casper setbench 225`

### Reddit
- [Subreddit](https://reddit.com) linking. If Casper detects a valid subreddit in a message,
it'll reply with a link directly to that subreddit as long as it's not part of a URL.

### (World of) Warcraft
- World of Warcraft character profiles and character stats. 


# Installation
You'll need to [setup your own bot credentials](https://discordapp.com/developers/applications/)
and dump them into a config.py file in the root directory. Ex:
```
class DiscordAPI:
    CLIENTID = 'client_id'
    CLIENTSECRET = 'client_secret'
    TOKEN = 'client_token'
    OWNERID = owner_id
```

You'll also need to add API credentials to the same config file:
```
class RedditAPI:
    CLIENTID = 'client_id'
    CLIENTSECRET = 'client_secret'
    USERPASS = 'account_password'
    USERNAME = 'account_name'
    AUTH_ENDPOINT = 'https://www.reddit.com/api/v1/access_token'
```

as well as Blizzard API credentials:
```
class WarcraftAPI:
    API_CLIENTID = 'client_id'
    API_CLIENTSECRET = 'client_secret'
```

Once done, it's just a matter of running it. `python casper.py`

# License
MIT License

Copyright (c) 2017-2019 David Schaeffer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.