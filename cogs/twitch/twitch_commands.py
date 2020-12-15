import asyncio
from pprint import pprint

import aiohttp
import discord

from cogs.twitch.db_interfaces.twitch_iface import TwitchDBInterface as TwitchIface
from config import TwitchAPI
from configparser import ConfigParser
from datetime import datetime
from discord.ext import commands, tasks
from utilities import Utilities as Utils


class Twitch(commands.Cog):
    def __init__(self, casper):
        self.casper = casper

        self.config = ConfigParser()
        self.config.read('config.ini')

        self.aiohttp_session = casper.aiohttp_session

        @tasks.loop(seconds=60)
        async def check_for_streams():
            """
            Polls Twitch every 60 seconds for stream status for registered Twitch streamers

            :return: None
            """
            ch_sims_and_logs = self.casper.get_channel(307655779056484353)
            print(f'=============================================\n'
                  f'Crawling streams at {datetime.now()}...')
            channels = await TwitchIface.get_all_channels()
            try:
                for ch in channels:
                    print(f'Checking {ch.username.title()} stream...')
                    stream = await self.get_twitch_channel_status(ch.username)
                    stream = stream['data']
                    if len(stream) == 0:  # non-live streams are empty
                        await TwitchIface.set_is_live(ch.username, False)
                        continue
                    print(f'{ch.username} is live:')
                    pprint(stream)
                    if ch.is_live is False:
                        if await TwitchIface.set_is_live(ch.username, True):
                            game_name = await self.get_twitch_game_name(stream[0]['game_id'])
                            embed = await self.create_new_live_stream_embed(
                                stream[0], game_name)
                            await ch_sims_and_logs.send(embed=embed)
            except Exception as e:
                print(f'Weird error?\n{e}')
                pass
            print(f'Finished crawling streams.\n'
                  f'=============================================')

        check_for_streams.start()

    @commands.command()
    async def addtwitch(self, ctx, username: str) -> discord.Message:
        """
        Add a new twitch channel to be polled for when they go live

        :param ctx: Represents the context in which a command is being invoked under
        :param username: The username as seen in the twitch URL
        :return: A discord message with success/failure in the calling channel
        """
        if username is None:
            return await ctx.send('Please include the username of the Twitch channel '
                                  'you\'d you like remove.')
        if await TwitchIface.add_channel(username=username.lower()):
            return await ctx.send(f'Record created for {username.title()}.')
        else:
            return await ctx.send('An error occurred when creating a record for your '
                                  'channel.')

    @commands.command()
    async def removetwitch(self, ctx, username: str = None) -> discord.Message:
        """
        Remove a twitch channel from going live notifications.

        :param ctx: Represents the context in which a command is being invoked under
        :param username: The username as seen in the twitch URL
        :return: A discord message with success/failure in the calling channel
        """
        if username is None:
            return await ctx.send('Please include the username of the Twitch channel '
                                  'you\'d you like remove.')
        if await TwitchIface.remove_channel(username.lower()):
            return await ctx.send(f'Record removed for {username.title()}.')
        else:
            return await ctx.send('An error occurred when creating a record for your '
                                  'channel.')

    # region Cog Logic
    async def html_get(self, url):
        access_token = await self.get_twitch_access_token()
        if access_token:
            headers = {'Client-ID': TwitchAPI.CLIENT_ID,
                       'Authorization': f'Bearer {access_token}'}
            connector = aiohttp.TCPConnector(limit=60)
            async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
                try:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            return resp
                        else:
                            print(f'GET to {url} failed:\n{resp.status}:{resp.reason}')
                            return None
                except aiohttp.ClientConnectionError as e:
                    print(f'An error occurred while fetching data from '
                          f'{TwitchAPI.APP_ACCESS_TOKEN_URL}:\n{e}')

    async def json_get(self, url):
        access_token = await self.get_twitch_access_token()
        if access_token:
            headers = {'Client-ID': TwitchAPI.CLIENT_ID,
                       'Authorization': f'Bearer {access_token}'}
            connector = aiohttp.TCPConnector(limit=60)
            async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
                try:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            return await resp.json()
                        else:
                            print(f'GET to {url} failed:\n{resp.status}:{resp.reason}')
                            return None
                except aiohttp.ClientConnectionError as e:
                    print(f'An error occurred while fetching data from '
                          f'{url}:\n{e}')
                    return None

    @staticmethod
    async def json_post(url):
        headers = {'Client-ID': TwitchAPI.CLIENT_ID}
        connector = aiohttp.TCPConnector(limit=60)
        async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
            try:
                async with session.post(url) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 400:
                        print(f'POST to {url} failed:\n{resp.status}:{resp.reason}')
                        return None
            except aiohttp.ClientConnectionError as e:
                print(f'An error occurred while posting data to '
                      f'{TwitchAPI.APP_ACCESS_TOKEN_URL}:\n{e}')
                return None
            except TimeoutError as e:
                print('')

    async def get_twitch_access_token(self):
        access_token = self.config.get('twitch_api', 'access_token')
        headers = {'Client-ID': TwitchAPI.CLIENT_ID}
        if not await self.access_token_is_valid(access_token):
            print(f'Twitch access token is not valid: {access_token}\n'
                  f'Fetching new Twitch access token...')
            resp = await Utils(self.aiohttp_session).resp_get(
                TwitchAPI.APP_ACCESS_TOKEN_URL, headers=headers)
            while resp.status != 200:
                print('Cannot fetch new access token, retrying in 30 seconds')
                await asyncio.sleep(30)
                resp = await Utils(self.aiohttp_session).resp_get(
                    TwitchAPI.APP_ACCESS_TOKEN_URL, headers=headers)
            access_token = resp['access_token']
            self.config.set('twitch_api', 'access_token', access_token)
            with open('config.ini', 'w') as configfile:
                self.config.write(configfile)
            print(f'New Twitch access token: {access_token}')
            return access_token
        return access_token

    async def access_token_is_valid(self, access_token):
        validation_url = 'https://id.twitch.tv/oauth2/validate'
        headers = {'Authorization': f'OAuth {access_token}'}
        resp = await Utils(self.aiohttp_session).resp_get(validation_url, headers=headers)
        if resp.status == 200:
            return True
        return False

    async def get_twitch_channel_status(self, username: str):
        access_token = await self.get_twitch_access_token()
        if access_token:
            headers = {'Client-ID': TwitchAPI.CLIENT_ID,
                       'Authorization': f'Bearer {access_token}'}
            url = f'https://api.twitch.tv/helix/streams?user_login={username}'
            resp = await Utils(self.aiohttp_session).json_get(url, headers=headers)
            return resp

    async def get_twitch_game_name(self, twitch_game_id):
        access_token = await self.get_twitch_access_token()
        if access_token:
            headers = {'Client-ID': TwitchAPI.CLIENT_ID,
                       'Authorization': f'Bearer {access_token}'}
            url = f'https://api.twitch.tv/helix/games?id={twitch_game_id}'
            resp = await Utils(self.aiohttp_session).json_get(url, headers=headers)
            try:
                return resp['data'][0]['name']
            except IndexError as e:
                print(f'Get game name failed:\n{e}')
                return ''

    async def create_new_live_stream_embed(self, stream: dict, game_name):
        embed = discord.Embed(url=f'https://www.twitch.tv/{stream["user_name"]}')
        user_data = await self.get_twitch_user_data(stream['user_name'])
        profile_image = user_data['profile_image_url']
        embed.set_image(url=profile_image)
        try:
            embed.title = (f'{stream["user_name"]} just went live on Twitch with '
                           f'{game_name}!')
        except KeyError as e:
            print(f'Embed broke: {e}')
            return None
        embed.description = stream["title"]
        return embed

    async def get_twitch_user_data(self, login_name):
        access_token = await self.get_twitch_access_token()
        if access_token:
            headers = {'Client-ID': TwitchAPI.CLIENT_ID,
                       'Authorization': f'Bearer {access_token}'}
            url = f'https://api.twitch.tv/helix/users?login={login_name}'
            resp = await Utils(self.aiohttp_session).json_get(url, headers=headers)
            try:
                return resp['data'][0]
            except TypeError as e:
                return None


def setup(casper):
    casper.add_cog(Twitch(casper))
