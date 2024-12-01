
# -*- coding: utf-8 -*-

# This is a custom module for Hikka Userbot
# Author: Your Name
# Description: Counts messages in a group and kicks inactive members based on inactivity days.

from datetime import datetime, timedelta
from telethon import functions, types
from .. import loader, utils

class GroupActivityMod(loader.Module):
    """Counts messages in a group and kicks inactive members."""
    strings = {"name": "GroupActivity"}

    async def msgcountcmd(self, message):
        """Counts messages in the current group.
        Usage: .msgcount
        """
        chat = message.chat
        if not chat:
            await message.edit("<b>This command can only be used in groups.</b>")
            return

        result = await message.client(functions.messages.GetFullChatRequest(chat_id=chat.id))
        participants = result.full_chat.participants.participants

        counts = {}
        async for msg in message.client.iter_messages(chat.id):
            if msg.sender_id:
                counts[msg.sender_id] = counts.get(msg.sender_id, 0) + 1

        report = "<b>Message counts in this group:</b>\n"
        for participant in participants:
            user_id = participant.user_id
            count = counts.get(user_id, 0)
            user = await message.client.get_entity(user_id)
            report += f"<b>{utils.escape_html(user.first_name)}</b>: {count} messages\n"

        await message.edit(report)

    async def kicatcmd(self, message):
        """Kicks members inactive for specified days.
        Usage: .kicat <days>
        """
        args = utils.get_args(message)
        if not args or not args[0].isdigit():
            await message.edit("<b>Specify the number of days of inactivity to kick. Example: .kicat 7</b>")
            return

        days = int(args[0])
        cutoff_date = datetime.now() - timedelta(days=days)

        chat = message.chat
        if not chat:
            await message.edit("<b>This command can only be used in groups.</b>")
            return

        kicked_users = []
        async for participant in message.client.iter_participants(chat.id):
            if participant.bot or participant.status == types.UserStatusRecently():
                # Skip bots and recently active users
                continue

            last_seen = getattr(participant.status, "was_online", None)
            if last_seen and last_seen < cutoff_date:
                try:
                    await message.client.kick_participant(chat.id, participant.id)
                    kicked_users.append(participant)
                except Exception as e:
                    await message.reply(f"<b>Failed to kick {participant.first_name}: {e}</b>")

        if kicked_users:
            report = f"<b>Kicked {len(kicked_users)} inactive members:</b>\n"
            for user in kicked_users:
                report += f"<b>{utils.escape_html(user.first_name)}</b>\n"
            await message.edit(report)
        else:
            await message.edit("<b>No inactive members found to kick.</b>")
