import asyncio
from urllib import parse

import discord
from discord.ext import commands
from cogs.warcraft.warcraft_character_iface import WarcraftCharacterInterface
from cogs.warcraft.guild_defaults_iface import GuildDefaultsInterface
from config import WarcraftAPI
import utilities


class Warcraft(commands.Cog):
    def __init__(self, casper):
        self.casper = casper
        self.casper.loop.create_task(self.auto_crawl())

        self.blizzard_region_namespaces = {
            'us': 'en_US', 'eu': 'en_GB', 'kr': 'ko_KR', 'ru': 'ru_RU', 'tw': 'zh_TW',
            'sea': 'en_SG'
        }
        self.dungeons = {
            'ad': 'Atal\'Dazar',
            'fh': 'Freehold',
            'kr': 'King\'s Rest',
            'sots': 'Shrine of the Storm',
            'sob': 'Siege of Boralus',
            'tos': 'Temple of Sethraliss',
            'mj': 'Mechagon - Junkyard',
            'mw': 'Mechagon - Workshop',
            'ml': 'The MOTHERLODE!',
            'om': 'Outside Mechagon',
            'ur': 'The Underrot',
            'td': 'Tol Dagor',
            'wm': 'Waycrest Manor', 'sm': 'Waycrest Manor',
        }

    # region Looping Tasks
    async def auto_crawl(self):
        """
        Auto-runs every hour. Gets a list of guilds from the database, fetches guild info
        from Blizzard API and then fetches Raider.io data for each character found in
        each guild. This data is then stored in the database.

        :return: None
        """
        while not self.casper.is_closed():
            print('Starting crawl.')
            guild_name = 'Felforged'
            guild_realm = 'wyrmrest-accord'
            guild_region = 'us'
            guild_members = await self.get_guild_members_from_blizzard(
                        guild_name, guild_realm, guild_region)
            if guild_members is None:
                print(f'An error occurred when attempting to retrieve guild members '
                      f'for:\nGuild: {guild_name}\nRealm: {guild_realm}\n'
                      f'Region: {guild_region}')
                continue
            for name, realm, rank in guild_members:
                try:
                    raiderio_data = await self.get_raiderio_data(
                        name, realm, guild_region)
                    if raiderio_data is not None:
                        await WarcraftCharacterInterface.update_character(
                            raiderio_data, rank)
                except Exception as e:
                    print(f'Error occurred when attempting to retrieve character data'
                          f' during a guild crawl:\nERROR: {e}')
            print('Finished auto crawl.')
            await asyncio.sleep(60 * 30)  # 60 seconds times 30 to sleep 30 mins
    # endregion

    # region Removes response and command invoke message
    @commands.command()
    async def warcraftdefaults(self, ctx, warcraft_guild, realm, region):
        """
        Gets the guild name, realm, and region set up as defaults for the discord server.

        :param ctx: Discord.py invocation context. Used for sending messages.
        :param warcraft_guild: Name of guild, space are auto-sanitized
        :param realm: Name of realm, space are auto-sanitized
        :param region: 2-letter abbreviation for region - US, EU, RU, KR
        :return: A GuildDefaults object
        """
        if await GuildDefaultsInterface.update_guild_defaults(
                ctx.guild.id, ctx.guild.name, warcraft_guild, realm, region):
            await self.react_to_message(ctx.message, True)
            return await ctx.send(f'Warcraft realm defaults updated:\n'
                                  f'Guild: {warcraft_guild.replace("-"," ").title()}\n'
                                  f'Realm: {realm.replace("-"," ").title()}\n'
                                  f'Region: {region.upper()}')
        else:
            await self.react_to_message(ctx.message, False)
            return await ctx.send(f'Warcraft defaults could not be updated.')

    @commands.command()
    async def crawlguild(self, ctx, guild=None, realm=None, region=None):
        """
        Fetches guild members of a guild via the Blizzard API.

        :param ctx: Discord.py invocation context. Used for sending messages.
        :param guild: Name of guild, space are auto-sanitized
        :param realm: Name of realm, space are auto-sanitized
        :param region: 2-letter abbreviation for region - US, EU, RU, KR
        :return: Status message in the channel the command was used
        """
        # Can this be handled better instead of repeated in every command?
        try:
            if guild is None:
                defaults = await self.get_guild_defaults(ctx.guild.id)
                guild = defaults.warcraft_guild
                realm = defaults.warcraft_realm
                region = defaults.warcraft_region
            elif realm is None or len(realm) < 3:
                defaults = await self.get_guild_defaults(ctx.guild.id)
                realm = defaults.warcraft_realm
                region = defaults.warcraft_region
            elif region is None:
                defaults = await self.get_guild_defaults(ctx.guild.id)
                region = defaults.warcraft_region
        except AttributeError:
            await self.react_to_message(ctx.message, False)
            await ctx.send(
                'To search a guild by name only, default settings must be '
                'set up using the command:\n'
                '`casper warcraftdefaults guild-name realm-name region`'
                '\nPlease include realm-name and region or configure your '
                'default settings.')
        # See note above this block
        msg = await ctx.send(f'Fetching data for {guild.replace("-", "").title()} on '
                             f'{realm.replace("-", " ").title()}-{region.upper()}.')
        guild_members = await self.get_guild_members_from_blizzard(guild, realm, region)
        if guild_members is None:
            print(f'An error occurred when attempting to retrieve guild members for:\n'
                  f'Guild: {guild}\nRealm: {realm}\nRegion{region}.')
            await msg.edit(content=f'An error occurred when attempting to retrieve'
                                   f' guild members for '
                                   f'{guild.replace("-", "").title()} on '
                                   f'{realm.replace("-", "").title()}-{region.upper()}')
        await msg.edit(content=f'Members retrieved. Updating records.')
        for name, realm, rank in guild_members:
            try:
                raiderio_data = await self.get_raiderio_data(name, realm, region)
                if raiderio_data is not None:
                    await WarcraftCharacterInterface.update_character(raiderio_data, rank)
            except Exception as e:
                print(f'Error occurred when attempting to retrieve character data during '
                      f'a guild crawl:\nGuild: {guild.replace("-", "").title()}\n'
                      f'Realm: {realm.replace("-", "").title()}-{region.upper()}\n'
                      f'Character: {name.title()}\n'
                      f'ERROR: {e}')
        await self.react_to_message(ctx.message, True)
        await msg.edit(content='Finished crawl. Deleting message in 30 seconds.',
                       delete_after=30)

    @commands.command()
    async def wow(self, ctx, name, realm=None, region=None):
        """
        Fetches character data from Raider.io API.

        :param ctx: Discord.py invocation context. Used for sending messages.
        :param name: Name of character
        :param realm: Name of realm, space are auto-sanitized
        :param region: 2-letter abbreviation for region - US, EU, RU, KR
        :return: A Discord Embed object populated with character data if successful,
        otherwise an error message.
        """
        try:
            if realm is None or len(realm) < 3:
                defaults = await self.get_guild_defaults(ctx.guild.id)
                realm = defaults.warcraft_realm
                region = defaults.warcraft_region
            elif region is None:
                defaults = await self.get_guild_defaults(ctx.guild.id)
                region = defaults.warcraft_region
        except AttributeError:
            await self.react_to_message(ctx.message, False)
            return await ctx.send(
                'To search a character by name only, default settings must be '
                'set up using the command:\n'
                '`casper warcraftdefaults guild-name realm-name region`'
                '\nPlease include realm-name and region or configure your '
                'default settings.')
        msg = await ctx.send(f'Fetching data for {name.title()} on '
                             f'{realm.title().replace("-", " ")}-'
                             f'{region.upper()}.')
        raiderio_data = await self.get_raiderio_data(name, realm, region)
        if raiderio_data is None:
            await self.react_to_message(ctx.message, False)
            return await msg.edit(content=f'Could not find data for {name.title()} on '
                                          f'{realm.title().replace("-", " ")}-'
                                          f'{region.title()} on raider.io. Ensure the '
                                          f'character has been queried there.',
                                  delete_after=60)
        # for k, v in raiderio_data.items():
        #     print(f'{k}: {v}')
        await msg.edit(content=f'Found character data, updating records.')
        try:
            await WarcraftCharacterInterface.update_character(raiderio_data)
        except Exception as e:
            await self.react_to_message(ctx.message, False)
            print(f'Error occurred during wow command character update:\n{e}')
            return await msg.edit(content='An error occurred when updating the '
                                          'character record. Sorry.',
                                  delete_after=60)
        await msg.edit(content=f'Records updated, building layout.')
        try:
            embed = await self.build_character_embed(raiderio_data)
            await self.react_to_message(ctx.message, True)
            return await msg.edit(content='', embed=embed, delete_after=60)
        except Exception as e:
            await self.react_to_message(ctx.message, False)
            print(f'Error occurred during wow command building embed:\n{e}')
            return await msg.edit(content=f'An error occurred while building '
                                          f'layout. Sorry.',
                                  delete_after=60)

    @commands.command()
    async def guild(self, ctx, name=None, realm=None, region=None):
        try:
            if name is None:
                defaults = await self.get_guild_defaults(ctx.guild.id)
                name = defaults.warcraft_guild
                realm = defaults.warcraft_realm
                region = defaults.warcraft_region
            elif realm is None or len(realm) < 3:
                defaults = await self.get_guild_defaults(ctx.guild.id)
                realm = defaults.warcraft_realm
                region = defaults.warcraft_region
            elif region is None:
                defaults = await self.get_guild_defaults(ctx.guild.id)
                region = defaults.warcraft_region
        except AttributeError:
            await self.react_to_message(ctx.message, False)
            return await ctx.send(
                'To search a guild without specifying the name, default settings must be '
                'set up using the command:\n'
                '`casper warcraftdefaults guild-name realm-name region`'
                '\nPlease include guild-name, realm-name, and region or configure your '
                'default settings.')
        msg = await ctx.send(f'Fetching data for {name.replace("-", " ").title()} on '
                             f'{realm.title().replace("-", " ")}-'
                             f'{region.upper()}.')
        raiderio_data = await self.get_raiderio_guild_data(name, realm, region)
        if raiderio_data is None:
            await self.react_to_message(ctx.message, False)
            return await msg.edit(content=f'Could not find data for {name.title()} on '
                                          f'{realm.title().replace("-", " ")}-'
                                          f'{region.title()} on raider.io. Ensure the '
                                          f'guild has been queried there.',
                                  delete_after=60)
        await msg.edit(content=f'Found guild data, building layout.')
        try:
            embed = await self.build_guild_embed(raiderio_data)
            await self.react_to_message(ctx.message, True)
            return await msg.edit(content='', embed=embed, delete_after=60)
        except Exception as e:
            await self.react_to_message(ctx.message, False)
            print(f'Error occurred during guild command building embed:\n{e}')
            return await msg.edit(content=f'An error occurred while building '
                                          f'layout. Sorry.',
                                  delete_after=60)

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
        response = await utilities.json_get(api_url)
        try:
            price = int((response['price'] / 100) / 100)
            await self.react_to_message(ctx.message, True)
            return await ctx.send(f'The price of a token for the {region.upper()} '
                                  f'costs: {price:,} gold.', delete_after=60)
        except AttributeError as e:
            await self.react_to_message(ctx.message, False)
            print(f'An error occurred when fetching token price:\n{e}')
            return await ctx.send('Could not fetch token price at this time. Please try '
                                  'again later.', delete_after=60)

    @commands.command()
    async def mplus(self, ctx, *, chars):
        msg = await ctx.send('Fetching character data.')
        defaults = await self.get_guild_defaults(ctx.guild.id)
        try:
            realm = defaults.warcraft_realm
            region = defaults.warcraft_region
        except AttributeError:
            await self.react_to_message(ctx.message, False)
            return await ctx.send(
                'To remove a guild without specifying realm and region, default settings '
                'must be set up using the command:\n'
                '`casper warcraftdefaults guild-name realm-name region`\n'
                'Otherwise, specify realm and region after the guild name.')
        names = chars.split(' ')
        out_msg = await self.build_mplus_msg(names, realm, region)
        await self.react_to_message(ctx.message, True)
        return await msg.edit(content=out_msg, delete_after=60)
    # endregion

    # region Leaves response and command invoke message
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
                                  f'Example: 0,2,4,5')
        try:
            defaults = await self.get_guild_defaults(ctx.guild.id)
            guild = defaults.warcraft_guild
            realm = defaults.warcraft_realm
            region = defaults.warcraft_region
        except AttributeError:
            await self.react_to_message(ctx.message, False)
            return await ctx.send(
                'To fetch guild members, default settings must be set up using the '
                'command:\n`casper warcraftdefaults guild-name realm-name region`')
        msg = await ctx.send(f'Fetching members for {guild.replace("-", "").title()} '
                             f'on {realm.replace("-", " ").title()}-{region.upper()}.')
        guild_members = await WarcraftCharacterInterface.get_guild_members(
            guild, realm, region, ranks)
        await msg.edit(content=f'Members found. Building layout.')
        output = await self.build_readycheck_msg(guild_members, sort_by)
        await self.react_to_message(ctx.message, True)
        return await msg.edit(content=output)

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
        try:
            defaults = await self.get_guild_defaults(ctx.guild.id)
            guild = defaults.warcraft_guild
            realm = defaults.warcraft_realm
            region = defaults.warcraft_region
        except AttributeError:
            await self.react_to_message(ctx.message, False)
            return await ctx.send(
                'To fetch guild members, default settings must be set up using the '
                'command:\n`casper warcraftdefaults guild-name realm-name region`')
        msg = await ctx.send(f'Fetching scores for the top {num} characters in the guild.')
        characters = await WarcraftCharacterInterface.get_guild_members(guild, realm, region)
        await msg.edit(content=f'Building layout.')
        output = await self.build_scores_msg(characters, num)
        await self.react_to_message(ctx.message, True)
        return await msg.edit(content='', embed=output)

    @commands.command()
    async def callout(self, ctx, ranks='0,1,3,6'):
        """
        Outputs a message with a list of characters who did not run a mythic+ of 15 or
        higher.

        :param ctx: Discord.py invocation context. Used for sending messages.
        :param ranks: A comma-separated string of integer ranks to filter by
        :return: An output with the offending characters
        """
        guild, realm, region = None, None, None
        try:
            defaults = await self.get_guild_defaults(ctx.guild.id)
            guild = defaults.warcraft_guild
            realm = defaults.warcraft_realm
            region = defaults.warcraft_region
        except AttributeError:
            await self.react_to_message(ctx.message, False)
            return await ctx.send(
                'To fetch guild members, default settings must be set up using the '
                'command:\n`casper warcraftdefaults guild-name realm-name region`')
        msg = await ctx.send(f'Fetching members for {guild.replace("-", "").title()} '
                             f'on {realm.replace("-", " ").title()}-{region.upper()}.')
        guild_members = await WarcraftCharacterInterface.get_guild_members(
            guild, realm, region, ranks)
        await msg.edit(content=f'Members found. Building layout.')
        output = await self.build_callout_msg(guild_members)
        await self.react_to_message(ctx.message, True)
        return await msg.edit(content=output)

    @commands.command()
    async def keys(self, ctx):
        """
        Fetches a list of characters with mythic+ key information.

        :param ctx: Discord.py invocation context. Used for sending messages.
        :return: An output of mythic+ key information
        """
        try:
            defaults = await self.get_guild_defaults(ctx.guild.id)
            guild = defaults.warcraft_guild
            realm = defaults.warcraft_realm
            region = defaults.warcraft_region
        except AttributeError:
            await self.react_to_message(ctx.message, False)
            return await ctx.send(
                'To fetch guild members, default settings must be set up using the '
                'command:\n`casper warcraftdefaults guild-name realm-name region`')
        guild_keys_output = await self.build_guild_keys_msg(
            await WarcraftCharacterInterface.get_guild_keys(guild, realm, region))
        await self.react_to_message(ctx.message, True)
        return await ctx.send(guild_keys_output)
    # endregion

    # region Reacts to message and leave command invoke message
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
            key = self.dungeons[key_info.split('+')[0]]
            key_level = int(key_info.split('+')[1])
        except Exception as e:
            print(f'Error occurred when parsing dungeon info:\n{e}')
            return await ctx.send('Please format your key info as:\n'
                                  '`casper addkey allikazam fh+18`')
        try:
            defaults = await self.get_guild_defaults(ctx.guild.id)
            realm = defaults.warcraft_realm
            region = defaults.warcraft_region
        except AttributeError:
            await self.react_to_message(ctx.message, False)
            return await ctx.send(
                'To fetch guild members, default settings must be set up using the '
                'command:\n`casper warcraftdefaults guild-name realm-name region`')
        character = await WarcraftCharacterInterface.get_character(name, realm, region)
        if character is None:
            await self.react_to_message(ctx.message, False)
            return await ctx.send(f'Could not find character by name of: {name.title()}.')
        await WarcraftCharacterInterface.addkey(character, key, key_level)
        return await self.react_to_message(ctx.message, True)

    @commands.command()
    async def removekey(self, ctx, name=None):
        """

        :param ctx: Discord.py invocation context. Used for sending messages.
        :param name: Character name
        :return: A message with the outcome of the key removal
        """
        if name is None:
            return await ctx.send('Please format your command as:\n'
                                  '`casper removekey allikazam`')
        try:
            defaults = await self.get_guild_defaults(ctx.guild.id)
            realm = defaults.warcraft_realm
            region = defaults.warcraft_region
        except AttributeError:
            return await ctx.send(
                'To fetch guild members, default settings must be set up using the '
                'command:\n`casper warcraftdefaults guild-name realm-name region`')
        character = await WarcraftCharacterInterface.get_character(name, realm, region)
        if character is None:
            await self.react_to_message(ctx.message, False)
            return await ctx.send(f'Could not find character by name of: {name.title()}. '
                                  f'This message will delete itself in 30 seconds.',
                                  delete_after=60)
        await WarcraftCharacterInterface.removekey(character)
        return await self.react_to_message(ctx.message, True)

    @commands.command()
    async def resetkeys(self, ctx):
        """
        Resets the mythic+ key information.

        :param ctx: Discord.py invocation context. Used for sending messages.
        :return: A message stating keys have been reset
        """
        await WarcraftCharacterInterface.reset_keys()
        return await self.react_to_message(ctx.message, True)

    @commands.command()
    async def remove(self, ctx, name):
        """
        Used to remove characters from the database that may no longer exist.

        :param ctx: Discord.py invocation context. Used for sending messages.
        :param name: Character name
        :return: A message with the outcome of the character removal
        """
        try:
            defaults = await self.get_guild_defaults(ctx.guild.id)
            realm = defaults.warcraft_realm
            region = defaults.warcraft_region
        except AttributeError:
            return await ctx.send(
                'To fetch guild members, default settings must be set up using the '
                'command:\n`casper warcraftdefaults guild-name realm-name region`')
        character = await WarcraftCharacterInterface.get_character(name, realm, region)
        if character is None:
            await self.react_to_message(ctx.message, False)
            return await ctx.send(f'Could not find character by name of: {name.title()}.')
        await WarcraftCharacterInterface.remove_character(character)
        return await self.react_to_message(ctx.message, True)
    # endregion

    # region Administrative commands
    @commands.command()
    async def removeall(self, ctx):
        if ctx.author.id != self.casper.owner_id:
            return
        characters = await WarcraftCharacterInterface.get_all_characters()
        characters = [character for character in characters
                      if character.guild is not 'felforged']
        for char in characters:
            await WarcraftCharacterInterface.remove_character(char)
        return await self.react_to_message(ctx.message, True)

    @commands.command()
    async def removeguild(self, ctx, guild_name, realm=None, region=None):
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
        defaults = await self.get_guild_defaults(ctx.guild.id)
        try:
            if realm is None:
                realm = defaults.warcraft_realm
            if region is None:
                region = defaults.warcraft_region
        except AttributeError:
            return await ctx.send(
                'To remove a guild without specifying realm and region, default settings '
                'must be set up using the command:\n'
                '`casper warcraftdefaults guild-name realm-name region`\n'
                'Otherwise, specify realm and region after the guild name.')
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

    @staticmethod
    async def get_guild_defaults(guild_id):
        """
        Fetches the guild defaults for a given discord server.

        :param guild_id: The Discord server ID for the server where the command was called
        :return: A GuildDefaults objects if successful, otherwise None
        """
        return await GuildDefaultsInterface.get_guild_defaults(guild_id)

    @staticmethod
    async def get_blizzard_access_token():
        """
        Fetched an access token for use with Blizzard API.

        :return: A Blizzard access token if successful, otherwise None
        """
        url = (f'https://us.battle.net/oauth/token?grant_type='
               f'client_credentials&client_id={WarcraftAPI.API_CLIENTID}'
               f'&client_secret={WarcraftAPI.API_CLIENTSECRET}')
        try:
            token = await utilities.json_get(url)
            return token
        except KeyError as e:
            print(f'Error attempting to generate access token:\n{e}')
            return None

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
                   f'{realm.lower()}/{parse.quote(name).lower()}'
                   f'f?namespace=profile-us&locale=en_US'
                   f'&access_token={token["access_token"]}')
            return await utilities.json_get(url)
        else:
            return None

    @staticmethod
    async def get_raiderio_data(name, realm, region):
        """
        Fetches character information from Raider.io API

        :param name: Character name
        :param realm: Realm name, spaces are auto-sanitized
        :param region: 2-letter abbreviation for region - US, EU, RU, KR
        :return: The returned Raider.io data
        """
        url = (f'https://raider.io/api/v1/characters/profile?region={region.lower()}'
               f'&realm={realm.replace(" ", "-").lower()}'
               f'&name={parse.quote(name).lower()}'
               f'&fields=gear,corruption,guild,raid_progression,mythic_plus_ranks,'
               f'mythic_plus_recent_runs,mythic_plus_highest_level_runs,'
               f'mythic_plus_weekly_highest_level_runs,'
               f'mythic_plus_previous_weekly_highest_level_runs,'
               f'mythic_plus_scores_by_season:current')
        return await utilities.json_get(url)

    @staticmethod
    async def get_raiderio_guild_data(name, realm, region):
        url = (f'https://raider.io/api/v1/guilds/profile?'
               f'region={region.lower()}&realm={realm.replace(" ", "-").lower()}'
               f'&name={parse.quote(name.replace("-", " ")).lower()}'
               f'&fields=raid_progression,raid_rankings')
        return await utilities.json_get(url)

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
                       f'{parse.quote(guild_name.lower().replace("-", " "))}'
                       f'/roster?namespace=profile-us&locale=en_US'
                       f'&access_token={token["access_token"]}')
                results = await utilities.json_get(url)
                if results is None:
                    return None
                members = []
                for member in results['members']:
                    if 'realm' in member['character'] and \
                            member['character']['level'] == 120:
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

    @staticmethod
    async def build_character_embed(r):  # r is raiderio_data
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
                   f'Heart of Azeroth: {r["gear"]["artifact_traits"]:.1f}\n'
                   f'Cloak Level: {r["gear"]["corruption"]["cloakRank"]} '
                   f'(Corruption: {r["gear"]["corruption"]["total"]})\n'
                   f'[Armory](https://worldofwarcraft.com/en-us/character/'
                   f'{r["realm"].lower().replace(" ", "-")}/{r["name"].lower()}) - '
                   f'[Raider.io](https://raider.io/characters/{r["region"].lower()}'
                   f'/{r["realm"].lower().replace(" ", "-")}/{r["name"].lower()})')
        )

        # RAID PROGRESSION
        raids = r["raid_progression"]
        embed.add_field(
            name='__**Raid Progression:**__',
            value=(f'**UD:** {raids["uldir"]["summary"]:{12}}'
                   f'**BoD:** {raids["battle-of-dazaralor"]["summary"]:{12}}'
                   f'**CoS:** {raids["crucible-of-storms"]["summary"]:{12}}'
                   f'**EP:** {raids["the-eternal-palace"]["summary"]:{12}}'
                   f'**NWC:** {raids["nyalotha-the-waking-city"]["summary"]:{12}}'),
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
        embed.add_field(name='This message will self-destruct in:',
                        value='60 seconds.',
                        inline=False)
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
        if sort_by == 'rank':
            guild_members = sorted(sorted(guild_members,
                                          key=lambda x: x.name),
                                   key=lambda x: x.guild_rank)
        elif sort_by == 'hoa':
            guild_members = sorted(sorted(guild_members,
                                          key=lambda x: x.name),
                                   key=lambda x: x.heart_of_azeroth_level, reverse=True)
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
        total_heart = 0.0
        member_count = 0
        output = (f'```{"Name:":{14}}{"HoA:":{6}}{"M+:":{9}}'
                  f'{"ilvl:":{6}}{"Cloak:":{10}}\n'
                  f'--------------------------------------------\n')
        for character in guild_members:
            total_ilvl += character.ilvl
            total_heart += character.heart_of_azeroth_level
            member_count += 1
            corruption = character.corruption_remaining
            if 20 <= corruption < 40:
                corruption = f'{corruption} *'
            elif 40 <= corruption < 60:
                corruption = f'{corruption} * *'
            elif 60 <= corruption < 80:
                corruption = f'{corruption} * * *'
            elif corruption >= 80:
                corruption = f'{corruption} SERIOUSLY'
            output += (f'{character.name.title():{14}}'
                       f'{character.heart_of_azeroth_level:<{6}}'
                       f'{character.m_plus_weekly_high:<{3}}'
                       f'| {character.m_plus_prev_weekly_high:<{4}}'
                       f'{character.ilvl:<{6}}'
                       f'{character.cloak_rank:<{3}}| {corruption:<{3}}\n')
        avg_ilvl = round(total_ilvl/member_count)
        avg_heart = round(total_heart/member_count, 1)
        output += ('--------------------------------------------\n'
                   f'{"Avg:":{14}}{avg_heart:<{10}}{avg_ilvl:<{6}}\n\n'
                   'Remember: You need to clear a +15 (not necessarily in time) '
                   'to maximize the loot from your weekly chest.```')
        return output

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
        guild_members.sort(key=lambda x: x.m_plus_weekly_high)
        output = '__**These people have not run a M+15 or higher this week:**__\n\n'
        if len(guild_members) > 0:
            for character in guild_members:
                output += f'{character.name.title()} - {character.m_plus_weekly_high}\n'
            output += ('\nRemember: You need to finish a +15 '
                       'to maximize the loot from your weekly chest.')
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

    async def build_mplus_msg(self, names, realm, region):
        plus_2_achieve = 33096
        wqs_50_complete = 33094
        total_num_runs = 0
        total_world_quests = 0
        total_boss_kills = 0
        out_msg = f'```{"Character":{14}}{"M+":<{5}}{"WQs":<{6}}{"Bosses":<{7}}\n\n'
        token = await self.get_blizzard_access_token()
        if token is not None:
            for name in names:
                char_mplus_runs = 0
                char_wqs = 0
                char_boss_kills = 0
                results = await self.get_blizzard_data(name, realm, region)
                achieves = results['achievements']
                try:
                    criteria_index = achieves['criteria'].index(plus_2_achieve)
                    char_mplus_runs = achieves['criteriaQuantity'][criteria_index]
                    total_num_runs += achieves['criteriaQuantity'][criteria_index]

                    criteria_index = achieves['criteria'].index(wqs_50_complete)
                    char_wqs = achieves['criteriaQuantity'][criteria_index]
                    total_world_quests += achieves['criteriaQuantity'][criteria_index]

                    current_raids = ['The Emerald Nightmare', 'Trial of Valor',
                                     'The Nighthold', 'Tomb of Sargeras',
                                     'Antorus, the Burning Throne',
                                     'Uldir', 'Battle for Daza\'lor',
                                     'Crucible of Storms', 'The Eternal Palace'
                                     ]
                    raid_results = [raid for raid in results['progression']['raids']
                                    if raid['name'] in current_raids]
                    for raid in raid_results:
                        for boss in raid['bosses']:
                            char_boss_kills += boss['lfrKills']
                            char_boss_kills += boss['normalKills']
                            char_boss_kills += boss['heroicKills']
                            char_boss_kills += boss['mythicKills']
                    total_boss_kills += char_boss_kills
                    out_msg += (f'{name.title():{14}}{char_mplus_runs:<{5}}'
                                f'{char_wqs:<{6}}{char_boss_kills:<{7}}\n')
                except (KeyError, ValueError, TypeError) as e:
                    print(f'An error occurred when fetching mplus data:\n{e}')
                    out_msg += (f'{name.title():{14}}{"Err":<{5}}'
                                f'{"Err":<{6}}{"Err":<{7}}\n')
            out_msg += (f'---------------------------------\n'
                        f'{"Total":{14}}{total_num_runs:<{5}}'
                        f'{total_world_quests:<{6}}{total_boss_kills:<{7}}\n\n'
                        f'(Since the start of Legion)'
                        f'```')
        return out_msg
    # endregion


def setup(casper):
    casper.add_cog(Warcraft(casper))
