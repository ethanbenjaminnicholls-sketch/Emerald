import os
import json
import random
import asyncio
import re
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
# BOT SETUP
# ============================================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True

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
        return {
            "welcome": {},
            "verify": {},
            "jointocreate": {}
        }

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            config = json.load(file)

        config.setdefault("welcome", {})
        config.setdefault("verify", {})
        config.setdefault("jointocreate", {})

        return config

    except Exception as error:
        print(f"Could not load config: {error}")

        return {
            "welcome": {},
            "verify": {},
            "jointocreate": {}
        }


def save_config():
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as file:
            json.dump(config, file, indent=4)

    except Exception as error:
        print(f"Could not save config: {error}")


config = load_config()


# ============================================================
# COLORS
# ============================================================

COLORS = {
    "red": discord.Color.red(),
    "green": discord.Color.green(),
    "blue": discord.Color.blue(),
    "purple": discord.Color.purple(),
    "orange": discord.Color.orange(),
    "yellow": discord.Color.yellow(),
    "pink": discord.Color.magenta(),
    "gold": discord.Color.gold(),
    "teal": discord.Color.teal(),
    "black": discord.Color.from_rgb(0, 0, 0),
    "white": discord.Color.from_rgb(255, 255, 255),
    "gray": discord.Color.grey(),
    "grey": discord.Color.grey(),
}


def get_color(value):
    value = value.lower().strip()

    if value.startswith("#"):
        try:
            number = int(value[1:], 16)

            if 0 <= number <= 0xFFFFFF:
                return discord.Color(number)

        except ValueError:
            pass

    return COLORS.get(value, discord.Color.green())


# ============================================================
# DURATION PARSER
# ============================================================

def parse_duration(duration):
    """
    Examples:

    10s
    10m
    2h
    1d
    """

    duration = duration.lower().strip()

    match = re.fullmatch(r"(\d+)\s*([smhd])", duration)

    if not match:
        return None

    amount = int(match.group(1))
    unit = match.group(2)

    if unit == "s":
        return amount

    if unit == "m":
        return amount * 60

    if unit == "h":
        return amount * 60 * 60

    if unit == "d":
        return amount * 60 * 60 * 24

    return None


# ============================================================
# BOT READY
# ============================================================

