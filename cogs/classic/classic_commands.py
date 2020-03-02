import json

import discord
from discord.ext import commands
from pathlib import WindowsPath

from cogs.classic.classic_character_iface import ClassicCharacterInterface
from cogs.classic.classic_kill_list_iface import ClassicKillListInterface
from cogs.classic.guild_defaults_iface import GuildDefaultsInterface


class Classic(commands.Cog):
    def __init__(self, casper):
        self.casper = casper

    #########################################################################
    # Command Logic
    #########################################################################
    @commands.command()
    async def census(self, ctx):
        census = WindowsPath(('C:/Program Files (x86)/World of Warcraft/_classic_/WTF/'
                              'Account/WARRIORSXFACTOR/SavedVariables/'
                              'CensusPlusClassic.lua'))
        with census.open('rt') as file:
            data = file.read()
        json_data = json.loads(data)
        print(json_data)
        return

    @commands.command()
    async def classicdefaults(self, ctx, classic_guild, realm, region):
        if await GuildDefaultsInterface.update_guild_defaults(
                ctx.guild.id, ctx.guild.name, classic_guild, realm, region):
            return await ctx.send(f'Warcraft realm defaults updated:\n'
                                  f'Guild: {classic_guild.replace("-", " ").title()}\n'
                                  f'Realm: {realm.replace("-"," ").title()}\n'
                                  f'Region: {region.upper()}')
        else:
            return await ctx.send(f'Warcraft defaults could not be updated.')

    @commands.command()
    async def classicadd(self, ctx, name, race, class_, realm):
        ...

    @commands.command()
    async def classicremove(self, ctx, name):
        ...

    @commands.command()
    async def who(self, ctx):
        if ctx.guild.id == 222207370636427264:
            output = ('```'
                      f'{"Name:":<{12}}{"Char:":{13}}{"Class:":{9}}{"Realm:":{13}}\n\n'
                      f'{"Alli":<{12}}{"Allirot":{13}}{"Priest":{9}}{"Sulfuras":{13}}\n'
                      f'{"Grass":<{12}}{"Grassybeef":{13}}{"Warrior":{9}}{"Sulfuras":{13}}\n'
                      f'{"Morz":<{12}}{"Rakraz":{13}}{"Rogue":{9}}{"Sulfuras":{13}}\n'
                      f'{"Ender":<{12}}{"Sallie":{13}}{"Warlock":{9}}{"Sulfuras":{13}}\n'
                      f'{"Cas":<{12}}{"Grubba":{13}}{"Warlock":{9}}{"Sulfuras":{13}}\n'
                      f'{"Zuul":<{12}}{"Zuulforrest":{13}}{"Warlock":{9}}{"Sulfuras":{13}}\n'
                      f'{"Nato":<{12}}{"Udderdefeat":{13}}{"Hunter":{9}}{"Sulfuras":{13}}\n'
                      '```')
            return await ctx.send(output)

    @commands.command()
    async def kos(self, ctx):
        embed = await self.build_kos_embed(ctx)
        return await ctx.send(embed=embed)

    @commands.command()
    async def kosadd(self, ctx, name=None, race=None, char_class=None, level=None,
                     location=None, bounty=None, *, infraction=None):
        if name is None:
            return await ctx.send(
                'Format your command as such:\n\n'
                'casper kosadd Allikazam Undead Mage 27 "Hillsbrad Foothills" 1g '
                'Smoke this fool, he camped me while I was questing.')
        await ClassicKillListInterface.update_character(
            ctx, name, race, char_class, level, location, bounty, infraction)
        embed = await self.build_kos_embed(ctx)
        return await ctx.send(embed=embed)

    @commands.command()
    async def kosremove(self, ctx, name):
        await ClassicKillListInterface.remove_character(ctx, name)
        embed = await self.build_kos_embed(ctx)
        return await ctx.send(embed=embed)

    @commands.command()
    async def koskilled(self, ctx, name):
        ...

    #########################################################################
    # Cog Logic
    #########################################################################
    @staticmethod
    async def get_guild_defaults(guild_id):
        return await GuildDefaultsInterface.get_guild_defaults(guild_id)

    @staticmethod
    async def build_kos_embed(ctx):
        characters = await ClassicKillListInterface.get_kos_list(ctx)
        embed = discord.Embed()
        embed.title = f'{ctx.guild.name.title()}\'s Kill on Sight List:'
        for char in characters:
            embed.add_field(
                name=(f'**{char.name.title()}**, Level {char.level} '
                      f'{char.race.title()} {char.char_class.title()}'),
                value=(f'__**Location of Infraction:**__ {char.location.title()}\n'
                       f'__**Infraction:**__ {char.infraction}\n'
                       f'__**Bounty:**__ {char.bounty}'),
                inline=False
            )
        return embed


def setup(casper):
    casper.add_cog(Classic(casper))
