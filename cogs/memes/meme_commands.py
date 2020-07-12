import discord
import random
from discord.ext import commands


class Memes(commands.Cog):
    def __init__(self, casper):
        self.casper = casper

    @commands.command(hidden=True, aliases=['SpongeBob'])
    async def spongebob(self, ctx, *, message: str = None):
        """
        sPOnGeBobIfY SomEONes MesSaGe
        """
        if message is not None:
            new_string = await self.get_spongebobified_msg(message)
            return await ctx.send(new_string)
        async for message in ctx.channel.history(before=ctx.message, limit=1):
            if message.author.id == self.casper.user.id:
                return await ctx.send('You think you\'re smarter than me?')
            msg_to_sb = message.content
            new_string = await self.get_spongebobified_msg(msg_to_sb)
            return await ctx.send(new_string)

    @staticmethod
    async def get_spongebobified_msg(msg_to_sb: str):
        new_string = ''
        for c in msg_to_sb:
            if random.randint(1, 2) == 2:
                if c == c.upper():
                    new_string += c.lower()
                else:
                    new_string += c.upper()
            else:
                new_string += c
        return new_string

    @commands.command(hidden=True)
    async def emojify(self, ctx, emoji, *, message):
        """Don't :clap: you :clap: hate :clap: when :clap: people :clap: write :clap:
        like :clap: this?"""
        if message is not None:
            new_str = f' {emoji} '.join([word for word in message.split(' ')])
            try:
                return await ctx.send(new_str)
            except discord.errors.HTTPException:
                return await ctx.send(f'Your :petty: new :petty: message :petty: was '
                                      f':petty: too :petty: long :petty: to :petty: send.')

    @commands.command()
    async def space(self, ctx, *, message: str = None):
        return await ctx.send(' '.join(message))

    @commands.command(hidden=True, aliases=['shame', 'hos'])
    async def hallofshame(self, ctx):
        hos = ['Nori', 'Bre', 'Lynndrae', 'Kessy', 'Sanguinara', 'MadMaddie', 'Zel',
               'Chinter', 'Krom', 'Aiirie', '<Redacted 1> - Fuck this one especially',
               '<Redacted 2>', 'Sana',
               'Carver', 'Shadowkow', 'Egha', 'Sythas', 'Elia', 'Kerrigan',
               'Incision', 'Saix', 'Arawn', 'Lienthunder']
        hos.sort()
        output = '\n'.join(hos)
        return await ctx.send(f'__**Hall of Shame:**__\n\n{output}')


def setup(casper):
    casper.add_cog(Memes(casper))
