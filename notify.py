import os
import time

import discord
from replit import db

import utils

client = discord.Client()


async def notify():
    channel = client.get_channel(int(db['notify']))
    while True:
        if not db['429']:
            utils.logger('NOTIFIER: check')
            for boss in utils.BOSSES:
                timer = utils.get_timer(boss)
                if timer is not None:
                    minutes = utils.minutes_sub(int(timer))
                    if 10 >= minutes >= 0:
                        msg = None
                        key = boss + utils.SUB_SUFFIX
                        try:
                            subs_id = db[key]
                            if subs_id:
                                msg = f'{boss} due in {utils.minutes_to_dhm(timer)} {" ".join(subs_id)}'
                            else:
                                raise IndexError
                        except (KeyError, IndexError):
                            msg = f'{boss} due in {utils.minutes_to_dhm(timer)}'
                        try:
                            await channel.send(msg)
                            utils.logger(f'NOTIFIER: {boss} sent')
                        except discord.errors.HTTPException as e:
                            message_error = str(e)
                            utils.logger(message_error)
                            if '429' in message_error:
                                utils.status(True)
                                time.sleep(3600)
                                utils.status(False)
        time.sleep(300)


@client.event
async def on_ready():
    utils.logger('NOTIFIER: ready')
    await notify()


def start_notifier():
    client.run(os.getenv('TOKEN'))
