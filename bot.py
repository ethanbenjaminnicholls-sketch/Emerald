import os
import json
import random
import asyncio
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# TOKEN
# ============================================================

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise RuntimeError("TOKEN environment variable is missing!")


# ============================================================
# INTENTS
# ============================================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True


# ============================================================
# BOT
# ============================================================

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ============================================================
# CONFIG
# ============================================================

CONFIG_FILE = "bot_config.json"


def load_config():

    if not os.path.exists(CONFIG_FILE):
        return {}

    try:

        with open(
            CONFIG_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as error:

        print(
            f"CONFIG LOAD ERROR: {error}"
        )

        return {}


def save_config():

    try:

        with open(
            CONFIG_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                config,
                file,
                indent=4
            )

    except Exception as error:

        print(
            f"CONFIG SAVE ERROR: {error}"
        )


config = load_config()


# ============================================================
# COLORS
# ============================================================

def get_color(value):

    value = str(
        value
    ).lower().strip()

    colors = {

        "red": discord.Color.red(),

        "green": discord.Color.green(),

        "blue": discord.Color.blue(),

        "purple": discord.Color.purple(),

        "orange": discord.Color.orange(),

        "yellow": discord.Color.yellow(),

        "pink": discord.Color.magenta(),

        "gold": discord.Color.gold(),

        "teal": discord.Color.teal(),

        "black": discord.Color.from_rgb(
            0,
            0,
            0
        ),

        "white": discord.Color.from_rgb(
            255,
            255,
            255
        )
    }

    # HEX COLOR

    if value.startswith("#"):

        try:

            number = int(
                value[1:],
                16
            )

            if 0 <= number <= 0xFFFFFF:

                return discord.Color(
                    number
                )

        except ValueError:

            pass

    return colors.get(
        value,
        discord.Color.green()
    )


# ============================================================
# READY
# ============================================================

@bot.event
async def on_ready():

    print(
        "========================================"
    )

    print(
        f"Logged in as: {bot.user}"
    )

    print(
        f"Bot ID: {bot.user.id}"
    )

    print(
        "========================================"
    )

    # STATUS

    try:

        await bot.change_presence(

            status=discord.Status.online,

            activity=discord.Streaming(

                name=".gg/emerald",

                url="https://www.twitch.tv/emerald"

            )

        )

    except Exception as error:

        print(
            f"PRESENCE ERROR: {error}"
        )

    # GLOBAL COMMAND SYNC

    try:

        synced = await bot.tree.sync()

        print(
            f"SUCCESSFULLY SYNCED "
            f"{len(synced)} COMMANDS"
        )

        for command in synced:

            print(
                f"COMMAND: /{command.name}"
            )

    except Exception as error:

        print(
            f"COMMAND SYNC ERROR: {error}"
        )


# ============================================================
# HELP
# ============================================================

@bot.tree.command(
    name="help",
    description="Show all bot commands."
)
async def help_command(
    interaction: discord.Interaction
):

    embed = discord.Embed(

        title="💚 Emerald Bot",

        description=(
            "Here are all available commands."
        ),

        color=discord.Color.green()

    )

    embed.add_field(

        name="🛡️ Moderation",

        value=(
            "`/kick` — Kick a member\n"
            "`/ban` — Ban a member\n"
            "`/timeout` — Timeout a member\n"
            "`/role` — Give a role"
        ),

        inline=False
    )

    embed.add_field(

        name="👋 Welcome",

        value=(
            "`/welcomesetup` — "
            "Set up welcome messages"
        ),

        inline=False
    )

    embed.add_field(

        name="🎉 Giveaways",

        value=(
            "`/giveaway` — Start a giveaway"
        ),

        inline=False
    )

    embed.add_field(

        name="✅ Verification",

        value=(
            "`/verifysetup` — "
            "Set up verification"
        ),

        inline=False
    )

    embed.add_field(

        name="🔊 Voice",

        value=(
            "`/jointocreate` — "
            "Create Join to Create"
        ),

        inline=False
    )

    embed.set_footer(
        text="Emerald Bot"
    )

    await interaction.response.send_message(
        embed=embed
    )


# ============================================================
# WELCOME SETUP
# ============================================================

@bot.tree.command(
    name="welcomesetup",
    description="Set up the welcome system."
)
@app_commands.describe(

    channel="Welcome channel.",

    message=(
        "Welcome message. "
        "Use {user} for the member."
    ),

    embed="Use an embed? yes or no.",

    color="Embed color.",

    image_url="Optional image URL."

)
@app_commands.checks.has_permissions(
    administrator=True
)
async def welcomesetup(

    interaction: discord.Interaction,

    channel: discord.TextChannel,

    message: str,

    embed: str = "no",

    color: str = "green",

    image_url: str = ""

):

    guild_id = str(
        interaction.guild.id
    )

    if guild_id not in config:

        config[guild_id] = {}

    config[guild_id]["welcome"] = {

        "channel_id": channel.id,

        "message": message,

        "embed": embed.lower() in (
            "yes",
            "y",
            "true",
            "on"
        ),

        "color": color,

        "image_url": image_url

    }

    save_config()

    await interaction.response.send_message(

        "✅ **Welcome system configured!**\n\n"

        f"Channel: {channel.mention}\n"

        f"Embed: `{embed}`\n"

        f"Color: `{color}`\n"

        f"Image: `{image_url or 'None'}`",

        ephemeral=True

    )


# ============================================================
# MEMBER JOIN
# ============================================================

@bot.event
async def on_member_join(member):

    guild_id = str(
        member.guild.id
    )

    guild_config = config.get(
        guild_id,
        {}
    )

    welcome = guild_config.get(
        "welcome"
    )

    if not welcome:
        return

    channel = member.guild.get_channel(

        welcome.get(
            "channel_id"
        )

    )

    if channel is None:
        return

    message = welcome.get(
        "message",
        "Welcome {user}!"
    )

    message = message.replace(
        "{user}",
        member.mention
    )

    # NORMAL MESSAGE

    if not welcome.get(
        "embed",
        False
    ):

        try:

            await channel.send(
                message
            )

        except Exception as error:

            print(
                f"WELCOME ERROR: {error}"
            )

        return

    # EMBED

    welcome_embed = discord.Embed(

        description=message,

        color=get_color(
            welcome.get(
                "color",
                "green"
            )
        )

    )

    welcome_embed.set_thumbnail(
        url=member.display_avatar.url
    )

    image_url = welcome.get(
        "image_url",
        ""
    )

    if image_url:

        welcome_embed.set_image(
            url=image_url
        )

    try:

        await channel.send(
            embed=welcome_embed
        )

    except Exception as error:

        print(
            f"WELCOME EMBED ERROR: {error}"
        )


# ============================================================
# ROLE
# ============================================================

@bot.tree.command(
    name="role",
    description="Give a member a role."
)
@app_commands.describe(
    user="Member.",
    role="Role."
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def role(

    interaction: discord.Interaction,

    user: discord.Member,

    role: discord.Role

):

    if role.is_default():

        await interaction.response.send_message(

            "❌ You cannot give @everyone.",

            ephemeral=True

        )

        return

    bot_member = interaction.guild.me

    if bot_member is None:

        await interaction.response.send_message(

            "❌ I could not find my bot member.",

            ephemeral=True

        )

        return

    if role >= bot_member.top_role:

        await interaction.response.send_message(

            "❌ That role is above or equal "
            "to my highest role.",

            ephemeral=True

        )

        return

    try:

        await user.add_roles(
            role
        )

        await interaction.response.send_message(

            f"✅ Gave {role.mention} "
            f"to {user.mention}."

        )

    except discord.Forbidden:

        await interaction.response.send_message(

            "❌ I cannot give that role.",

            ephemeral=True

        )


# ============================================================
# KICK
# ============================================================

@bot.tree.command(
    name="kick",
    description="Kick a member."
)
@app_commands.describe(
    user="Member to kick.",
    reason="Reason."
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def kick(

    interaction: discord.Interaction,

    user: discord.Member,

    reason: str = "No reason provided"

):

    try:

        await user.kick(
            reason=reason
        )

        await interaction.response.send_message(

            f"👢 **{user}** was kicked.\n"
            f"Reason: {reason}"

        )

    except discord.Forbidden:

        await interaction.response.send_message(

            "❌ I cannot kick that member.",

            ephemeral=True

        )


# ============================================================
# BAN
# ============================================================

@bot.tree.command(
    name="ban",
    description="Ban a member."
)
@app_commands.describe(
    user="Member to ban.",
    reason="Reason."
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def ban(

    interaction: discord.Interaction,

    user: discord.Member,

    reason: str = "No reason provided"

):

    try:

        await user.ban(
            reason=reason
        )

        await interaction.response.send_message(

            f"🔨 **{user}** was banned.\n"
            f"Reason: {reason}"

        )

    except discord.Forbidden:

        await interaction.response.send_message(

            "❌ I cannot ban that member.",

            ephemeral=True

        )


# ============================================================
# TIMEOUT
# ============================================================

@bot.tree.command(
    name="timeout",
    description="Timeout a member."
)
@app_commands.describe(

    user="Member to timeout.",

    minutes="Timeout length in minutes.",

    reason="Reason."

)
@app_commands.checks.has_permissions(
    administrator=True
)
async def timeout(

    interaction: discord.Interaction,

    user: discord.Member,

    minutes: int,

    reason: str = "No reason provided"

):

    if minutes < 1:

        await interaction.response.send_message(

            "❌ Minutes must be at least 1.",

            ephemeral=True

        )

        return

    if minutes > 40320:

        await interaction.response.send_message(

            "❌ Maximum timeout is 28 days.",

            ephemeral=True

        )

        return

    try:

        await user.timeout(

            timedelta(
                minutes=minutes
            ),

            reason=reason

        )

        await interaction.response.send_message(

            f"⏰ {user.mention} has been "
            f"timed out for **{minutes} minutes**."

        )

    except discord.Forbidden:

        await interaction.response.send_message(

            "❌ I cannot timeout that member.",

            ephemeral=True

        )


# ============================================================
# GIVEAWAY
# ============================================================

@bot.tree.command(
    name="giveaway",
    description="Start a giveaway."
)
@app_commands.describe(

    prize="Giveaway prize.",

    winners="Number of winners.",

    duration="Duration in seconds."

)
@app_commands.checks.has_permissions(
    administrator=True
)
async def giveaway(

    interaction: discord.Interaction,

    prize: str,

    winners: int,

    duration: int

):

    if winners < 1:

        await interaction.response.send_message(

            "❌ Winners must be at least 1.",

            ephemeral=True

        )

        return

    if duration < 10:

        await interaction.response.send_message(

            "❌ Duration must be at least 10 seconds.",

            ephemeral=True

        )

        return

    giveaway_embed = discord.Embed(

        title="🎉 GIVEAWAY!",

        description=(

            f"🎁 **Prize:** {prize}\n"

            f"🏆 **Winners:** {winners}\n\n"

            "React with 🎉 to enter!"

        ),

        color=discord.Color.green()

    )

    await interaction.response.send_message(

        embed=giveaway_embed

    )

    giveaway_message = (
        await interaction.original_response()
    )

    await giveaway_message.add_reaction(
        "🎉"
    )

    await asyncio.sleep(
        duration
    )

    try:

        giveaway_message = (
            await interaction.channel.fetch_message(
                giveaway_message.id
            )
        )

        reaction = discord.utils.get(

            giveaway_message.reactions,

            emoji="🎉"

        )

        if reaction is None:
            return

        users = [

            user async for user in reaction.users()

            if not user.bot

        ]

        if not users:

            await interaction.channel.send(

                "😔 Nobody entered the giveaway."

            )

            return

        chosen = random.sample(

            users,

            min(
                winners,
                len(users)
            )

        )

        mentions = ", ".join(

            user.mention
            for user in chosen

        )

        await interaction.channel.send(

            f"🎉 Congratulations {mentions}!\n"
            f"You won **{prize}**!"

        )

    except Exception as error:

        print(
            f"GIVEAWAY ERROR: {error}"
        )


# ============================================================
# VERIFY VIEW
# ============================================================

class VerifyView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    @discord.ui.button(

        label="Verify",

        style=discord.ButtonStyle.green,

        emoji="✅",

        custom_id="emerald_verify_button"

    )
    async def verify_button(

        self,

        interaction: discord.Interaction,

        button: discord.ui.Button

    ):

        guild_id = str(
            interaction.guild.id
        )

        guild_config = config.get(
            guild_id,
            {}
        )

        verify = guild_config.get(
            "verify"
        )

        if not verify:

            await interaction.response.send_message(

                "❌ Verification is not configured.",

                ephemeral=True

            )

            return

        role = interaction.guild.get_role(

            verify["role_id"]

        )

        if role is None:

            await interaction.response.send_message(

                "❌ The verified role no longer exists.",

                ephemeral=True

            )

            return

        try:

            await interaction.user.add_roles(
                role
            )

            await interaction.response.send_message(

                "✅ You are now verified!",

                ephemeral=True

            )

        except discord.Forbidden:

            await interaction.response.send_message(

                "❌ I cannot give you "
                "the verified role.",

                ephemeral=True

            )


# ============================================================
# VERIFY SETUP
# ============================================================

@bot.tree.command(
    name="verifysetup",
    description="Set up server verification."
)
@app_commands.describe(

    channel="Verification channel.",

    role="Role users receive after verification."

)
@app_commands.checks.has_permissions(
    administrator=True
)
async def verifysetup(

    interaction: discord.Interaction,

    channel: discord.TextChannel,

    role: discord.Role

):

    guild_id = str(
        interaction.guild.id
    )

    if guild_id not in config:

        config[guild_id] = {}

    config[guild_id]["verify"] = {

        "channel_id": channel.id,

        "role_id": role.id

    }

    save_config()

    verify_embed = discord.Embed(

        title="✅ Verification",

        description=(

            "Click **Verify** below to receive "
            "the verified role."

        ),

        color=discord.Color.green()

    )

    await channel.send(

        embed=verify_embed,

        view=VerifyView()

    )

    await interaction.response.send_message(

        f"✅ Verification setup completed.\n"
        f"Channel: {channel.mention}\n"
        f"Role: {role.mention}",

        ephemeral=True

    )


# ============================================================
# JOIN TO CREATE SETUP
# ============================================================

@bot.tree.command(
    name="jointocreate",
    description="Create a Join to Create voice system."
)
@app_commands.describe(
    category="Category for the Join to Create channel."
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def jointocreate(

    interaction: discord.Interaction,

    category: discord.CategoryChannel

):

    guild_id = str(
        interaction.guild.id
    )

    if guild_id not in config:

        config[guild_id] = {}

    # If an old JTC trigger exists,
    # remove ONLY the old trigger.

    old_id = config[guild_id].get(
        "jtc_channel_id"
    )

    if old_id:

        old_channel = (
            interaction.guild.get_channel(
                old_id
            )
        )

        if old_channel:

            try:

                await old_channel.delete()

            except Exception:

                pass

    # CREATE PERMANENT TRIGGER CHANNEL

    channel = (
        await interaction.guild.create_voice_channel(

            name="Join To Create",

            category=category

        )
    )

    # Save ONLY the trigger channel ID

    config[guild_id][
        "jtc_channel_id"
    ] = channel.id

    # Keep temporary channels list

    config[guild_id].setdefault(
        "temporary_channels",
        []
    )

    save_config()

    await interaction.response.send_message(

        f"✅ Join to Create has been set up!\n\n"
        f"🔊 Trigger channel: {channel.mention}\n\n"
        "When somebody joins it, a temporary "
        "voice channel will be created and "
        "they will automatically be moved into it.",

        ephemeral=True

    )


# ============================================================
# JOIN TO CREATE VOICE SYSTEM
# ============================================================

@bot.event
async def on_voice_state_update(

    member,

    before,

    after

):

    guild_id = str(
        member.guild.id
    )

    guild_config = config.get(
        guild_id,
        {}
    )

    jtc_id = guild_config.get(
        "jtc_channel_id"
    )

    if not jtc_id:
        return


    # ========================================================
    # JOINED THE PERMANENT TRIGGER
    # ========================================================

    if (

        after.channel

        and after.channel.id == jtc_id

    ):

        try:

            # Create a NEW temporary channel

            new_channel = (

                await member.guild.create_voice_channel(

                    name=f"{member.display_name}'s Channel",

                    category=after.channel.category

                )

            )

            # Store temporary channel ID

            temporary_channels = (
                guild_config.setdefault(

                    "temporary_channels",

                    []

                )
            )

            temporary_channels.append(
                new_channel.id
            )

            save_config()


            # =================================================
            # MOVE USER INTO NEW CHANNEL
            # =================================================

            await member.move_to(
                new_channel
            )

            print(

                f"Created temporary channel "
                f"'{new_channel.name}' for "
                f"{member}"

            )

        except discord.Forbidden:

            print(

                "❌ JTC ERROR: I don't have permission "
                "to create or move members."

            )

        except Exception as error:

            print(

                f"❌ JTC CREATE ERROR: {error}"

            )

        return


    # ========================================================
    # LEFT A TEMPORARY CHANNEL
    # ========================================================

    if before.channel:

        temporary_channels = (
            guild_config.get(

                "temporary_channels",

                []

            )
        )

        # IMPORTANT:
        # Only channels created by this system
        # can ever be deleted.

        if before.channel.id in temporary_channels:

            # Nobody is inside

            if len(
                before.channel.members
            ) == 0:

                channel_id = (
                    before.channel.id
                )

                try:

                    await before.channel.delete(

                        reason=(
                            "Join to Create "
                            "temporary channel empty"
                        )

                    )

                    print(

                        f"Deleted temporary "
                        f"channel {channel_id}"

                    )

                except discord.NotFound:

                    pass

                except discord.Forbidden:

                    print(

                        "❌ JTC ERROR: I don't have "
                        "permission to delete "
                        "temporary channels."

                    )

                except Exception as error:

                    print(

                        f"❌ JTC DELETE ERROR: {error}"

                    )

                # Remove from saved list

                if channel_id in temporary_channels:

                    temporary_channels.remove(
                        channel_id
                    )

                save_config()


# ============================================================
# ERROR HANDLER
# ============================================================

@bot.tree.error
async def command_error(

    interaction: discord.Interaction,

    error: app_commands.AppCommandError

):

    print(
        f"COMMAND ERROR: {repr(error)}"
    )

    if isinstance(

        error,

        app_commands.MissingPermissions

    ):

        message = (

            "❌ You need **Administrator** "
            "permission to use this command."

        )

    else:

        message = (

            "❌ Something went wrong. "
            "Check the Railway logs."

        )

    try:

        if interaction.response.is_done():

            await interaction.followup.send(

                message,

                ephemeral=True

            )

        else:

            await interaction.response.send_message(

                message,

                ephemeral=True

            )

    except Exception as error:

        print(

            f"ERROR HANDLER ERROR: {error}"

        )


# ============================================================
# START BOT
# ============================================================

print(
    "Starting Emerald Bot..."
)

bot.run(
    TOKEN
)
