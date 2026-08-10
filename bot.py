```python
import os
import json
import random
import asyncio
import re
import time

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

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ============================================================
# FILES
# ============================================================

CONFIG_FILE = "bot_config.json"


# ============================================================
# CONFIG
# ============================================================

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {
            "servers": {},
            "giveaways": {}
        }

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        data.setdefault("servers", {})
        data.setdefault("giveaways", {})

        return data

    except Exception as error:
        print(f"Could not load config: {error}")

        return {
            "servers": {},
            "giveaways": {}
        }


def save_config():
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as file:
            json.dump(config, file, indent=4)

    except Exception as error:
        print(f"Could not save config: {error}")


config = load_config()


# ============================================================
# COLOURS
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
    "grey": discord.Color.grey()
}


COLOR_CHOICES = [
    app_commands.Choice(name="Green", value="green"),
    app_commands.Choice(name="Red", value="red"),
    app_commands.Choice(name="Blue", value="blue"),
    app_commands.Choice(name="Purple", value="purple"),
    app_commands.Choice(name="Orange", value="orange"),
    app_commands.Choice(name="Yellow", value="yellow"),
    app_commands.Choice(name="Pink", value="pink"),
    app_commands.Choice(name="Gold", value="gold"),
    app_commands.Choice(name="Teal", value="teal"),
    app_commands.Choice(name="Black", value="black"),
    app_commands.Choice(name="White", value="white"),
    app_commands.Choice(name="Gray", value="gray")
]


def get_color(value: str):
    value = value.lower().strip()

    # Named colour
    if value in COLORS:
        return COLORS[value]

    # Hex colour
    if value.startswith("#"):
        try:
            number = int(value[1:], 16)

            if 0 <= number <= 0xFFFFFF:
                return discord.Color(number)

        except ValueError:
            pass

    return discord.Color.green()


# ============================================================
# DURATION PARSER
# Examples:
# 10s
# 5m
# 2h
# 1d
# 1w
# ============================================================

def parse_duration(duration: str):

    duration = duration.lower().strip()

    match = re.fullmatch(r"(\d+)\s*([smhdw])", duration)

    if not match:
        return None

    amount = int(match.group(1))
    unit = match.group(2)

    multipliers = {
        "s": 1,
        "m": 60,
        "h": 60 * 60,
        "d": 60 * 60 * 24,
        "w": 60 * 60 * 24 * 7
    }

    seconds = amount * multipliers[unit]

    if seconds <= 0:
        return None

    return seconds


def format_duration(seconds: int):

    if seconds < 60:
        return f"{seconds} second(s)"

    if seconds < 3600:
        return f"{seconds // 60} minute(s)"

    if seconds < 86400:
        return f"{seconds // 3600} hour(s)"

    return f"{seconds // 86400} day(s)"


# ============================================================
# VERIFY VIEW
# ============================================================

class VerifyView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verify",
        style=discord.ButtonStyle.success,
        emoji="✅",
        custom_id="emerald_verify_button"
    )
    async def verify_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ This button can only be used inside a server.",
                ephemeral=True
            )
            return

        guild_id = str(interaction.guild.id)

        server_config = config["servers"].get(
            guild_id,
            {}
        )

        role_id = server_config.get("verify_role_id")

        if not role_id:
            await interaction.response.send_message(
                "❌ Verification has not been configured in this server.",
                ephemeral=True
            )
            return

        role = interaction.guild.get_role(role_id)

        if role is None:
            await interaction.response.send_message(
                "❌ The verification role no longer exists.",
                ephemeral=True
            )
            return

        member = interaction.guild.get_member(
            interaction.user.id
        )

        if member is None:
            await interaction.response.send_message(
                "❌ I couldn't find your member information.",
                ephemeral=True
            )
            return

        if role in member.roles:
            await interaction.response.send_message(
                "✅ You are already verified!",
                ephemeral=True
            )
            return

        try:

            await member.add_roles(
                role,
                reason="Verification button"
            )

            await interaction.response.send_message(
                f"✅ You are now verified and received {role.mention}!",
                ephemeral=True
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ I can't give you the verification role. "
                "Make sure my bot role is above the verification role.",
                ephemeral=True
            )

        except Exception as error:

            print(f"Verification error: {error}")

            await interaction.response.send_message(
                "❌ Something went wrong while verifying you.",
                ephemeral=True
            )


# ============================================================
# GIVEAWAY VIEW
# ============================================================

class GiveawayView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Enter Giveaway",
        style=discord.ButtonStyle.success,
        emoji="🎉",
        custom_id="emerald_giveaway_enter"
    )
    async def enter_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.guild is None:
            return

        # Find giveaway using the message ID
        message_id = str(interaction.message.id)

        giveaway = config["giveaways"].get(
            message_id
        )

        if not giveaway:
            await interaction.response.send_message(
                "❌ This giveaway no longer exists.",
                ephemeral=True
            )
            return

        if giveaway.get("ended", False):
            await interaction.response.send_message(
                "❌ This giveaway has already ended.",
                ephemeral=True
            )
            return

        user_id = interaction.user.id

        entries = giveaway.setdefault(
            "entries",
            []
        )

        if user_id in entries:

            await interaction.response.send_message(
                "❌ You are already entered!",
                ephemeral=True
            )

            return

        entries.append(user_id)

        save_config()

        await interaction.response.send_message(
            "🎉 You have entered the giveaway!",
            ephemeral=True
        )


# ============================================================
# BOT SETUP HOOK
# ============================================================

@bot.event
async def setup_hook():

    # Register persistent buttons
    bot.add_view(
        VerifyView()
    )

    bot.add_view(
        GiveawayView()
    )

    # Sync GLOBAL slash commands
    try:

        synced = await bot.tree.sync()

        print(
            f"Successfully synced {len(synced)} global commands."
        )

        for command in synced:
            print(
                f"Registered global command: /{command.name}"
            )

    except Exception as error:

        print(
            f"Global command sync failed: {error}"
        )


# ============================================================
# BOT READY
# ============================================================

@bot.event
async def on_ready():

    print("========================================")
    print(f"Logged in as: {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print("========================================")

    try:

        await bot.change_presence(
            status=discord.Status.online,
            activity=discord.Streaming(
                name=".gg/emerald",
                url="https://www.twitch.tv/emerald"
            )
        )

        print(
            "Streaming status: .gg/emerald"
        )

    except Exception as error:

        print(
            f"Could not set status: {error}"
        )

    # Resume giveaways after restart
    for message_id in list(
        config["giveaways"].keys()
    ):

        giveaway = config["giveaways"][message_id]

        if not giveaway.get("ended", False):

            bot.loop.create_task(
                finish_giveaway(
                    message_id
                )
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
            "Here are all of my available commands."
        ),
        color=discord.Color.green()
    )

    embed.add_field(
        name="🛠️ Moderation",
        value=(
            "`/role` — Give a member a role.\n"
            "`/kick` — Kick a member.\n"
            "`/ban` — Ban a member."
        ),
        inline=False
    )

    embed.add_field(
        name="👋 Welcome",
        value=(
            "`/welcomesetup` — Configure welcome messages."
        ),
        inline=False
    )

    embed.add_field(
        name="✅ Verification",
        value=(
            "`/verifysetup` — Set up the verification system."
        ),
        inline=False
    )

    embed.add_field(
        name="🎉 Giveaways",
        value=(
            "`/giveaway` — Start a giveaway."
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
# WELCOME SETUP
# ============================================================

@bot.tree.command(
    name="welcomesetup",
    description="Set up the welcome system."
)
@app_commands.describe(
    channel="The channel for welcome messages.",
    message="Welcome message. Use {user} to mention the member.",
    embed="Choose whether to use an embed.",
    color="Choose the embed colour.",
    image_url="Optional image URL."
)
@app_commands.choices(
    embed=[
        app_commands.Choice(
            name="Yes",
            value="yes"
        ),
        app_commands.Choice(
            name="No",
            value="no"
        )
    ],
    color=COLOR_CHOICES
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def welcomesetup(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    message: str,
    embed: app_commands.Choice[str],
    color: app_commands.Choice[str],
    image_url: str = ""
):

    guild_id = str(
        interaction.guild.id
    )

    use_embed = (
        embed.value == "yes"
    )

    welcome_data = {
        "channel_id": channel.id,
        "message": message,
        "embed": use_embed,
        "color": color.value,
        "image_url": image_url.strip()
    }

    server = config["servers"].setdefault(
        guild_id,
        {}
    )

    server["welcome"] = welcome_data

    save_config()

    await interaction.response.send_message(
        "✅ **Welcome system configured!**\n\n"
        f"**Channel:** {channel.mention}\n"
        f"**Embed:** {embed.name}\n"
        f"**Colour:** {color.name}\n"
        f"**Image:** "
        f"{image_url.strip() if image_url.strip() else 'None'}",
        ephemeral=True
    )


# ============================================================
# WELCOME MESSAGE
# ============================================================

@bot.event
async def on_member_join(
    member: discord.Member
):

    guild_id = str(
        member.guild.id
    )

    server = config["servers"].get(
        guild_id
    )

    if not server:
        return

    welcome = server.get(
        "welcome"
    )

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

    # Normal message
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
                f"Welcome message error: {error}"
            )

        return

    # Embed
    embed_color = get_color(
        welcome.get(
            "color",
            "green"
        )
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

        print(
            f"Welcome embed error: {error}"
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
@app_commands.checks.has_permissions(
    administrator=True
)
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
            "❌ I couldn't find my bot member.",
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

        await user.add_roles(
            role,
            reason=f"Role command by {interaction.user}"
        )

        await interaction.response.send_message(
            f"✅ {role.mention} has been given to {user.mention}."
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ I don't have permission to give that role.",
            ephemeral=True
        )

    except Exception as error:

        print(
            f"Role error: {error}"
        )

        await interaction.response.send_message(
            "❌ Something went wrong.",
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
            f"**Reason:** {reason}"
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ I don't have permission to kick this member.",
            ephemeral=True
        )

    except Exception as error:

        print(
            f"Kick error: {error}"
        )

        await interaction.response.send_message(
            "❌ Something went wrong.",
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
            f"**Reason:** {reason}"
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ I don't have permission to ban this member.",
            ephemeral=True
        )

    except Exception as error:

        print(
            f"Ban error: {error}"
        )

        await interaction.response.send_message(
            "❌ Something went wrong.",
            ephemeral=True
        )


# ============================================================
# VERIFY SETUP
# ============================================================

@bot.tree.command(
    name="verifysetup",
    description="Set up the verification system."
)
@app_commands.describe(
    channel="The channel where the verification button will be sent.",
    role="The role users receive after verifying."
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def verifysetup(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    role: discord.Role
):

    bot_member = interaction.guild.me

    if bot_member is None:

        await interaction.response.send_message(
            "❌ I couldn't find my bot member.",
            ephemeral=True
        )

        return

    if role.is_default():

        await interaction.response.send_message(
            "❌ You cannot use @everyone as the verification role.",
            ephemeral=True
        )

        return

    if role >= bot_member.top_role:

        await interaction.response.send_message(
            "❌ The verification role must be below my bot role.",
            ephemeral=True
        )

        return

    guild_id = str(
        interaction.guild.id
    )

    server = config["servers"].setdefault(
        guild_id,
        {}
    )

    server["verify_role_id"] = role.id

    save_config()

    embed = discord.Embed(
        title="✅ Verification",
        description=(
            "Click the button below to verify yourself."
        ),
        color=discord.Color.green()
    )

    await channel.send(
        embed=embed,
        view=VerifyView()
    )

    await interaction.response.send_message(
        f"✅ Verification system created in {channel.mention}.\n"
        f"Users will receive {role.mention}.",
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
    duration="Duration such as 10m, 2h, or 1d.",
    winners="Number of winners.",
    prize="What is being given away?",
    channel="Channel for the giveaway."
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def giveaway(
    interaction: discord.Interaction,
    duration: str,
    winners: app_commands.Range[int, 1, 20],
    prize: str,
    channel: discord.TextChannel
):

    seconds = parse_duration(
        duration
    )

    if seconds is None:

        await interaction.response.send_message(
            "❌ Invalid duration.\n"
            "Use formats such as `10s`, `10m`, `2h`, `1d`, or `1w`.",
            ephemeral=True
        )

        return

    if seconds > 60 * 60 * 24 * 30:

        await interaction.response.send_message(
            "❌ The maximum giveaway duration is 30 days.",
            ephemeral=True
        )

        return

    end_time = int(
        time.time() + seconds
    )

    embed = discord.Embed(
        title="🎉 GIVEAWAY 🎉",
        description=(
            f"**Prize:** {prize}\n\n"
            f"**Winners:** {winners}\n"
            f"**Duration:** {format_duration(seconds)}\n\n"
            "Click **Enter Giveaway** below to enter!"
        ),
        color=discord.Color.green()
    )

    embed.set_footer(
        text="Good luck!"
    )

    await interaction.response.send_message(
        "🎉 Creating giveaway...",
        ephemeral=True
    )

    giveaway_message = await channel.send(
        embed=embed,
        view=GiveawayView()
    )

    message_id = str(
        giveaway_message.id
    )

    config["giveaways"][message_id] = {
        "guild_id": interaction.guild.id,
        "channel_id": channel.id,
        "prize": prize,
        "winners": winners,
        "end_time": end_time,
        "entries": [],
        "ended": False
    }

    save_config()

    await interaction.edit_original_response(
        content=(
            f"✅ Giveaway created in {channel.mention}!"
        )
    )

    bot.loop.create_task(
        finish_giveaway(
            message_id
        )
    )


# ============================================================
# FINISH GIVEAWAY
# ============================================================

async def finish_giveaway(
    message_id: str
):

    giveaway = config["giveaways"].get(
        message_id
    )

    if not giveaway:
        return

    if giveaway.get(
        "ended",
        False
    ):
        return

    remaining = (
        giveaway["end_time"]
        - int(time.time())
    )

    if remaining > 0:

        await asyncio.sleep(
            remaining
        )

    giveaway = config["giveaways"].get(
        message_id
    )

    if not giveaway:
        return

    if giveaway.get(
        "ended",
        False
    ):
        return

    giveaway["ended"] = True

    save_config()

    guild = bot.get_guild(
        giveaway["guild_id"]
    )

    if guild is None:
        return

    channel = guild.get_channel(
        giveaway["channel_id"]
    )

    if channel is None:
        return

    try:

        message = await channel.fetch_message(
            int(message_id)
        )

    except Exception:

        message = None

    entries = giveaway.get(
        "entries",
        []
    )

    if not entries:

        result = discord.Embed(
            title="🎉 Giveaway Ended",
            description=(
                f"**Prize:** {giveaway['prize']}\n\n"
                "❌ Nobody entered the giveaway."
            ),
            color=discord.Color.green()
        )

        if message:

            try:
                await message.edit(
                    embed=result,
                    view=None
                )
            except Exception:
                pass

        return

    winner_count = min(
        giveaway["winners"],
        len(entries)
    )

    selected = random.sample(
        entries,
        winner_count
    )

    mentions = []

    for user_id in selected:

        member = guild.get_member(
            user_id
        )

        if member:

            mentions.append(
                member.mention
            )

    result = discord.Embed(
        title="🎉 Giveaway Ended!",
        description=(
            f"**Prize:** {giveaway['prize']}\n\n"
            f"**Winner(s):** "
            f"{', '.join(mentions) if mentions else 'Unknown'}"
        ),
        color=discord.Color.green()
    )

    if message:

        try:

            await message.edit(
                embed=result,
                view=None
            )

        except Exception as error:

            print(
                f"Could not edit giveaway: {error}"
            )

    if mentions:

        await channel.send(
            f"🎉 Congratulations {', '.join(mentions)}! "
            f"You won **{giveaway['prize']}**!"
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
            "❌ **Administrator permission required.**"
        )

    elif isinstance(
        error,
        app_commands.CommandOnCooldown
    ):

        message = (
            "❌ This command is on cooldown."
        )

    else:

        print(
            f"Command error: {repr(error)}"
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

    except Exception as error:

        print(
            f"Could not send command error: {error}"
        )


# ============================================================
# START BOT
# ============================================================

bot.run(TOKEN)
```
