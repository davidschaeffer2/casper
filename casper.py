from pathlib import Path

import discord

from config import DiscordAPI
from discord.ext import commands


bot_prefix = commands.when_mentioned_or('Casper ', 'casper ')
bot_description = """Casper is a discord bot with a focus on character data
                  aggregation for Blizzard Entertainment's World of Warcraft. 
                  It also has a variety of joke commands and fitness-related
                  commands."""
casper = commands.Bot(command_prefix=bot_prefix, description=bot_description,
                      owner_id=DiscordAPI.OWNERID, pm_help=True)


@casper.event
async def on_ready():
    print('=============================================================\n'
          'Bot started. Loading cogs...')
    cogs_path = Path(__file__).parent / 'cogs'
    for sub_dir in cogs_path.iterdir():
        for cog in sub_dir.iterdir():
            if 'commands' in cog.name:
                try:
                    casper.load_extension(
                        f'cogs.{sub_dir.name}.{cog.name.replace(".py", "")}')
                    print(f'Loaded: cogs.{sub_dir.name}.{cog.name.replace(".py", "")}')
                except discord.ext.commands.errors.ExtensionAlreadyLoaded as e:
                    print(f'Extension already loaded: {cog.name}')
    print('Finished loading all cogs.\n'
          '=============================================================')


@casper.event
async def on_command(ctx):
    """
    This trigger is just for better error logging and troubleshooting.
    :param ctx:
    :return:
    """
    print(f'=============================================================\n'
          f'Command used:\n'
          f'User: {ctx.author.name}\n'
          f'Server: {ctx.guild}\n'
          f'Channel: {ctx.message.channel}\n'
          f'Command: {ctx.message.content}\n'
          f'=============================================================')
    return


@casper.command()
async def leave(ctx):
    if ctx.author.id == DiscordAPI.OWNERID:
        await ctx.guild.leave()
        print(f'Left guild: {ctx.guild.name}')


@casper.command()
async def where(ctx):
    if ctx.author.id == DiscordAPI.OWNERID:
        output = 'I\'m currently in the following discord servers:\n\n'
        for guild in casper.guilds:
            output += f'{guild.name}\n'
        return await ctx.send(output)


@casper.command()
async def thanks(ctx):
    return await ctx.send('You\'re welcome.')


if __name__ == '__main__':
    casper.run(DiscordAPI.TOKEN)
