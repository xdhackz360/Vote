import logging
import random
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store vote data in memory (replace with database in production)
vote_channels = {}
vote_counts = {}
vote_voters = {}  # Dictionary to store voters for each poll
user_data = {}  # Dictionary to store user-specific data

# Replace these with your actual API details
API_ID = "28239710"
API_HASH = "7fc5b35692454973318b86481ab5eca3"
BOT_TOKEN = "7629248955:AAEDVLI83wNW6Yv5kX3drnSjatzVfi2wUig"

app = Client("vote_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    if len(message.command) > 1:
        await handle_participation(client, message)
        return

    keyboard = [
        [
            InlineKeyboardButton("Owner", url="https://t.me/owner_username"),
            InlineKeyboardButton("Updates", url="https://t.me/updates_channel")
        ],
        [InlineKeyboardButton("Add to Channel", url="https://t.me/your_bot?startchannel=true")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = """
» ᴛᴏ ᴄʀᴇᴀᴛᴇ ᴀᴜᴛᴏ ᴠᴏᴛᴇ ᴄʀᴇᴀᴛᴏʀ ꜰᴏʀ ʏᴏᴜʀ ᴄʜᴀᴛ, ᴜꜱᴇ /vote ᴄᴏᴍᴍᴀɴᴅ.
‣ ᴠᴏᴛᴇ-ᴘᴏʟʟ - ɢɪᴠᴇᴀᴡᴀʏ
ɪғ ʏᴏᴜ ɴᴇᴇᴅ ᴀɴʏ ʜᴇʟᴘ, ᴛʜᴇɴ ᴅᴍ ᴛᴏ ᴍʏ ᴏᴡɴᴇʀ
"""
    await message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("vote") & filters.private)
async def vote_command(client, message: Message):
    await message.reply_text("Please send me your channel username (e.g., @channel):", parse_mode=ParseMode.MARKDOWN)
    user_data[message.from_user.id] = {'expecting_channel': True}

@app.on_message(filters.text & filters.private)
async def handle_channel_response(client, message: Message):
    user_id = message.from_user.id
    if 'expecting_channel' not in user_data.get(user_id, {}):
        return

    channel_username = message.text.strip()
    if not channel_username.startswith('@'):
        channel_username = '@' + channel_username

    try:
        chat = await client.get_chat(channel_username)
        bot_member = await client.get_chat_member(chat.id, client.me.id)
        user_member = await client.get_chat_member(chat.id, user_id)

        if not (bot_member.status == ChatMemberStatus.ADMINISTRATOR or bot_member.status == ChatMemberStatus.OWNER):
            await message.reply_text("Please add me as an admin in the channel!", parse_mode=ParseMode.MARKDOWN)
            return

        if not (user_member.status == ChatMemberStatus.ADMINISTRATOR or user_member.status == ChatMemberStatus.OWNER):
            await message.reply_text("You must be an admin in the channel to use this command!", parse_mode=ParseMode.MARKDOWN)
            return

        # Generate single random emoji
        emojis = ["❤️", "🎉", "✨", "💫", "😊"]
        selected_emoji = random.choice(emojis)

        # Store channel info
        clean_username = channel_username.replace('@', '')
        vote_channels[clean_username] = {
            'emoji': selected_emoji,
            'creator_id': user_id,
            'chat_id': chat.id,
            'channel_name': chat.title,
            'full_username': channel_username
        }
        vote_counts[clean_username] = 0
        vote_voters[clean_username] = set()  # Initialize an empty set for voters

        # Create participation link
        bot_username = client.me.username
        participation_link = f"https://t.me/{bot_username}?start={clean_username}"

        success_message = f"""
» ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴠᴏᴛᴇ-ᴘᴏʟʟ ᴄʀᴇᴀᴛᴇᴅ.
• ᴄʜᴀᴛ: {channel_username}
• ᴇᴍᴏᴊɪ: {selected_emoji}

Participation Link:
{participation_link}
"""
        await message.reply_text(success_message, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await message.reply_text(f"Error: Could not access the channel. Make sure:\n1. The channel username is correct\n2. I am an admin in the channel\n3. I have permission to post messages", parse_mode=ParseMode.MARKDOWN)
        logger.error(f"Channel creation error: {e}")

    finally:
        del user_data[user_id]['expecting_channel']

async def handle_participation(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("Invalid participation link!", parse_mode=ParseMode.MARKDOWN)
        return

    channel_username = message.command[1]  # Already clean username from start command
    user = message.from_user

    if channel_username not in vote_channels:
        await message.reply_text("This vote poll doesn't exist!", parse_mode=ParseMode.MARKDOWN)
        return

    channel_info = vote_channels[channel_username]
    emoji = channel_info['emoji']

    # Create vote button
    keyboard = [[InlineKeyboardButton(
        f"{emoji} {vote_counts[channel_username]}",
        callback_data=f"vote|{channel_username}"
    )]]

    participant_message = f"""
[⚡] PARTICIPANT DETAILS [⚡]
‣ ᴜꜱᴇʀ: {user.first_name}
‣ ᴜꜱᴇʀ-ɪᴅ: {user.id}
‣ ᴜꜱᴇʀɴᴀᴍᴇ: @{user.username if user.username else "N/A"}

ɴᴏᴛᴇ: ᴏɴʟʏ ᴄʜᴀɴɴᴇʟ ꜱᴜʙꜱᴄʀɪʙᴇʀꜱ ᴄᴀɴ ᴠᴏᴛᴇ.
×× ᴄʀᴇᴀᴛᴇᴅ ʙʏ - ᴠᴏᴛᴇ ʙᴏᴛ (https://t.me/{client.me.username})
"""
    try:
        await client.send_message(
            chat_id=channel_info['chat_id'],
            text=participant_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        await message.reply_text("✅ sᴜᴄᴄᴇssғᴜʟʟʏ ᴘᴀʀᴛɪᴄɪᴘᴀᴛᴇᴅ.", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await message.reply_text("❌ Error posting to channel. Please make sure I still have admin permissions.", parse_mode=ParseMode.MARKDOWN)
        logger.error(f"Participation error: {e}")

@app.on_callback_query()
async def button_callback(client, callback_query):
    try:
        # Parse callback data
        action, channel_username = callback_query.data.split("|")

        if action != "vote" or channel_username not in vote_channels:
            await callback_query.answer("Invalid vote!", show_alert=True)
            return

        # Check if the user is a subscriber
        user_id = callback_query.from_user.id
        member = await client.get_chat_member(vote_channels[channel_username]['chat_id'], user_id)
        if member.status in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED):
            await callback_query.answer("Only channel subscribers can vote!", show_alert=True)
            return

        # Check if the user has already voted
        if user_id in vote_voters[channel_username]:
            await callback_query.answer("You have already voted!", show_alert=True)
            return

        # Update vote count and add user to voters list
        vote_counts[channel_username] += 1
        vote_voters[channel_username].add(user_id)
        current_votes = vote_counts[channel_username]

        # Show vote confirmation dialog
        success_text = f"""
{vote_channels[channel_username]['channel_name']}
Successfully Voted.
{vote_channels[channel_username]['emoji']} - {current_votes}
Counters On The Post Will Be Updated Soon."""

        await callback_query.answer(success_text, show_alert=True)

        # Update button
        keyboard = [[InlineKeyboardButton(
            f"{vote_channels[channel_username]['emoji']} {current_votes}",
            callback_data=f"vote|{channel_username}"
        )]]

        await callback_query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        logger.error(f"Vote callback error: {e}")
        await callback_query.answer("Error processing vote!", show_alert=True)

if __name__ == "__main__":
    app.run()
