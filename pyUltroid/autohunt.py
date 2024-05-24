# written by @moiusrname

import asyncio
from random import randint

from telethon.errors import DataInvalidError
from telethon.events import MessageEdited

from . import LOGS, udB, ultroid_bot, ultroid_cmd


HEXA_BOT = 572621020


async def do_click(msg, *buttons):
    async def _click(m):
        try:
            return await m.click(*buttons)
        except DataInvalidError:
            return

    for _ in range(3):
        await asyncio.sleep(2)
        if msg and msg.buttons:
            if await _click(msg):
                return msg
            else:
                msg = await msg.client.get_messages(msg.chat_id, ids=msg.id)


class HexaError(Exception):
    pass


async def start_hunt(pokes: list):
    async with ultroid_bot.conversation(HEXA_BOT, timeout=10) as conv:
        await conv.send_message("/hunt")
        try:
            response = await conv.get_response()
            if response.photo and response.buttons:
                if not pokes:
                    return response
                if any(i in str(reponse.message).lower() for i in pokes):
                    return response
        except (asyncio.TimeoutError, Exception):
            return
        finally:
            await asyncio.sleep(5)


async def main(pokes):
    for _ in range(pow(2, 5)):
        # send /hunt
        if response := await start_hunt(pokes):
            break
    else:
        raise HexaError("No response for /hunt..")

    await asyncio.sleep(3)
    has_finished = ("fled.", "fainted.", "caught a")
    async with ultroid_bot.conversation(HEXA_BOT, timeout=90) as conv:
        await conv.send_message("Starting #autohexa")
        if response.buttons and response.buttons[0][0].text == "Battle":
            # click Battle
            if not await do_click(response, 0, 0):
                raise HexaError("Could not click Battle..")

        response = await conv.get_response()
        await conv.mark_read()
        await asyncio.sleep(3)

        while True:
            # click poke balls
            clicked = False
            if (
                response.buttons
                and response.buttons[-1][0].text.lower() == "poke balls"
            ):
                if response := await do_click(response, -1, 0):
                    clicked = True
            if not clicked:
                raise HexaError("Could not Click PokeBall..")

            # click 'regular' or the first button
            _response = conv.wait_event(
                MessageEdited(
                    incoming=True,
                    from_users=[HEXA_BOT],
                    func=lambda e: e.is_private and e.id == response.id,
                ),
                timeout=8,
            )
            response = await _response
            clicked = False
            if response.buttons and response.buttons[-1][0].text == r"🔙":
                if response := await do_click(response, 0, 0):
                    clicked = True
            if not clicked:
                raise HexaError("Could not Click Regular/first button..")

            # multiple edits, filter out the useless ones
            func = lambda e: (
                e.is_private
                and e.id == response.id
                and (
                    e.buttons
                    and e.buttons[-1][0].text.lower() == "poke balls"
                    or any(i in e.text.lower() for i in has_finished)
                )
            )
            _response = conv.wait_event(
                MessageEdited(
                    incoming=True,
                    from_users=[HEXA_BOT],
                    func=func,
                ),
                timeout=25,
            )
            response = await _response
            await asyncio.sleep(1)
            if any(i in response.text.lower() for i in has_finished):
                return True
            else:
                continue


@ultroid_cmd(pattern="autohunt (\d+)")
async def poke_autohunter(e):
    count = int(e.pattern_match.group(1))
    done, count = 0, count if count in range(99) else 10
    edt_ = ""
    if keys := udB.get_key("autohunt"):
        assert isinstance(keys, (list, tuple)), "wrong key type"
        edt_ = ", ".join(keys)
    msg = await e.eor(f"`Hunting {count} times for {edt_}..`")
    for _ in range(count):
        try:
            await main(keys)
        except asyncio.TimeoutError:
            LOGS.info("timeout err...")
        except Exception as exc:
            LOGS.exception(exc)
        else:
            done += 1
        finally:
            await asyncio.sleep(randint(8, 16))
    await msg.edit(f"`Hunted {count} times! \nWas Successful {done} times.`")
