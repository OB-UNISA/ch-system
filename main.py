import multiprocessing
import os
from datetime import datetime

import discord
from replit import db

import notify
import routine
import server
import utils

client = discord.Client()


@client.event
async def on_ready():
    print(f'BOT: logged at {datetime.now()}')
    for boss in utils.BOSSES:
        db[boss] = utils.get_timer(boss)


@client.event
async def on_message(message):
    if message.author == client.user or message.channel.name != 'timer-bot':
        return

    msg = message.content.split(' ')
    all_commands = ['all', 'All', 'soon', 'Soon']
    get_commands = ['g', 'G', 'get', 'Get']
    sub_commands = ['sub', 'Sub']
    unsub_commands = ['unsub', 'Unsub']
    length = len(msg)

    if length == 1 and msg[0] in all_commands:
        msg_to_send = ''

        frozen = False
        dl = False
        edl = False
        raid = False

        for boss in utils.BOSSES.keys():
            timer = utils.get_timer(boss)
            if timer is not None:
                boss2 = None
                if boss.isdigit():
                    boss2 = int(boss)
                if not frozen and boss2 is not None and 110 <= boss2 <= 140 and utils.minutes_sub(
                        timer) >= -10:
                    frozen = True
                    msg_to_send += utils.separator_label('frozen:',
                                                         separator='')
                elif not dl and boss2 is not None and 155 <= boss2 <= 180 and utils.minutes_sub(
                        timer) >= -10:
                    dl = True
                    msg_to_send += utils.separator_label('dl:')
                elif not edl and boss2 is not None and 185 <= boss2 <= 215 and utils.minutes_sub(
                        timer) >= -10:
                    edl = True
                    msg_to_send += utils.separator_label('edl:')
                elif not raid and boss2 is None:
                    raid = True
                    msg_to_send += utils.separator_label('raid:')

                if boss2 is None or utils.minutes_sub(timer) >= -10:
                    msg_to_send += f'{boss}: {utils.minutes_to_dhm(timer)}\n'
        if len(msg_to_send) > 1:
            await message.channel.send(msg_to_send)
        else:
            await message.channel.send('no timers found')
    elif length == 2 and msg[0] in get_commands:
        boss = msg[1]
        minutes = utils.get_timer(boss)
        if minutes is not None:
            await message.channel.send(utils.minutes_to_dhm(minutes))
        else:
            await message.channel.send(f'{boss} no timer set')
    elif length == 1:
        boss = msg[0]
        if boss in utils.BOSSES:
            default_timer = utils.BOSSES[boss]
            db[boss] = utils.minutes_add(default_timer)
            await message.channel.send(f'{boss} reset to {default_timer}m')
        else:
            await message.channel.send(f'{boss} is not tracked')
    elif length >= 2 and msg[0] in sub_commands:
        msg_to_send = ''
        for boss in msg[1:]:
            if utils.add_sub(boss, message.author.id):
                msg_to_send += f'added to {boss} subs\n'
            else:
                msg_to_send += f'already in {boss} subs\n'
        await message.channel.send(f'{message.author.mention}\n' + msg_to_send)
    elif length >= 2 and msg[0] in unsub_commands:
        msg_to_send = ''
        for boss in msg[1:]:
            if utils.remove_sub(boss, message.author.id):
                msg_to_send += f'removed from {boss} subs\n'
            else:
                msg_to_send += f'not a {boss} sub\n'
        await message.channel.send(f'{message.author.mention}\n' + msg_to_send)
    elif length == 2:
        try:
            boss = msg[0]
            timer = int(msg[1])
            if utils.set_timer(boss, timer):
                if timer == 0:
                    await message.channel.send(f'{boss} timer deleted')
                else:
                    await message.channel.send(f'{boss} set to {timer}m')
            else:
                await message.channel.send(f'{boss} is not tracked')

        except ValueError:
            await message.channel.send(utils.usage(message.content))
    else:
        await message.channel.send(utils.usage(message.content))


server_s = multiprocessing.Process(target=server.run)
server_s.daemon = True
server_s.start()
notifier = multiprocessing.Process(target=notify.start_notifier)
notifier.daemon = True
notifier.start()
delete_old_timers = multiprocessing.Process(target=routine.delete_old_timers)
delete_old_timers.daemon = True
delete_old_timers.start()
client.run(os.getenv('TOKEN'))
