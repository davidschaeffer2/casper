"""
File: utilities.py

This file contains some utility functions that are used multiple times in the project.
Usually covers things such as boilerplate code that can be annoying to have to retype
each time you want to perform that process.
"""

from datetime import datetime
from dateutil.tz import tz

import aiohttp


class Utilities:
    def __init__(self, aiohttp_session):
        self.aiohttp_session = aiohttp_session

    async def json_get(self, url, headers=None):
        """
        Asynchronous method to fetch API results as json.

        :param url: The url to make a GET request to.
        :param headers: Optional headers if additional info needs to be passed along
        :return: The response if successful, otherwise None
        """
        if headers is None:
            async with self.aiohttp_session.get(url) as resp:
                return await resp.json()
        else:
            async with self.aiohttp_session.get(url, headers=headers) as resp:
                return await resp.json()

    async def json_post(self, url, auth=None, headers=None, data=None):
        """
        Asynchronous method to post API results as json.

        :param url: The url to make a POST request to.
        :param auth: Optional authorization information
        :param headers: Optional headers if additional info needs to be passed along
        :param data: Optional data payload
        :return: The response if successful, otherwise None
        """
        if headers is None:
            async with self.aiohttp_session.post(url) as resp:
                return await resp.json()
        else:
            async with self.aiohttp_session.post(url, headers=headers, auth=auth) as resp:
                return await resp.json()

    async def convert_utc_to_local(self, utc_time):
        """
        Given a datetime string formatted as "YYYY-MM-DD HH:MM:SS" in zulu time,
        convert to the local timezone equivalent
        :param utc_time:
        :return: The string formatted the same way but in local time
        """
        local_time = datetime.strptime(utc_time, '%Y-%m-%d %H:%M:%S')
        local_time = local_time.replace(tzinfo=tz.tzutc())
        local_time = local_time.astimezone(tz.tzlocal())
        return local_time