@bot.event
async def on_ready():

    print("========================================")
    print(f"Logged in as: {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print("========================================")

    # Streaming status
    try:
        await bot.change_presence(
            status=discord.Status.online,
            activity=discord.Streaming(
                name=".gg/emerald",
                url="https://www.twitch.tv/emerald"
            )
        )

        print("✅ Status: Streaming .gg/emerald")

    except Exception as error:
        print(f"❌ Could not set status: {error}")

    # GLOBAL slash commands
    try:
        synced = await bot.tree.sync()

        print(f"✅ Synced {len(synced)} GLOBAL commands:")

        for command in synced:
            print(f"   /{command.name}")

    except Exception as error:
        print(f"❌ Failed to sync commands: {error}")


# ============================================================
# WELCOME SETUP
# ============================================================

@bot.tree.command(
    name="welcomesetup",
    description="Set up the server welcome system."
)
@app_commands.describe(
    channel="The channel where welcome messages are sent.",
    message="Welcome message. Use {user} to mention the member.",
    embed="Use an embed? yes or no.",
    color="Embed colour, such as green, red, blue, purple or #00ff00.",
    image_url="Optional image URL."
)
@app_commands.checks.has_permissions(administrator=True)
async def welcomesetup(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    message: str,
    embed: str = "no",
    color: str = "green",
    image_url: str = ""
):

    guild_id = str(interaction.guild.id)

    use_embed = embed.lower().strip() in (
        "yes",
        "y",
        "true",
        "on"
    )

    color_name = color.lower().strip()

    config["welcome"][guild_id] = {
        "channel_id": channel.id,
        "message": message,
        "embed": use_embed,
        "color": color_name,
        "image_url": image_url.strip()
    }

    save_config()

    await interaction.response.send_message(
        "✅ **Welcome system configured!**\n\n"
        f"**Channel:** {channel.mention}\n"
        f"**Embed:** {'Yes' if use_embed else 'No'}\n"
        f"**Colour:** `{color_name}`\n"
        f"**Image:** `{image_url.strip() if image_url.strip() else 'None'}`",
        ephemeral=True
    )


# ============================================================
# WELCOME MESSAGE
# ============================================================

@bot.event
async def on_member_join(member):

    guild_id = str(member.guild.id)

    welcome = config["welcome"].get(guild_id)

    if not welcome:
        return

    channel = member.guild.get_channel(
        welcome.get("channel_id")
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
    if not welcome.get("embed", False):

        try:
            await channel.send(message)

        except Exception as error:
            print(f"Welcome message error: {error}")

        return

    # EMBED
    embed_color = get_color(
        welcome.get("color", "green")
    )

    welcome_embed = discord.Embed(
        description=message,
        color=embed_color
    )

    # Member avatar
    welcome_embed.set_thumbnail(
        url=member.display_avatar.url
    )

    # Optional image
    image_url = welcome.get(
        "image_url",
        ""
    ).strip()

    if image_url:
        welcome_embed.set_image(
            url=image_url
        )

    try:
        await channel.send(
            embed=welcome_embed
        )

    except Exception as error:
        print(f"Welcome embed error: {error}")


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
        description="Here are all available commands.",
        color=discord.Color.green()
    )

    embed.add_field(
        name="🛠️ Moderation",
        value=(
            "`/kick` — Kick a member\n"
            "`/ban` — Ban a member\n"
            "`/timeout` — Timeout a member\n"
            "`/role` — Give a role"
        ),
        inline=False
    )

    embed.add_field(
        name="👋 Server",
        value=(
            "`/welcomesetup` — Configure welcomes\n"
            "`/verifysetup` — Configure verification\n"
            "`/jointocreate` — Configure Join to Create"
        ),
        inline=False
    )

    embed.add_field(
        name="🎉 Fun",
        value=(
            "`/giveaway` — Start a giveaway"
        ),
        inline=False
    )

    embed.set_footer(
        text=".gg/emerald"
    )

    await interaction.response.send_message(
        embed=embed
    )


# ============================================================
# ROLE
# ============================================================

@bot.tree.command(
    name="role",
    description="Give a member a role."
)
@app_commands.describe(
    user="The member.",
    role="The role to give."
)
@app_commands.checks.has_permissions(administrator=True)
async def role(
    interaction: discord.Interaction,
    user: discord.Member,
    role: discord.Role
):

    bot_member = interaction.guild.me

    if role.is_default():
        await interaction.response.send_message(
            "❌ You cannot give the @everyone role.",
            ephemeral=True
        )
        return

    if bot_member is None:
        await interaction.response.send_message(
            "❌ I couldn't find my member information.",
            ephemeral=True
        )
        return

    if role >= bot_member.top_role:
        await interaction.response.send_message(
            "❌ That role is above or equal to my highest role.",
            ephemeral=True
        )
        return

    try:
        await user.add_roles(role)

        await interaction.response.send_message(
            f"✅ {role.mention} has been given to {user.mention}."
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I don't have permission to give that role.",
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
    user="The member to kick.",
    reason="Reason for the kick."
)
@app_commands.checks.has_permissions(administrator=True)
async def kick(
    interaction: discord.Interaction,
    user: discord.Member,
    reason: str = "No reason provided"
):

    try:
        await user.kick(reason=reason)

        await interaction.response.send_message(
            f"👢 **{user}** was kicked.\n"
            f"**Reason:** {reason}"
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
    user="The member to ban.",
    reason="Reason for the ban."
)
@app_commands.checks.has_permissions(administrator=True)
async def ban(
    interaction: discord.Interaction,
    user: discord.Member,
    reason: str = "No reason provided"
):

    try:
        await user.ban(reason=reason)

        await interaction.response.send_message(
            f"🔨 **{user}** was banned.\n"
            f"**Reason:** {reason}"
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
    user="The member to timeout.",
    duration="Duration: 10s, 10m, 2h or 1d.",
    reason="Reason for the timeout."
)
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(
    interaction: discord.Interaction,
    user: discord.Member,
    duration: str,
    reason: str = "No reason provided"
):

    seconds = parse_duration(duration)

    if seconds is None:
        await interaction.response.send_message(
            "❌ Invalid duration. Use something like `10m`, `2h` or `1d`.",
            ephemeral=True
        )
        return

    if seconds > 28 * 24 * 60 * 60:
        await interaction.response.send_message(
            "❌ Discord does not allow a timeout longer than 28 days.",
            ephemeral=True
        )
        return

    try:

        await user.timeout(
            timedelta(seconds=seconds),
            reason=reason
        )

        await interaction.response.send_message(
            f"⏱️ **{user}** has been timed out for `{duration}`.\n"
            f"**Reason:** {reason}"
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I cannot timeout that member.",
            ephemeral=True
        )


# ============================================================
# GIVEAWAY
# ============================================================

async def finish_giveaway(
    channel,
    message_id,
    prize,
    winners
):

    try:
        giveaway_message = await channel.fetch_message(
            message_id
        )

    except Exception:
        return

    entries = []

    for reaction in giveaway_message.reactions:

        if str(reaction.emoji) == "🎉":

            try:
                users = [
                    user async for user in reaction.users()
                ]

                entries = [
                    user for user in users
                    if not user.bot
                ]

            except Exception:
                pass

    if not entries:

        await channel.send(
            f"🎉 **Giveaway ended!**\n"
            f"Prize: **{prize}**\n"
            f"Nobody entered."
        )

        return

    winners = min(winners, len(entries))

    selected = random.sample(
        entries,
        winners
    )

    mentions = ", ".join(
        user.mention for user in selected
    )

    await channel.send(
        f"🎉 **Giveaway ended!**\n\n"
        f"**Prize:** {prize}\n"
        f"🏆 **Winner(s):** {mentions}"
    )


@bot.tree.command(
    name="giveaway",
    description="Start a giveaway."
)
@app_commands.describe(
    duration="Duration: 10s, 10m, 1h or 1d.",
    prize="What are you giving away?",
    winners="Number of winners."
)
@app_commands.checks.has_permissions(manage_guild=True)
async def giveaway(
    interaction: discord.Interaction,
    duration: str,
    prize: str,
    winners: int = 1
):

    seconds = parse_duration(duration)

    if seconds is None:
        await interaction.response.send_message(
            "❌ Invalid duration. Example: `10m`, `2h`, `1d`.",
            ephemeral=True
        )
        return

    if winners < 1 or winners > 50:
        await interaction.response.send_message(
            "❌ Winners must be between 1 and 50.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="🎉 GIVEAWAY",
        description=(
            f"**Prize:** {prize}\n\n"
            f"React with 🎉 to enter!\n\n"
            f"**Winners:** {winners}\n"
            f"**Duration:** {duration}"
        ),
        color=discord.Color.green()
    )

    embed.set_footer(
        text="Emerald Giveaways"
    )

    await interaction.response.send_message(
        embed=embed
    )

    giveaway_message = await interaction.original_response()

    await giveaway_message.add_reaction("🎉")

    await asyncio.sleep(seconds)

    await finish_giveaway(
        interaction.channel,
        giveaway_message.id,
        prize,
        winners
    )


# ============================================================
# VERIFY SETUP
# ============================================================

class VerifyButton(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verify",
        style=discord.ButtonStyle.green,
        emoji="✅",
        custom_id="emerald_verify"
    )
    async def verify(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        guild_id = str(interaction.guild.id)

        verify_config = config["verify"].get(
            guild_id
        )

        if not verify_config:
            await interaction.response.send_message(
                "❌ Verification has not been configured.",
                ephemeral=True
            )
            return

        role = interaction.guild.get_role(
            verify_config["role_id"]
        )

        if role is None:
            await interaction.response.send_message(
                "❌ The verified role no longer exists.",
                ephemeral=True
            )
            return

        try:

            await interaction.user.add_roles(role)

            await interaction.response.send_message(
                "✅ You have been verified!",
                ephemeral=True
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ I cannot give you the verified role.",
                ephemeral=True
            )


@bot.tree.command(
    name="verifysetup",
    description="Set up the verification system."
)
@app_commands.describe(
    channel="The channel for verification.",
    role="The role members receive when verified."
)
@app_commands.checks.has_permissions(administrator=True)
async def verifysetup(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    role: discord.Role
):

    guild_id = str(interaction.guild.id)

    config["verify"][guild_id] = {
        "channel_id": channel.id,
        "role_id": role.id
    }

    save_config()

    embed = discord.Embed(
        title="✅ Verification",
        description=(
            "Click the button below to verify yourself "
            "and receive the verified role."
        ),
        color=discord.Color.green()
    )

    embed.set_footer(
        text="Emerald Verification"
    )

    await channel.send(
        embed=embed,
        view=VerifyButton()
    )

    await interaction.response.send_message(
        f"✅ Verification setup complete!\n"
        f"**Channel:** {channel.mention}\n"
        f"**Role:** {role.mention}",
        ephemeral=True
    )


# ============================================================
# JOIN TO CREATE
# ============================================================

@bot.tree.command(
    name="jointocreate",
    description="Set up a Join to Create voice channel."
)
@app_commands.describe(
    category="Category where the Join to Create channel will be placed."
)
@app_commands.checks.has_permissions(administrator=True)
async def jointocreate(
    interaction: discord.Interaction,
    category: discord.CategoryChannel
):

    guild_id = str(interaction.guild.id)

    channel = await interaction.guild.create_voice_channel(
        "Join to Create",
        category=category
    )

    config["jointocreate"][guild_id] = {
        "channel_id": channel.id,
        "category_id": category.id
    }

    save_config()

    await interaction.response.send_message(
        f"✅ **Join to Create enabled!**\n\n"
        f"Users can join {channel.mention} to create their own voice channel.",
        ephemeral=True
    )


# ============================================================
# JOIN TO CREATE SYSTEM
# ============================================================

@bot.event
async def on_voice_state_update(
    member,
    before,
    after
):

    guild_id = str(member.guild.id)

    jtc = config["jointocreate"].get(
        guild_id
    )

    if not jtc:
        return

    trigger_id = jtc.get(
        "channel_id"
    )

    category_id = jtc.get(
        "category_id"
    )

    # User joined Join to Create
    if after.channel and after.channel.id == trigger_id:

        category = member.guild.get_channel(
            category_id
        )

        if category is None:
            return

        try:

            new_channel = await member.guild.create_voice_channel(
                name=f"{member.display_name}'s Channel",
                category=category
            )

            await member.move_to(
                new_channel
            )

        except discord.Forbidden:

            print(
                f"Could not create JTC channel in {member.guild.name}"
            )

    # Delete empty temporary channel
    if before.channel:

        channel = before.channel

        if channel.category_id == category_id:

            if channel.id != trigger_id:

                if len(channel.members) == 0:

                    try:
                        await channel.delete(
                            reason="Empty Join to Create channel"
                        )

                    except Exception:
                        pass


# ============================================================
# GLOBAL PERSISTENT VERIFY VIEW
# ============================================================

@bot.event
async def setup_hook():

    bot.add_view(
        VerifyButton()
    )


# ============================================================
# COMMAND ERROR HANDLER
# ============================================================

@bot.tree.error
async def command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
):

    if isinstance(
        error,
        app_commands.MissingPermissions
    ):

        message = (
            "❌ You do not have the required permissions "
            "to use this command."
        )

    elif isinstance(
        error,
        app_commands.BotMissingPermissions
    ):

        message = (
            "❌ I don't have the permissions required "
            "to perform that action."
        )

    else:

        print(
            f"Command error: {error}"
        )

        message = (
            "❌ An unexpected error occurred."
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

    except Exception as send_error:

        print(
            f"Could not send error message: {send_error}"
        )


# ============================================================
# START BOT
# ============================================================

bot.run(TOKEN)
