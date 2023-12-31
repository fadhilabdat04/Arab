import asyncio
import importlib
import re
from contextlib import closing, suppress

from pyrogram import enums, filters, idle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from uvloop import install

from ArabManage import BOT_NAME, BOT_USERNAME, LOG_GROUP_ID, aiohttpsession, app, bot1
from ArabManage.modules import ALL_MODULES
from ArabManage.modules.sudoers import bot_sys_stats
from ArabManage.utils import paginate_modules
from ArabManage.utils.constants import MARKDOWN
from ArabManage.utils.dbfunctions import clean_restart_stage

loop = asyncio.get_event_loop()

HELPABLE = {}


async def start_bot():
    global HELPABLE

    for module in ALL_MODULES:
        imported_module = importlib.import_module(f"ArabManage.modules.{module}")
        if (
            hasattr(imported_module, "__MODULE__")
            and imported_module.__MODULE__
        ):
            imported_module.__MODULE__ = imported_module.__MODULE__
            if (
                hasattr(imported_module, "__HELP__")
                and imported_module.__HELP__
            ):
                HELPABLE[imported_module.__MODULE__.lower()] = imported_module
    bot_modules = ""
    j = 1
    for i in ALL_MODULES:
        if j == 4:
            bot_modules += "|{:<15}|\n".format(i)
            j = 0
        else:
            bot_modules += "|{:<15}".format(i)
        j += 1
    print("+===============================================================+")
    print("|                ARAB MANAGE SUPERBOT by ARAB SUPPORT                    |")
    print("+===============+===============+===============+===============+")
    print(bot_modules)
    print("+===============+===============+===============+===============+")
    print(f"[INFO]: BOT STARTED AS {BOT_NAME}!")

    restart_data = await clean_restart_stage()

    try:
        print("[INFO]: SENDING ONLINE STATUS")
        if restart_data:
            await app.edit_message_text(
                restart_data["chat_id"],
                restart_data["message_id"],
                "**Restarted Successfully**",
            )

        else:
            await app.send_message(LOG_GROUP_ID, "Bot started!")
    except Exception:
        pass

    
    await idle()

    await aiohttpsession.close()
    print("[INFO]: CLOSING AIOHTTP SESSION AND STOPPING BOT")
    await app.stop()
    print("[INFO]: Bye!")
    for task in asyncio.all_tasks():
        task.cancel()
    print("[INFO]: Turned off!")


home_keyboard_pm = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                text="Help", callback_data="bot_commands"
            ),
            InlineKeyboardButton(
                text="Jajanan Telegram",
                url="https://t.me/Jasasiarab",
            ),
        ],
        [
            InlineKeyboardButton(
                text="ARAB ROBOT Stats",
                callback_data="stats_callback",
            ),
        ],
        [
            InlineKeyboardButton(
                text="Tambahkan Saya Menjadi Di GC Ampas-mu",
                url=f"http://t.me/{BOT_USERNAME}?startgroup=new",
            )
        ],
    ]
)

home_text_pm = (
    f"""
yoo {query.from_user.first_name}, saya {BOT_NAME} Bot Music Plus Manage Bot , Ga Ada yang spesial sama aja kek bot music laen, kalo mau donasi jangan lupa klik /donate otey

General command are:
 - /start: Start the bot
 - /help: Give this message
 - /donate: Donate for my 

 Dev By: @Dhilnihnge 
 """
)


keyboard = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                text="Help",
                url=f"t.me/{BOT_USERNAME}?start=help",
            ),
            InlineKeyboardButton(
                text="Jasa SI ARAB",
                url="https://t.me/Jasasiarab",
            ),
        ],
        [
            InlineKeyboardButton(
                text="ARAB ROBOT Stats",
                callback_data="stats_callback",
            ),
        ],
    ]
)


@app.on_message(filters.command("start"))
async def start(_, message):
    if message.chat.type != enums.ChatType.PRIVATE:
        return await message.reply_photo(
            photo="https://te.legra.ph/file/d2f257710e964cd8aa0db.jpg",
            caption="Pm Me For More Details.",
            reply_markup=keyboard,
        )
    if len(message.text.split()) > 1:
        name = (message.text.split(None, 1)[1]).lower()
        if name == "mkdwn_help":
            await message.reply(
                MARKDOWN, parse_mode="html", disable_web_page_preview=True
            )
        elif "_" in name:
            module = name.split("_", 1)[1]
            text = (
                f"Here is the help for **{HELPABLE[module].__MODULE__}**:\n"
                + HELPABLE[module].__HELP__
            )
            await message.reply(text, disable_web_page_preview=True)
        elif name == "help":
            text, keyb = await help_parser(message.from_user.first_name)
            await message.reply(
                text,
                reply_markup=keyb,
            )
    else:
        await message.reply_photo(
            photo="https://te.legra.ph/file/d2f257710e964cd8aa0db.jpg",
            caption=home_text_pm,
            reply_markup=home_keyboard_pm,
        )
    return


