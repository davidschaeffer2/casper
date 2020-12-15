import asyncio
import random
import string
from datetime import datetime
from pprint import pprint
from urllib import parse

import discord
from discord.ext import commands, tasks
from ratelimiter import RateLimiter

from utilities import Utilities
from cogs.warcraft.warcraft_character_iface import WarcraftCharacterInterface
from cogs.warcraft.weekly_gulld_runs_iface import WeeklyGuildRunsInterface
from config import WarcraftAPI


class Warcraft(commands.Cog):
    def __init__(self, casper):
        self.casper = casper
        self.guild_name = 'felforged'
        self.guild_realm = 'wyrmrest-accord'
        self.region = 'us'

        self.aiohttp_session = casper.aiohttp_session

        self.blizzard_region_namespaces = {
            'us': 'en_US', 'eu': 'en_GB', 'kr': 'ko_KR', 'ru': 'ru_RU', 'tw': 'zh_TW',
            'sea': 'en_SG'
        }
        self.sl_dungeons = {  # Dungeon Name: (usable abbreviations)
            'De Other Side': ('dos', 'tos', 'deother', 'other', 'otherside'),
            'Halls of Atonement': ('hoa', 'halls', 'atonement', 'atone'),
            'Mists of Tirna Scithe': ('mots', 'mists', 'tirna', 'scithe'),
            'Plaguefall': ('pf', 'plague', 'plaguefall'),
            'Spires of Ascension': ('soa', 'spires', 'ascension'),
            'Sanguine Depths': ('sd', 'sang', 'sanguine', 'depths'),
            'The Necrotic Wake': ('tnw', 'nw', 'wake', 'necrotic'),
            'Theater of Pain': ('top', 'theater', 'pain'),
        }

        async def crawl_all_characters():
            """
            Gets a list of all characters from the database and then pulls updated
            information from raider.io. If the character cannot be fetched from raider.io,

            :return: None
            """
            rate_limiter = RateLimiter(max_calls=120, period=60)
            characters = await WarcraftCharacterInterface.get_all_characters()
            if len(characters) > 0:
                for character in characters:
                    try:
                        async with rate_limiter:
                            raiderio_data = await self.get_raiderio_data(
                                character.name, character.realm, character.region)
                            if raiderio_data is not None:
                                await WarcraftCharacterInterface.update_character(raiderio_data)
                                await self.log_weekly_runs(raiderio_data)
                            elif abs((datetime.now() - character.last_updated)).days > 30:
                                print(f'{character.name} removed for being old.')
                                await WarcraftCharacterInterface.remove_character(character)
                    except Exception as e:
                        print(f'Error occurred when attempting to retrieve character data '
                              f'for {character.name} during '
                              f'character crawl:\n{e}')
                        continue
            else:
                print('No characters found to update.')

        async def crawl_guild():
            rate_limiter = RateLimiter(max_calls=120, period=60)
            members = await self.get_guild_members_from_blizzard(
                    self.guild_name, self.guild_realm, self.region)
            if len(members) > 0:
                for name, realm, rank in members:
                    try:
                        async with rate_limiter:
                            raiderio_data = await self.get_raiderio_data(
                                name, realm, self.region)
                            if raiderio_data is not None:
                                await WarcraftCharacterInterface.update_character(
                                    raiderio_data, rank)
                    except Exception as e:
                        print(f'Error occurred during crawl Felforged and character '
                              f'{name}:\n{e}')
                        continue
            else:
                print('Could not fetch guild members during crawl_guild.')

        @tasks.loop(seconds=300)
        async def auto_crawl():
            """
            Auto-runs every 10 minutes. Calls two methods, crawl_all_characters and
            crawl_all_guilds. The first ensures all guild members and guild ranks are
            crawled, the latter ensures all characters are updated.

            :return: None
            """
            print('----------------------------------------')
            print(f'Crawling Felforged starting at {datetime.now()}.')
            await crawl_guild()
            print(f'Finished crawling Felforged at {datetime.now()}.')
            print('----------------------------------------')
            print('----------------------------------------')
            print(f'Crawling all characters starting at {datetime.now()}.')
            await crawl_all_characters()
            print(f'Finished crawling all characters at {datetime.now()}.')
            print('----------------------------------------')

        auto_crawl.start()

        @tasks.loop(seconds=300)
        async def weekly_reset():
            # Felforged pve channel
            ch = self.casper.get_channel(647918497342423052)
            if datetime.now().weekday() == 1 and datetime.now().hour == 10:
                if (await WarcraftCharacterInterface.reset_keys() and
                        await WeeklyGuildRunsInterface.reset_runs()):
                    await ch.send('Weekly reset, keys and weekly runs reset. Wish you '
                                  'good loot and stable connect!')
                    await asyncio.sleep(24*60*60)
                else:
                    me = await self.casper.fetch_user(213665551988293632)  # me
                    await me.send('An error occurred when attempting weekly reset.')

        weekly_reset.start()

    @commands.Cog.listener()
    async def on_message(self, message):
        stripped_msg = message.content.translate(
            str.maketrans('', '', string.punctuation)
        ).lower()
        channel = message.channel

        if message.author.id == self.casper.user.id:
            return

        # Ursola
        if message.author.id == 219924616121024512 and random.random() <= 0.01:
            # expac is gonna be lit
            await channel.send('https://i.imgur.com/Q2Defzk.png')

        # Cas
        if message.author.id == 223587679051317248 and random.random() <= 0.01:
            # buy next 6 month mount
            await channel.send('https://i.imgur.com/CsNcnnG.png')

        # Grass
        if message.author.id == 227471595470454786 and random.random() <= 0.01:
            # don't roll off ledges
            await channel.send('https://i.imgur.com/1Wi1UEy.jpg')

        if (any('ion' == word for word in stripped_msg.split()) or
                any('ions' == word for word in stripped_msg.split())) and \
                random.random() <= 0.15:
            # ion big dick energy
            await channel.send('https://i.imgur.com/jsAyl9e.gif')

        if any('anima' == word for word in stripped_msg.split()) and \
                random.random() <= 0.05:
            await channel.send('https://i.imgur.com/AG6tvqG.png')

    @commands.command(hidden=True)
    async def test(self, ctx, name):
        data = await self.get_raiderio_data(name, 'wyrmrest-accord', 'us')
        weekly_high: dict = data['mythic_plus_weekly_highest_level_runs']
        if len(weekly_high) > 0:
            #pprint(weekly_high[0])
            for dungeon in weekly_high:
                dungeon_name = dungeon['dungeon']
                dungeon_level = dungeon['mythic_level']
                dungeon_id = dungeon['url'].split('/')[5].split('-')[0]
                print(dungeon_name, dungeon_level, dungeon_id)

    @commands.command()
    async def cas(self, ctx):
        await ctx.message.delete()
        return await ctx.send('https://i.imgur.com/CsNcnnG.png')

    @commands.command()
    async def topay(self, ctx):
        await ctx.message.delete()
        return await ctx.send(
                'Hi guys, returning top 1% orange parsing mage who hasn\'t played since '
                '8.3. What\'s the best mage spec & covenent to be playing in Shadowlands '
                'if I want to be CE Mythic Raiding and pushing high keys? Assume '
                'infinite weekly playtime, high gamer IQ, and the the ability to play '
                'perfect APLs and adapt as needed. Please don\'t provide a "play what is '
                'fun" answer since what\'s fun for me is min/maxing the best performing '
                'spec with my play time.\n\n- Top, probably​')

    # region Removes response after 5 minutes
    @commands.command()
    async def wow(self, ctx, name, realm='wyrmrest-accord', region='us'):
        """
        Fetches character data from Raider.io API.

        :param ctx: Discord.py invocation context. Used for sending messages.
        :param name: Name of character
        :param realm: Name of realm, space are auto-sanitized
        :param region: 2-letter abbreviation for region - US, EU, RU, KR
        :return: A Discord Embed object populated with character data if successful,
        otherwise an error message.
        """
        msg = await ctx.send(f'Fetching data for {name.title()} on '
                             f'{realm.title().replace("-", " ")}-'
                             f'{region.upper()}.')
        raiderio_data = await self.get_raiderio_data(name, realm, region)
        if raiderio_data is None:
            await self.react_to_message(ctx.message, False)
            return await msg.edit(content=f'Could not find data for {name.title()} on '
                                          f'{realm.title().replace("-", " ")}-'
                                          f'{region.upper()} on raider.io. Ensure the '
                                          f'character has been queried there.', delete_after=300)
        # for k, v in raiderio_data.items():
        #     print(f'{k}: {v}')
        await msg.edit(content=f'Found character data, updating records.')
        try:
            await WarcraftCharacterInterface.update_character(raiderio_data)
        except Exception as e:
            await self.react_to_message(ctx.message, False)
            print(f'Error occurred during wow command character update:\n{e}')
            return await msg.edit(content='An error occurred when updating the '
                                          'character record. Sorry.', delete_after=300)
        await msg.edit(content=f'Records updated, building layout.')
        try:
            embed = await self.build_character_embed(raiderio_data)
            await self.react_to_message(ctx.message, True)
            return await msg.edit(content='', embed=embed, delete_after=300)
        except Exception as e:
            await self.react_to_message(ctx.message, False)
            print(f'Error occurred during wow command building embed:\n{e}')
            return await msg.edit(content=f'An error occurred while building '
                                          f'layout. Sorry.', delete_after=300)

    @commands.command()
    async def mplus(self, ctx, *, char_names=None):
        """
        See how many m+ you've run since start of Legion

        :param ctx:
        :param char_names:
        :return:
        """
        if char_names is None:
            await self.react_to_message(ctx.message, False)
            return await ctx.send('You must provide at least one character name. You can '
                                  'list multiple character names separated by a space.')
        msg = await ctx.send(f'Fetching character data...')
        out_msg = (f'```{"Name:":<{14}}{"M+ Run: (since Legion)":<{5}}\n'
                   f'-------------------------------\n')
        total = 0
        try:
            for char in char_names.split(' '):
                criteria_resp = await self.get_blizzard_achieve_statistics_data(
                    char, 'wyrmrest-accord', 'us')
                # Bro, this is gross
                if criteria_resp is not None:
                    for section in criteria_resp['categories']:
                        if section['name'] == 'Dungeons & Raids':
                            for subsection in section['statistics']:
                                if subsection['id'] == 7399:
                                    total += int(subsection["quantity"])
                                    out_msg += (f'{char.title():<{14}}'
                                                f'{int(subsection["quantity"])}\n')
            out_msg += (f'-------------------------------\n'
                        f'{"Total:":<{13}}{total:{5}}```')
            await self.react_to_message(ctx.message, True)
            return await msg.edit(content=out_msg, delete_after=300)
        except Exception as e:
            print(f'Mplus command messed up:\n{e}')
            await self.react_to_message(ctx.message, False)
            return await ctx.send('Sorry, an error occurred when collecting data.',
                                  delete_after=300)

    @commands.command(aliases=['rc'])
    async def readycheck(self, ctx, sort_by='rank', ranks='0,1,3,6'):
        """
        Outputs a subset of guild members specified by rank with information on class,
        Heart of Azeroth level, weekly highest mythic+ completed, ilvl, and previous
        week's highest mythic+ completed.

        :param ctx: Discord.py invocation context. Used for sending messages.
        :param sort_by: rank (default), name, class, hoa, mplus, ilvl
        :param ranks: A comma-separated string of integer ranks to filter by
        :return: A layout of character information if successful, otherwise an error
        message
        """
        try:
            rank = int(ranks[0])  # really used as a data type check, nothing more
        except AttributeError as e:
            await self.react_to_message(ctx.message, False)
            return await ctx.send(f'Ranks must be given as their numerical values as '
                                  f'depicted on the armory. 0 for GM, 1 for Officers, '
                                  f'and so on to 7 separated by a comma:\n'
                                  f'Example: 0,2,4,5', delete_after=300)
        msg = await ctx.send(f'Fetching members for '
                             f'{self.guild_name.replace("-", "").title()} '
                             f'on {self.guild_realm.replace("-", " ").title()}'
                             f'-{self.region.upper()}.')
        guild_members = await WarcraftCharacterInterface.get_guild_members(
            self.guild_name, self.guild_realm, self.region, ranks)
        await msg.edit(content=f'Members found. Building layout.')
        output = await self.build_readycheck_msg(guild_members, sort_by)
        await self.react_to_message(ctx.message, True)
        return await msg.edit(content=output, delete_after=300)

    @commands.command()
    async def scores(self, ctx, num=10):
        """
        Outputs a scoreboard for character mythic+ scores, limited to characters found in
        the default guild for the discord server.

        :param ctx: Discord.py invocation context. Used for sending messages.
        :param num: The number of characters to show, caps at 25 for message character
        count limitations
        :return: An output with the scores of characters if successful, otherwise an error
         message
        """
        msg = await ctx.send(f'Fetching scores for the top {num} characters in the guild.')
        characters = await WarcraftCharacterInterface.get_guild_members(
            self.guild_name, self.guild_realm, self.region)
        await msg.edit(content=f'Building layout.')
        output = await self.build_scores_msg(characters, num)
        await self.react_to_message(ctx.message, True)
        return await msg.edit(content='', embed=output, delete_after=300)

    @commands.command(aliases=['abb', 'abbs', 'abs', 'dungeons'])
    async def abbreviations(self, ctx):
        """
        See available abbreviations for Shadowlands dungeons

        :param ctx:
        :return:
        """
        out_msg = 'Please use one of the following abbreviations for dungeons:\n\n'
        for dungeon, abbs in self.sl_dungeons.items():
            abbreviations = ', '.join(abbs)
            out_msg += f'**{dungeon}**: {abbreviations}\n'
        await self.react_to_message(ctx.message, True)
        return await ctx.send(out_msg, delete_after=300)

    @commands.command(aliases=['ak'])
    async def addkey(self, ctx, name, key_info=None):
        """
        Adds a mythic+ key to a character.

        :param ctx: Discord.py invocation context. Used for sending messages.
        :param name: Character name
        :param key_info: Key info formatted as dungeon_abbreviation+key_level
        :return: The list of current mythic+ keys for the default guild of the discord
        server if successful, otherwise an error message
        """
        if key_info is None:
            return await ctx.send('Please format your key info as:\n'
                                  '`casper addkey allikazam fh+18`')
        if '+' not in key_info:
            return await ctx.send('Please format your key info as:\n'
                                  '`casper addkey allikazam fh+18`')
        try:
            # Grab the dungeon name from the SL Dungeons dict if the abbreviation
            # used is found in the tuple of values
            key = [dungeon_name[0] for dungeon_name in self.sl_dungeons.items()
                   if key_info.split('+')[0].lower() in dungeon_name[1]][0]
            key_level = int(key_info.split('+')[1])
        except Exception as e:
            print(f'Error occurred when parsing dungeon info:\n{e}')
            out_msg = 'Please use one of the following abbreviations for dungeons:\n\n'
            for dungeon, abbs in self.sl_dungeons.items():
                abbreviations = ', '.join(abbs)
                out_msg += f'**{dungeon}**: {abbreviations}\n'
            return await ctx.send(out_msg, delete_after=300)
        character = await WarcraftCharacterInterface.get_character(
            name, self.guild_realm, self.region)
        if character is None:
            await self.react_to_message(ctx.message, False)
            return await ctx.send(f'Could not find character by name of: {name.title()}.'
                                  f'Please try using the `wow` command to scan your '
                                  f'character.', delete_after=300)
        await WarcraftCharacterInterface.addkey(character, key, key_level)
        return await self.react_to_message(ctx.message, True)

    @commands.command(aliases=['rk'])
    async def removekey(self, ctx, name=None):
        """

        :param ctx: Discord.py invocation context. Used for sending messages.
        :param name: Character name
        :return: A message with the outcome of the key removal
        """
        if name is None:
            return await ctx.send('Please format your command as:\n'
                                  '`casper removekey allikazam`')
        character = await WarcraftCharacterInterface.get_character(
            name, self.guild_realm, self.region)
        if character is None:
            await self.react_to_message(ctx.message, False)
            return await ctx.send(f'Could not find character by name of: {name.title()}. '
                                  f'This message will delete itself in 30 seconds.',
                                  delete_after=300)
        await WarcraftCharacterInterface.removekey(character)
        return await self.react_to_message(ctx.message, True)

    @commands.command()
    async def remove(self, ctx, name):
        """
        Used to remove characters from the database that may no longer exist.

        :param ctx: Discord.py invocation context. Used for sending messages.
        :param name: Character name
        :return: A message with the outcome of the character removal
        """
        character = await WarcraftCharacterInterface.get_character(
            name, self.guild_realm, self.region)
        if character is None:
            await self.react_to_message(ctx.message, False)
            return await ctx.send(f'Could not find character by name of: {name.title()}.',
                                  delete_after=300)
        await WarcraftCharacterInterface.remove_character(character)
        return await self.react_to_message(ctx.message, True)
    # endregion

    # region Leaves response
    @commands.command()
    async def callout(self, ctx, ranks='0,1,3,6'):
        """
        Outputs a message with a list of characters who did not run a mythic+ of 15 or
        higher.

        :param ctx: Discord.py invocation context. Used for sending messages.
        :param ranks: A comma-separated string of integer ranks to filter by
        :return: An output with the offending characters
        """
        msg = await ctx.send(f'Fetching members for '
                             f'{self.guild_name.replace("-", "").title()} '
                             f'on {self.guild_realm.replace("-", " ").title()}'
                             f'-{self.region.upper()}.')
        guild_members = await WarcraftCharacterInterface.get_guild_members(
            self.guild_name, self.guild_realm, self.region, ranks)
        await msg.edit(content=f'Members found. Building layout.')
        output = await self.build_callout_msg(guild_members)
        await self.react_to_message(ctx.message, True)
        return await msg.edit(content=output)

    @commands.command()
    async def weeklyruns(self, ctx, name, count=4):
        """
        View all the weekly m+ runs done by a character.

        :param ctx: Invoking context
        :param name: Name of the character to look up
        :param count: Max number of runs to return, default 4, max 10.
        :return: An embed with dungeons sorted high to low
        """
        runs = await WeeklyGuildRunsInterface.get_player_runs(name.lower())
        if count > 10:
            count = 10
        embed = await self.build_weeklyruns_embed(name, runs, count)
        return await ctx.send(embed=embed)

    @commands.command()
    async def keys(self, ctx):
        """
        Fetches a list of characters with mythic+ key information.

        :param ctx: Discord.py invocation context. Used for sending messages.
        :return: An output of mythic+ key information
        """
        guild_keys_output = await self.build_guild_keys_msg(
            await WarcraftCharacterInterface.get_guild_keys(
                self.guild_name, self.guild_realm, self.region))
        await self.react_to_message(ctx.message, True)
        return await ctx.send(guild_keys_output)

    @commands.command()
    async def token(self, ctx):
        """
        Fetches the price for a Blizzard token.

        :param ctx: Discord.py invocation context. Used for sending messages.
        :return: A message containing the price of a token if successful, otherwise an
        error message.
        """
        region = 'us'
        token = await self.get_blizzard_access_token()
        api_url = (f'https://{region.lower()}.api.blizzard.com/data/wow/token/index?'
                   f'namespace=dynamic-us'
                   f'&locale=en_US'
                   f'&access_token={token["access_token"]}')
        response = await Utilities(self.aiohttp_session).json_get(api_url)
        try:
            price = int((response['price'] / 100) / 100)
            await self.react_to_message(ctx.message, True)
            return await ctx.send(f'The price of a token for the {region.upper()} '
                                  f'costs: {price:,} gold.')
        except AttributeError as e:
            await self.react_to_message(ctx.message, False)
            print(f'An error occurred when fetching token price:\n{e}')
            return await ctx.send('Could not fetch token price at this time. Please try '
                                  'again later.')

    @commands.command()
    async def affixes(self, ctx):
        """
        Display this week's current m+ affixes.

        :param ctx:
        :return:
        """
        affix_resp = await self.get_affixes()
        try:
            affix_details = affix_resp['affix_details']
            out_msg = ''
            for affix in affix_details:
                out_msg += (f'**__{affix["name"]}__**:\n'
                            f'{affix["description"]}\n\n')
            await self.react_to_message(ctx.message, True)
            return await ctx.send(out_msg)
        except Exception as e:
            print(f'An error occurred when attempting to fetch the affixes.\n{e}')
            await self.react_to_message(ctx.message, False)

    @commands.command()
    async def vault(self, ctx):
        return await ctx.send(
            'The weekly vault works as such:\n\n'
            'Running a single m+ rewards a single piece of gear based on the level of '
            'that dungeon.\n'
            'Running four (4) m+ will reward a second piece of gear based on the 4th '
            'highest dungeon you\'ve run this week.\n'
            'Running ten (10) m+ will reward a third piece of gear based on the 10th '
            'highest dungeon you\'ve run this week.\n\n'
            'For example, if you run four (4) dungeons at +15, +12, +14, +15, the first '
            'piece of gear in the vault will be a +15 piece, the second will be a +12 '
            'piece (no matter what order you did those keys in).\n'
            'If you run ten dungeons (first, get some help) at +3, +14, +10, +15, +15, '
            '+8, +12, +11, +15, +14, the first piece of gear will be a +15 piece, the '
            'second piece of gear will be a +14 piece, and the third piece of gear will '
            'be a +3 piece.\n\n'
        )
    # endregion

    # region Administrative commands
    @commands.command(hidden=True)
    async def removeall(self, ctx):
        if ctx.author.id != self.casper.owner_id:
            return
        characters = await WarcraftCharacterInterface.get_all_characters()
        characters = [character for character in characters
                      if character.guild is not 'felforged']
        for char in characters:
            await WarcraftCharacterInterface.remove_character(char)
        return await self.react_to_message(ctx.message, True)

    @commands.command(hidden=True)
    async def removeguild(self, ctx, guild_name, realm='wyrmrest-accord', region='us'):
        """
        Used to remove guilds from the database that may no longer exist.

        :param ctx: Discord.py invocation context. Used for sending messages.
        :param guild_name: Guild name, space are auto-sanitized
        :param realm: Realm name, spaces are auto-sanitized
        :param region: 2-letter abbreviation for region - US, EU, RU, KR
        :return: A message with the outcome of the guild removal
        """
        if ctx.author.id != self.casper.owner_id:
            return
        guild_members = await WarcraftCharacterInterface.get_guild_members(
            guild_name, realm, region)
        if len(guild_members) == 0:
            await self.react_to_message(ctx.message, False)
            return await ctx.send(f'Could not find guild by name of: {guild_name.title()}.')
        for character in guild_members:
            await WarcraftCharacterInterface.remove_character(character)
        return await self.react_to_message(ctx.message, True)
    # endregion

    # region Cog Logic
    @staticmethod
    async def react_to_message(msg, is_successful):
        """
        Reacts to a message with a white checkmark in a green box if action was a
        success, otherwise reacts with a red cross mark

        :param msg: The message to add the reaction to.
        :param is_successful: True/False if the action was a success.
        :return:
        """
        if is_successful:
            return await msg.add_reaction('\U00002705')  # white checkmark in green box
        return await msg.add_reaction('\U0000274c')  # red cross mark X

    async def get_blizzard_access_token(self):
        """
        Fetched an access token for use with Blizzard API.

        :return: A Blizzard access token if successful, otherwise None
        """
        url = (f'https://us.battle.net/oauth/token?grant_type='
               f'client_credentials&client_id={WarcraftAPI.API_CLIENTID}'
               f'&client_secret={WarcraftAPI.API_CLIENTSECRET}')
        try:
            token = await Utilities(self.aiohttp_session).json_get(url)
            return token
        except KeyError as e:
            print(f'Error attempting to generate access token:\n{e}')
            return None

    # TODO: UNUSED
    async def get_blizzard_data(self, name, realm, region):
        """
        Fetches character information from Blizzard API.

        :param name: Character name
        :param realm: Realm name, space are auto-sanitized
        :param region: 2-letter abbreviation for region - US, EU, RU, KR
        :return: Character information from Blizzard API if successful, otherwise None
        """
        token = await self.get_blizzard_access_token()
        if token is not None:
            url = (f'https://{region.lower()}.api.blizzard.com/profile/wow/character/'
                   f'{realm.lower()}/{parse.quote(name.title())}'
                   f'?namespace=profile-us&locale=en_US'
                   f'&access_token={token["access_token"]}')
            return await Utilities(self.aiohttp_session).json_get(url)
        else:
            return None

    # TODO: UNUSED
    async def get_blizzard_achieve_data(self, name, realm, region):
        """
        Fetches character information from Blizzard API.

        :param name: Character name
        :param realm: Realm name, space are auto-sanitized
        :param region: 2-letter abbreviation for region - US, EU, RU, KR
        :return: Character information from Blizzard API if successful, otherwise None
        """
        token = await self.get_blizzard_access_token()
        if token is not None:
            url = (f'https://{region.lower()}.api.blizzard.com/profile/wow/character/'
                   f'{realm.lower()}/{parse.quote(name.title())}/achievements'
                   f'?namespace=profile-us&locale=en_US'
                   f'&access_token={token["access_token"]}')
            return await Utilities(self.aiohttp_session).json_get(url)
        else:
            return None

    async def get_blizzard_achieve_statistics_data(self, name, realm, region):
        """
        Fetches character information from Blizzard API.

        :param name: Character name
        :param realm: Realm name, space are auto-sanitized
        :param region: 2-letter abbreviation for region - US, EU, RU, KR
        :return: Character information from Blizzard API if successful, otherwise None
        """
        token = await self.get_blizzard_access_token()
        if token is not None:
            url = (f'https://{region.lower()}.api.blizzard.com/profile/wow/character/'
                   f'{realm.lower()}/{parse.quote(name.title())}/achievements/statistics'
                   f'?namespace=profile-us&locale=en_US'
                   f'&access_token={token["access_token"]}')
            return await Utilities(self.aiohttp_session).json_get(url)
        else:
            return None

    async def get_raiderio_data(self, name, realm, region):
        """
        Fetches character information from Raider.io API

        :param name: Character name
        :param realm: Realm name, spaces are auto-sanitized
        :param region: 2-letter abbreviation for region - US, EU, RU, KR
        :return: The returned Raider.io data
        """
        url = (f'https://raider.io/api/v1/characters/profile?region={region.lower()}'
               f'&realm={realm.replace(" ", "-").lower()}'
               f'&name={parse.quote(name)}'
               f'&fields=gear,corruption,guild,raid_progression,mythic_plus_ranks,'
               f'mythic_plus_recent_runs,mythic_plus_highest_level_runs,'
               f'mythic_plus_weekly_highest_level_runs,'
               f'mythic_plus_previous_weekly_highest_level_runs,'
               f'mythic_plus_scores_by_season:current')
        return await Utilities(self.aiohttp_session).json_get(url)

    async def get_raiderio_guild_data(self, name, realm, region):
        url = (f'https://raider.io/api/v1/guilds/profile?'
               f'region={region.lower()}&realm={realm.replace(" ", "-").lower()}'
               f'&name={parse.quote(name.replace("-", " "))}'
               f'&fields=raid_progression,raid_rankings')
        return await Utilities(self.aiohttp_session).json_get(url)

    async def get_guild_members_from_blizzard(self, guild_name, realm, region):
        """
        Fetches all guild members for a guild from the Blizzard API.

        :param guild_name: Name of guild, spaces are auto-sanitized
        :param realm: Realm name, spaces are auto-sanitized
        :param region: 2-letter abbreviation for region - US, EU, RU, KR
        :return: A list of character information containing name, realm, and guild rank
        if successful, otherwise None
        """
        token = await self.get_blizzard_access_token()
        if token is not None:
            try:
                url = (f'https://{region.lower()}.api.blizzard.com/data/wow/guild/'
                       f'{realm.lower()}/'
                       f'{parse.quote(guild_name.replace("-", " ")).lower()}'
                       f'/roster?namespace=profile-us&locale=en_US'
                       f'&access_token={token["access_token"]}')
                results = await Utilities(self.aiohttp_session).json_get(url)
                if results is None:
                    return None
                members = []
                for member in results['members']:
                    if 'realm' in member['character'] and \
                            (50 <= member['character']['level'] <= 60):
                        members.append((member['character']['name'],
                                        member['character']['realm']['slug'],
                                        member['rank']))
                return members
            except AttributeError as e:
                print(f'Error occurred when retrieving guild members for:\n'
                      f'Guild: {guild_name}\n'
                      f'Error: {e}')
                pass
            return None

    async def get_affixes(self):
        url = 'https://raider.io/api/v1/mythic-plus/affixes?region=us&locale=en'
        return await Utilities(self.aiohttp_session).json_get(url)

    @staticmethod
    async def log_weekly_runs(raiderio_data):
        for dungeon in raiderio_data['mythic_plus_weekly_highest_level_runs']:
            dungeon_name = dungeon['dungeon']
            dungeon_level = dungeon['mythic_level']
            run_id = dungeon['url'].split('/')[5].split('-')[0]
            await WeeklyGuildRunsInterface.add_run(
                run_id, raiderio_data['name'], dungeon_name, dungeon_level
            )

    async def build_character_embed(self, r):  # r is raiderio_data
        """
        Builds a Discord Embed object with character information.

        :param r: A list of Raider.io data returned via API
        :return: A Discord Embed object with character information
        """
        embed = discord.Embed()
        embed.set_thumbnail(url=r['thumbnail_url'])
        embed.title = f'__{r["name"]}__'
        guild_name = ''
        if r['guild'] is not None:
            guild_name = f'<{r["guild"]["name"]}>'

        # CHARACTER BASICS
        embed.add_field(
            name=f'{guild_name} {r["realm"]}-{r["region"].upper()}',
            value=(f'{r["race"]} {r["active_spec_name"]} {r["class"]}\n'
                   f'**ilvl:** {r["gear"]["item_level_equipped"]}\n'
                   f'[Armory](https://worldofwarcraft.com/en-us/character/'
                   f'{r["realm"].lower().replace(" ", "-")}/{r["name"].lower()}) - '
                   f'[Raider.io](https://raider.io/characters/{r["region"].lower()}'
                   f'/{r["realm"].lower().replace(" ", "-")}/{r["name"].lower()})'),
            inline=False
        )

        # RAID PROGRESSION
        raids = r["raid_progression"]
        try:
            embed.add_field(
                name='__**Raid Progression:**__',
                value=(f'**CN:** {raids["castle-nathria"]["summary"]:{12}}'),
                inline=False
            )
        except Exception as e:
            print(f'Error occurred during wow command building embed, raid progression '
                  f'section:\n{e}')
            embed.add_field(
                name='__**Raid Progression:**__',
                value=(f'Could not fetch raid progression at this time.'),
                inline=False
            )

        # MYTHIC+ PROGRESSION
        season_highs = r['mythic_plus_highest_level_runs']
        if len(season_highs) > 0:
            scores = r['mythic_plus_scores_by_season'][0]['scores']
            ranks = r['mythic_plus_ranks']

            # OVERALL MYTHIC+ PROGRESSION
            mins, secs = divmod(season_highs[0]['clear_time_ms']/1000, 60)
            embed.add_field(
                name='__**Mythic+ Progression:**__',
                value=(f'**Current Season Score:** {scores["all"]}\n'
                       f'**Realm Rank:** #{ranks["overall"]["realm"]:,} '
                       f'(#{ranks["class"]["realm"]:,} {r["class"]})\n'
                       f'Season Best: {season_highs[0]["dungeon"]}+'
                       f'{season_highs[0]["mythic_level"]} cleared in '
                       f'{mins}:{secs:.1f} upgrading the key '
                       f'{season_highs[0]["num_keystone_upgrades"]} times for '
                       f'a score of {season_highs[0]["score"]}.\n'
                       f'[Run Info]({season_highs[0]["url"]})'),
                inline=False
            )

            # WEEKLY MYTHIC+ PROGRESSION
            weekly_highs = r['mythic_plus_weekly_highest_level_runs']
            recent_highs = r['mythic_plus_recent_runs']
            if len(weekly_highs) > 0:
                mins, secs = divmod(weekly_highs[0]["clear_time_ms"] / 1000, 60)
                embed.add_field(name='__**Weekly High Mythic+ Run:**__',
                                value=f'{weekly_highs[0]["dungeon"]}+'
                                      f'{weekly_highs[0]["mythic_level"]} '
                                      f'cleared in {mins}:{secs:.1f} upgrading '
                                      f'the key '
                                      f'{weekly_highs[0]["num_keystone_upgrades"]} '
                                      f'time(s) for a score of '
                                      f'{weekly_highs[0]["score"]}.\n'
                                      f'[Run Info]({weekly_highs[0]["url"]})',
                                inline=False)
                await self.log_weekly_runs(r)

            # MOST RECENT MYTHIC+ PROGRESSION
            elif len(recent_highs) > 0:
                mins, secs = divmod(recent_highs[0]["clear_time_ms"] / 1000, 60)
                embed.add_field(
                    name=('__**Most Recent Mythic+ Run:**__ '
                          '(No run found this week)'),
                    value=f'{recent_highs[0]["dungeon"]} '
                          f'+{recent_highs[0]["mythic_level"]} cleared in '
                          f'{mins}:{secs:.1f} upgrading the key '
                          f'{recent_highs[0]["num_keystone_upgrades"]} '
                          f'time(s) for a score of '
                          f'{recent_highs[0]["score"]}.\n'
                          f'[Run Info]({recent_highs[0]["url"]})',
                    inline=False)
        else:
            embed.add_field(
                name='__**Mythic+ Progression:**__',
                value='No mythic+ data exists for this character.',
                inline=False
            )
        return embed

    @staticmethod
    async def build_guild_embed(r):
        embed = discord.Embed()
        embed.title = f'__{r["name"]}__'
        embed.add_field(name=(f'{r["faction"].title()} on '
                              f'{r["realm"]}-{r["region"].upper()}'),
                        value=f'[Raider.io]({r["profile_url"]})',
                        inline=False)
        rr = r['raid_rankings']
        rp = r['raid_progression']
        embed.add_field(name=f'__**Uldir:**__',
                        value=(f'**N: {rp["uldir"]["normal_bosses_killed"]}/{rp["uldir"]["total_bosses"]}** '
                               f'(Realm #{rr["uldir"]["normal"]["realm"]})\n'
                               f'**H: {rp["uldir"]["heroic_bosses_killed"]}/{rp["uldir"]["total_bosses"]}** '
                               f'(Realm #{rr["uldir"]["heroic"]["realm"]})\n'
                               f'**M: {rp["uldir"]["mythic_bosses_killed"]}/{rp["uldir"]["total_bosses"]}** '
                               f'(Realm #{rr["uldir"]["mythic"]["realm"]})\n'),
                        inline=False)
        embed.add_field(name=f'__**Battle of Dazaralor:**__',
                        value=(f'**N: {rp["battle-of-dazaralor"]["normal_bosses_killed"]}/{rp["battle-of-dazaralor"]["total_bosses"]}** '
                               f'(Realm #{rr["battle-of-dazaralor"]["normal"]["realm"]})\n'
                               f'**H: {rp["battle-of-dazaralor"]["heroic_bosses_killed"]}/{rp["battle-of-dazaralor"]["total_bosses"]}** '
                               f'(Realm #{rr["battle-of-dazaralor"]["heroic"]["realm"]})\n'
                               f'**M: {rp["battle-of-dazaralor"]["mythic_bosses_killed"]}/{rp["battle-of-dazaralor"]["total_bosses"]}** '
                               f'(Realm #{rr["battle-of-dazaralor"]["mythic"]["realm"]})\n'),
                        inline=False)
        embed.add_field(name=f'__**Crucible of Storms:**__',
                        value=(f'**N: {rp["crucible-of-storms"]["normal_bosses_killed"]}/{rp["crucible-of-storms"]["total_bosses"]}** '
                               f'(Realm #{rr["crucible-of-storms"]["normal"]["realm"]})\n'
                               f'**H: {rp["crucible-of-storms"]["heroic_bosses_killed"]}/{rp["crucible-of-storms"]["total_bosses"]}** '
                               f'(Realm #{rr["crucible-of-storms"]["heroic"]["realm"]})\n'
                               f'**M: {rp["crucible-of-storms"]["mythic_bosses_killed"]}/{rp["crucible-of-storms"]["total_bosses"]}** '
                               f'(Realm #{rr["crucible-of-storms"]["mythic"]["realm"]})\n'),
                        inline=False)
        embed.add_field(name=f'__**The Eternal Palace:**__',
                        value=(f'**N: {rp["the-eternal-palace"]["normal_bosses_killed"]}/{rp["the-eternal-palace"]["total_bosses"]}** '
                               f'(Realm #{rr["the-eternal-palace"]["normal"]["realm"]})\n'
                               f'**H: {rp["the-eternal-palace"]["heroic_bosses_killed"]}/{rp["the-eternal-palace"]["total_bosses"]}** '
                               f'(Realm #{rr["the-eternal-palace"]["heroic"]["realm"]})\n'
                               f'**M: {rp["the-eternal-palace"]["mythic_bosses_killed"]}/{rp["the-eternal-palace"]["total_bosses"]}** '
                               f'(Realm #{rr["the-eternal-palace"]["mythic"]["realm"]})\n'),
                        inline=False)
        embed.add_field(name=f'__**Nyalotha, The Waking City:**__',
                        value=(f'**N: {rp["nyalotha-the-waking-city"]["normal_bosses_killed"]}/{rp["nyalotha-the-waking-city"]["total_bosses"]}** '
                               f'(Realm #{rr["nyalotha-the-waking-city"]["normal"]["realm"]})\n'
                               f'**H: {rp["nyalotha-the-waking-city"]["heroic_bosses_killed"]}/{rp["nyalotha-the-waking-city"]["total_bosses"]}** '
                               f'(Realm #{rr["nyalotha-the-waking-city"]["heroic"]["realm"]})\n'
                               f'**M: {rp["nyalotha-the-waking-city"]["mythic_bosses_killed"]}/{rp["nyalotha-the-waking-city"]["total_bosses"]}** '
                               f'(Realm #{rr["nyalotha-the-waking-city"]["mythic"]["realm"]})\n'),
                        inline=False)
        return embed

    @staticmethod
    async def build_readycheck_msg(guild_members, sort_by):
        """
        Builds the readycheck layout.

        :param guild_members: A list of WarcraftCharacter objects
        :param sort_by: rank (default), name, class, hoa, mplus, ilvl
        :return: A layout with the sorted list of characters and relevant information
        """
        if len(guild_members) == 0:
            return 'No members found.'
        if sort_by == 'rank':
            guild_members = sorted(sorted(guild_members,
                                          key=lambda x: x.name),
                                   key=lambda x: x.guild_rank)
        elif sort_by == 'ilvl':
            guild_members = sorted(sorted(guild_members,
                                          key=lambda x: x.name),
                                   key=lambda x: x.ilvl, reverse=True)
        elif sort_by == 'name':
            guild_members.sort(key=lambda x: x.name)
        elif sort_by == 'mplus':
            guild_members = sorted(sorted(guild_members,
                                          key=lambda x: x.name),
                                   key=lambda x: x.m_plus_weekly_high, reverse=True)
        elif sort_by == 'corruption':
            guild_members = sorted(sorted(guild_members,
                                          key=lambda x: x.name),
                                   key=lambda x: x.corruption_remaining, reverse=True)
        total_ilvl = 0
        member_count = 0
        output = (f'```{"Name:":{14}}|{"M+":{14}}|{"ilvl:":{6}}|\n'
                  f'{"-"*14}+{"-"*14}+{"-"*6}|\n')
        for character in guild_members:
            total_ilvl += character.ilvl
            member_count += 1
            num_runs = len(await WeeklyGuildRunsInterface.get_player_runs(character.name.title()))
            output += (f'{character.name.title():{14}}|'
                       f'{character.m_plus_weekly_high:<{3}}'
                       f'/ {character.m_plus_prev_weekly_high:<{4}}'
                       f'/ {num_runs:<{3}}|'
                       f'{character.ilvl:<{6}}|\n')
        avg_ilvl = round(total_ilvl/member_count)
        output += (f'{"-"*14}+{"-"*14}+{"-"*6}|\n'
                   f'{"Avg:":{14}}|{"":{14}}|{avg_ilvl:<{6}}|\n\n'
                   'Remember:\n'
                   ' - You need to clear a +15 (not necessarily in time) '
                   'to maximize the loot from your weekly chest\n'
                   ' - Weekly vault rewards an extra piece of gear after 1, 4, 10 runs\n'
                   ' - Use the command `casper vault` for more info```')
        return output

    @staticmethod
    async def build_weeklyruns_embed(name, runs, count):
        embed = discord.Embed()
        embed.title = f'__{name.title()}__'
        runs = sorted(runs, key=lambda x: x.dungeon_level, reverse=True)
        if len(runs) == 0:
            embed.add_field(name='No runs found for this week.',
                            value='Make sure the run shows on your r.io page.')
            return embed
        for i, run in enumerate(runs):
            if i < count:
                if i+1 == 1:
                    embed.add_field(
                        name=f'{i+1}. (1st piece of loot) {run.dungeon_name} '
                        f'+{run.dungeon_level}',
                        value=(f'https://raider.io/mythic-plus-runs/season-bfa-4-post/'
                               f'{run.run_id}'),
                        inline=False
                    )
                elif i+1 == 4:
                    embed.add_field(
                        name=f'{i+1}. (2nd piece of loot) {run.dungeon_name} '
                        f'+{run.dungeon_level}',
                        value=(f'https://raider.io/mythic-plus-runs/season-bfa-4-post/'
                               f'{run.run_id}'),
                        inline=False
                    )
                elif i+1 == 10:
                    embed.add_field(
                        name=f'{i+1}. (3rd piece of loot) {run.dungeon_name} '
                        f'+{run.dungeon_level}',
                        value=(f'https://raider.io/mythic-plus-runs/season-bfa-4-post/'
                               f'{run.run_id}'),
                        inline=False
                    )
                else:
                    embed.add_field(
                            name=f'{i+1}. {run.dungeon_name} '
                            f'+{run.dungeon_level}',
                            value=(f'https://raider.io/mythic-plus-runs/season-bfa-4-post/'
                                   f'{run.run_id}'),
                            inline=False
                        )
        return embed

    @staticmethod
    async def build_scores_msg(guild_members, num):
        guild_members.sort(key=lambda x: x.m_plus_score_overall, reverse=True)
        embed = discord.Embed()
        embed.title = ':trophy: __Mythic+ Guild Leaderboard:__ :trophy:'
        for place, character in enumerate(guild_members):
            place = place+1
            temp_place = place  # Because we're using trophy emojies for 1st-3rd places
            if place == 1:
                place = ':first_place:'
            elif place == 2:
                place = ':second_place:'
            elif place == 3:
                place = ':third_place:'
            char_class = character.char_class.title()
            if char_class == 'Death Knight':
                char_class = 'DK'
            elif char_class == 'Demon Hunter':
                char_class = 'DH'
            embed.add_field(name=f'{place}    {character.name.title()}',
                            value=(f'Score: {character.m_plus_score_overall:,} '
                                   f':black_small_square: '
                                   f'Realm: {character.m_plus_rank_overall:,} '
                                   f':black_small_square: '
                                   f'{char_class}: {character.m_plus_rank_class:,} '),
                            inline=False)
            place = temp_place
            if place == num:
                break
        return embed

    @staticmethod
    async def build_callout_msg(guild_members):
        """
        Builds the callout layout.

        :param guild_members: A list of WarcraftCharacter objects
        :return: An output with the offending players if any, otherwise a congratulatory
        message
        """
        guild_members = list(filter(lambda x: x.m_plus_weekly_high < 15, guild_members))
        guild_members = sorted(sorted(guild_members,
                                      key=lambda x: x.name),
                               key=lambda x: x.m_plus_weekly_high)
        output = '__**These people have not run a M+15 or higher this week:**__\n\n```'
        if len(guild_members) > 0:
            output += (f'{"Name:":<{14}}{"Weekly High:":<{3}}\n'
                       f'--------------------------------------------\n')
            for character in guild_members:
                output += (f'{character.name.title():<{14}}'
                           f'{character.m_plus_weekly_high:<{3}}\n')
            output += ('--------------------------------------------\n'
                       'Remember: You need to clear a +15 (not necessarily in time) '
                       'to maximize the loot from your weekly chest.```')
            return output
        return 'Congratulations, everyone has run a M+15 or higher this week!'

    @staticmethod
    async def build_guild_keys_msg(guild_members):
        """
        Builds the mythic+ keys information layout.

        :param guild_members: A list of WarcraftCharacter objects
        :return: An output with mythic+ keys information for the default guild for the
        discord server.
        """
        output = '```Current Mythic+ keys available in guild:\n\n'
        if len(guild_members) > 0:
            for char in guild_members:
                output += (f'{char.name.title():{14}}{char.m_plus_key:{24}}'
                           f'{char.m_plus_key_level:{6}}\n')
            output += '```'
            return output
        else:
            return 'No keys found for this guild.'
    # endregion


def setup(casper):
    casper.add_cog(Warcraft(casper))
