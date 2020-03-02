from datetime import datetime
from dateutil.tz import tz

import aiohttp


async def json_get(url, headers=None):
    """
    Asynchronous method to fetch API results as json.
    :param url: The url to make a POST request to.
    :param headers: Optional headers if additional info needs to be passed along
    :return: The json results or None if error
    """
    if headers is None:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return None
            except aiohttp.ClientConnectionError as e:
                print(f'An error occurred while fetching data from {url}:\n'
                      f'{e}')
                return None
    else:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return None
            except aiohttp.ClientConnectionError as e:
                print(f'An error occurred while fetching data from {url}:\n'
                      f'{e}')
                return None


async def json_post(url, auth=None, headers=None, data=None):
    """
    Asynchronous method to post API results as json.
    :param data:
    :param auth:
    :param url: The url to make a POST request to.
    :param headers: Optional headers if additional info needs to be passed along
    :return: The json results or None if error
    """
    async with aiohttp.ClientSession(headers=headers, auth=auth) as session:
        async with session.post(url, data=data) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                return None


async def convert_utc_to_local(utc_time):
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