@app.on_message(filters.command("help"))
async def help_command(_, message):
    if message.chat.type != enums.ChatType.PRIVATE:
        if len(message.command) >= 2:
            name = (message.text.split(None, 1)[1]).lower()
            if str(name) in HELPABLE:
                key = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Click here",
                                url=f"t.me/{BOT_USERNAME}?start=help_{name}",
                            )
                        ],
                    ]
                )
                await message.reply(
                    f"Click on the below button to get help about {name}",
                    reply_markup=key,
                )
            else:
                await message.reply(
                    "PM Me For More Details.", reply_markup=keyboard
                )
        else:
            await message.reply(
                "Pm Me For More Details.", reply_markup=keyboard
            )
    elif len(message.command) >= 2:
        name = (message.text.split(None, 1)[1]).lower()
        if str(name) in HELPABLE:
            text = (
                f"Here is the help for **{HELPABLE[name].__MODULE__}**:\n"
                + HELPABLE[name].__HELP__
            )
            await message.reply(text, disable_web_page_preview=True)
        else:
            text, help_keyboard = await help_parser(
                message.from_user.first_name
            )
            await message.reply(
                text,
                reply_markup=help_keyboard,
                disable_web_page_preview=True,
            )
    else:
        text, help_keyboard = await help_parser(message.from_user.first_name)
        await message.reply(
            text, reply_markup=help_keyboard, disable_web_page_preview=True
        )
    return


async def help_parser(name, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    return (
        """yoo {query.from_user.first_name}, saya {BOT_NAME} Bot Music Plus Manage Bot , Ga Ada yang spesial sama aja kek bot music laen, kalo mau donasi jangan lupa klik /donate otey

General command are:
 - /start: Start the bot
 - /help: Give this message
 - /donate: Donate for my 

 Dev By: @Dhilnihnge
""".format(
            first_name=name,
            bot_name=BOT_NAME,
        ),
        keyboard,
    )


@app.on_message(filters.command("donate"))
async def donate(_, message):
    message.chat.type != enums.ChatType.PRIVATE:
        return await message.reply_photo(
            photo="https://telegra.ph/qris-08-08-3",
            caption="Hai {first_name}, jika kamu merasa bot ini berguna kamu bisa melakukan donasi dengan scan QR menggunakan merchant yang support QRIS ya. Karena server bot ini menggunakan VPS dan tidaklah gratis. Terimakasih..\n\nDevs : @Dhilnihnge",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Contact My Owner", url="t.me/Dhilnihnge")]]
        )
    if len(message.text.split()) > 1:
        name = (message.text.split(None, 1)[1]).lower()
        if name == "mkdwn_help":
            await message.reply(
                MARKDOWN, parse_mode="html", disable_web_page_preview=True
            )
        elif "_" in name:
            module = name.split("_", 1)[1]
            text = (
                f"Here is the help for **{HELPABLE[module].__MODULE__}**:\n"
                + HELPABLE[module].__HELP__
            )
            await message.reply(text, disable_web_page_preview=True)
        elif name == "help":
            text, keyb = await help_parser(message.from_user.first_name)
            await message.reply(
                text,
                reply_markup=keyb,
            )
    else:
        await message.reply_photo(
            photo="",
            caption=
            reply_markup=home_keyboard_pm,
        )
    return
   

@app.on_callback_query(filters.regex("bot_commands"))
async def commands_callbacc(_, CallbackQuery):
    text, keyboard = await help_parser(CallbackQuery.from_user.mention)
    await app.send_message(
        CallbackQuery.message.chat.id,
        text=text,
        reply_markup=keyboard,
    )

    await CallbackQuery.message.delete()


@app.on_callback_query(filters.regex("stats_callback"))
async def stats_callbacc(_, CallbackQuery):
    text = await bot_sys_stats()
    await app.answer_callback_query(CallbackQuery.id, text, show_alert=True)


@app.on_callback_query(filters.regex(r"help_(.*?)"))
async def help_button(client, query):
    home_match = re.match(r"help_home\((.+?)\)", query.data)
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)
    create_match = re.match(r"help_create", query.data)
    top_text = f"""
yoo {query.from_user.first_name}, saya {BOT_NAME}.
Music Plus Manage Bot , Ga Ada yang spesial sama aja kek bot music laen, kalo mau donasi jangan lupa klik /donate otey,  udah langsung klik button di bawah
Dev By: @Dhilnihnge
General command are:
 - /start: Start the bot
 - /help: Give this message
 - /donate: Donate for my 
 """
    if mod_match:
        module = mod_match.group(1)
        text = (
            "{} **{}**:\n".format(
                "Here is the help for", HELPABLE[module].__MODULE__
            )
            + HELPABLE[module].__HELP__
        )

        await query.message.edit(
            text=text,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("back", callback_data="help_back")]]
            ),
            disable_web_page_preview=True,
        )
    elif home_match:
        await app.send_message(
            query.from_user.id,
            text=home_text_pm,
            reply_markup=home_keyboard_pm,
        )
        await query.message.delete()
    elif prev_match:
        curr_page = int(prev_match.group(1))
        await query.message.edit(
            text=top_text,
            reply_markup=InlineKeyboardMarkup(
                paginate_modules(curr_page - 1, HELPABLE, "help")
            ),
            disable_web_page_preview=True,
        )

    elif next_match:
        next_page = int(next_match.group(1))
        await query.message.edit(
            text=top_text,
            reply_markup=InlineKeyboardMarkup(
                paginate_modules(next_page + 1, HELPABLE, "help")
            ),
            disable_web_page_preview=True,
        )

    elif back_match:
        await query.message.edit(
            text=top_text,
            reply_markup=InlineKeyboardMarkup(
                paginate_modules(0, HELPABLE, "help")
            ),
            disable_web_page_preview=True,
        )

    elif create_match:
        text, keyboard = await help_parser(query)
        await query.message.edit(
            text=text,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )

    return await client.answer_callback_query(query.id)


if __name__ == "__main__":
    install()
    with closing(loop):
        with suppress(asyncio.exceptions.CancelledError):
            loop.run_until_complete(start_bot())
        loop.run_until_complete(asyncio.sleep(3.0))  # task cancel wait
