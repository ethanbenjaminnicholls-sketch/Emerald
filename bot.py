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
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except Exception as error:
        print(f"Config load error: {error}")
        return {}


def save_config():
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as file:
            json.dump(config, file, indent=4)

    except Exception as error:
        print(f"Config save error: {error}")


config = load_config()


def get_guild_config(guild_id):
    guild_id = str(guild_id)

    if guild_id not in config:
        config[guild_id] = {}

    return config[guild_id]


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
  "gray": discord.Color.dark_gray(),
"grey": discord.Color.dark_gray()
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

def parse_duration(value):
    """
    Examples:
    10s
    5m
    2h
    1d
    """

    match = re.fullmatch(
        r"(\d+)\s*(s|m|h|d)",
        value.lower().strip()
    )

    if not match:
        return None

    number = int(match.group(1))
    unit = match.group(2)

    if unit == "s":
        return number

    if unit == "m":
        return number * 60

    if unit == "h":
        return number * 60 * 60

    if unit == "d":
        return number * 60 * 60 * 24

    return None


# ============================================================
# READY
# ============================================================

@bot.event
async def on_ready():

    print("========================================")
    print(f"Logged in as: {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print("========================================")

    # --------------------------------------------------------
    # GLOBAL COMMAND SYNC
    # --------------------------------------------------------

    try:
        synced = await bot.tree.sync()

        print(f"SYNCED {len(synced)} GLOBAL COMMANDS:")

        for command in synced:
            print(f"  /{command.name}")

    except Exception as error:
        print(f"GLOBAL COMMAND SYNC ERROR: {error}")

    # --------------------------------------------------------
    # STREAMING STATUS
    # --------------------------------------------------------

    try:
        await bot.change_presence(
            status=discord.Status.online,
            activity=discord.Streaming(
                name=".gg/emerald",
                url="https://www.twitch.tv/emerald"
            )
        )

        print("Status: Streaming .gg/emerald")

    except Exception as error:
        print(f"Status error: {error}")

    print("========================================")


# ============================================================
# HELP
# ============================================================

@bot.tree.command(
    name="help",
    description="Show all available bot commands."
)
async def help_command(interaction: discord.Interaction):

    embed = discord.Embed(
        title="💚 Emerald Help",
        description="Here are all of my available commands.",
        color=discord.Color.green()
    )

    embed.add_field(
        name="🛠️ Moderation",
        value=(
            "`/kick` — Kick a member\n"
            "`/ban` — Ban a member\n"
            "`/timeout` — Timeout a member\n"
            "`/role` — Give a role to a member"
        ),
        inline=False
    )

    embed.add_field(
        name="👋 Welcome",
        value=(
            "`/welcomesetup` — Configure welcome messages\n"
            "Supports normal messages, embeds, colors and images."
        ),
        inline=False
    )

    embed.add_field(
        name="🎉 Giveaways",
        value=(
            "`/giveaway` — Start a giveaway\n"
            "Members can enter using the button."
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
        name="🔊 Voice",
        value=(
            "`/jointocreate` — Create a Join To Create voice system."
        ),
        inline=False
    )

    embed.set_footer(
        text="Emerald • .gg/emerald"
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
    channel="The channel where welcome messages are sent.",
    message="Welcome message. Use {user} to mention the member.",
    embed="Use an embed? Type yes or no.",
    color="Embed color such as green, red, blue or #00ff00.",
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

    guild_config = get_guild_config(
        interaction.guild.id
    )

    use_embed = embed.lower().strip() in (
        "yes",
        "y",
        "true",
        "on"
    )

    color_name = color.lower().strip()

    # Validate URL if supplied
    image_url = image_url.strip()

    guild_config["welcome"] = {
        "channel_id": channel.id,
        "message": message,
        "embed": use_embed,
        "color": color_name,
        "image_url": image_url
    }

    save_config()

    # Preview
    preview_message = message.replace(
        "{user}",
        interaction.user.mention
    )

    if use_embed:

        preview = discord.Embed(
            description=preview_message,
            color=get_color(color_name)
        )

        preview.set_thumbnail(
            url=interaction.user.display_avatar.url
        )

        if image_url:
            preview.set_image(
                url=image_url
            )

        await interaction.response.send_message(
            "✅ **Welcome system configured!**",
            embed=preview,
            ephemeral=True
        )

    else:

        await interaction.response.send_message(
            "✅ **Welcome system configured!**\n\n"
            f"**Channel:** {channel.mention}\n"
            f"**Embed:** No",
            ephemeral=True
        )


# ============================================================
# WELCOME EVENT
# ============================================================

@bot.event
async def on_member_join(member):

    guild_config = get_guild_config(
        member.guild.id
    )

    welcome = guild_config.get("welcome")

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

    # --------------------------------------------------------
    # NORMAL MESSAGE
    # --------------------------------------------------------

    if not welcome.get("embed", False):

        try:
            await channel.send(message)

        except Exception as error:
            print(f"Welcome error: {error}")

        return

    # --------------------------------------------------------
    # EMBED
    # --------------------------------------------------------

    welcome_embed = discord.Embed(
        description=message,
        color=get_color(
            welcome.get("color", "green")
        )
    )

    # Member profile picture
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
# ROLE
# ============================================================

@bot.tree.command(
    name="role",
    description="Give a member a role."
)
@app_commands.describe(
    user="The member to give the role to.",
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

    if role >= bot_member.top_role:
        await interaction.response.send_message(
            "❌ That role is above or equal to my highest role.",
            ephemeral=True
        )
        return

    try:

        await user.add_roles(role)

        await interaction.response.send_message(
            f"✅ {role.mention} was given to {user.mention}."
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
    duration="Duration such as 10m, 1h or 1d.",
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
            "❌ Invalid duration.\n"
            "Use something like `10m`, `1h`, or `1d`.",
            ephemeral=True
        )
        return

    if seconds > 28 * 24 * 60 * 60:
        await interaction.response.send_message(
            "❌ Discord only allows timeouts up to 28 days.",
            ephemeral=True
        )
        return

    try:

        await user.timeout(
            timedelta(seconds=seconds),
            reason=reason
        )

        await interaction.response.send_message(
            f"⏱️ **{user}** has been timed out for "
            f"`{duration}`.\n"
            f"**Reason:** {reason}"
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ I cannot timeout that member.",
            ephemeral=True
        )


# ============================================================
# GIVEAWAY VIEW
# ============================================================

class GiveawayView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

        self.entries = set()

    @discord.ui.button(
        label="Enter Giveaway",
        emoji="🎉",
        style=discord.ButtonStyle.green,
        custom_id="emerald_giveaway_enter"
    )
    async def enter(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user.id in self.entries:

            self.entries.remove(
                interaction.user.id
            )

            await interaction.response.send_message(
                "You have left the giveaway.",
                ephemeral=True
            )

        else:

            self.entries.add(
                interaction.user.id
            )

            await interaction.response.send_message(
                "🎉 You entered the giveaway!",
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
    duration="Duration such as 10m, 1h or 1d.",
    winners="Number of winners.",
    prize="What are you giving away?"
)
@app_commands.checks.has_permissions(administrator=True)
async def giveaway(
    interaction: discord.Interaction,
    duration: str,
    winners: int,
    prize: str
):

    if winners < 1:
        await interaction.response.send_message(
            "❌ You need at least 1 winner.",
            ephemeral=True
        )
        return

    seconds = parse_duration(duration)

    if seconds is None:
        await interaction.response.send_message(
            "❌ Invalid duration. Use `10m`, `1h`, or `1d`.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    end_time = discord.utils.utcnow() + timedelta(
        seconds=seconds
    )

    view = GiveawayView()

    embed = discord.Embed(
        title="🎉 GIVEAWAY",
        description=(
            f"**Prize:** {prize}\n\n"
            f"**Winners:** {winners}\n"
            f"**Ends:** <t:{int(end_time.timestamp())}:R>\n\n"
            "Click **Enter Giveaway** to enter!"
        ),
        color=discord.Color.green()
    )

    embed.set_footer(
        text=f"Hosted by {interaction.user}"
    )

    message = await interaction.followup.send(
        embed=embed,
        view=view,
        wait=True
    )

    await asyncio.sleep(seconds)

    if not view.entries:

        ended = discord.Embed(
            title="🎉 GIVEAWAY ENDED",
            description=(
                f"**Prize:** {prize}\n\n"
                "❌ Nobody entered the giveaway."
            ),
            color=discord.Color.red()
        )

        await message.edit(
            embed=ended,
            view=None
        )

        return

    entry_ids = list(view.entries)

    random.shuffle(entry_ids)

    selected = entry_ids[:min(
        winners,
        len(entry_ids)
    )]

    mentions = []

    for user_id in selected:

        member = interaction.guild.get_member(
            user_id
        )

        if member:
            mentions.append(
                member.mention
            )

    ended = discord.Embed(
        title="🎉 GIVEAWAY ENDED",
        description=(
            f"**Prize:** {prize}\n\n"
            f"🏆 **Winner(s):** "
            f"{', '.join(mentions) if mentions else 'Unknown'}"
        ),
        color=discord.Color.green()
    )

    await message.edit(
        embed=ended,
        view=None
    )

    if mentions:

        await interaction.channel.send(
            f"🎉 Congratulations {', '.join(mentions)}! "
            f"You won **{prize}**!"
        )


# ============================================================
# VERIFY VIEW
# ============================================================

class VerifyView(discord.ui.View):

    def __init__(self, role_id):
        super().__init__(timeout=None)

        self.role_id = role_id

    @discord.ui.button(
        label="Verify",
        emoji="✅",
        style=discord.ButtonStyle.green,
        custom_id="emerald_verify"
    )
    async def verify(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        role = interaction.guild.get_role(
            self.role_id
        )

        if role is None:
            await interaction.response.send_message(
                "❌ The verification role no longer exists.",
                ephemeral=True
            )
            return

        if role in interaction.user.roles:

            await interaction.response.send_message(
                "✅ You are already verified!",
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
                "❌ I cannot give you the verification role.",
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
    channel="Channel where the verification panel will be sent.",
    role="Role given after verification."
)
@app_commands.checks.has_permissions(administrator=True)
async def verifysetup(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    role: discord.Role
):

    guild_config = get_guild_config(
        interaction.guild.id
    )

    guild_config["verify_role_id"] = role.id

    save_config()

    embed = discord.Embed(
        title="✅ Server Verification",
        description=(
            "Click the button below to verify yourself."
        ),
        color=discord.Color.green()
    )

    view = VerifyView(role.id)

    await channel.send(
        embed=embed,
        view=view
    )

    await interaction.response.send_message(
        f"✅ Verification system created in {channel.mention}.\n"
        f"**Verified role:** {role.mention}",
        ephemeral=True
    )


# ============================================================
# JOIN TO CREATE
# ============================================================

@bot.tree.command(
    name="jointocreate",
    description="Create a Join To Create voice system."
)
@app_commands.describe(
    category="Category where the Join To Create channel will be created."
)
@app_commands.checks.has_permissions(administrator=True)
async def jointocreate(
    interaction: discord.Interaction,
    category: discord.CategoryChannel
):

    guild_config = get_guild_config(
        interaction.guild.id
    )

    # Create the main Join To Create channel
    channel = await interaction.guild.create_voice_channel(
        "Join To Create",
        category=category
    )

    guild_config["jtc_channel_id"] = channel.id

    save_config()

    await interaction.response.send_message(
        f"✅ Join To Create has been created: {channel.mention}\n\n"
        "When someone joins it, their own voice channel will "
        "automatically be created.",
        ephemeral=True
    )


# ============================================================
# VOICE STATE
# ============================================================

@bot.event
async def on_voice_state_update(
    member,
    before,
    after
):

    guild_config = get_guild_config(
        member.guild.id
    )

    jtc_id = guild_config.get(
        "jtc_channel_id"
    )

    if not jtc_id:
        return

    # --------------------------------------------------------
    # CREATE PERSONAL CHANNEL
    # --------------------------------------------------------

    if after.channel and after.channel.id == jtc_id:

        category = after.channel.category

        try:

            new_channel = await member.guild.create_voice_channel(
                f"{member.display_name}'s Room",
                category=category
            )

            await member.move_to(
                new_channel
            )

            guild_config.setdefault(
                "temporary_channels",
                []
            )

            guild_config["temporary_channels"].append(
                new_channel.id
            )

            save_config()

        except Exception as error:
            print(
                f"JTC creation error: {error}"
            )

    # --------------------------------------------------------
    # DELETE EMPTY PERSONAL CHANNEL
    # --------------------------------------------------------

    if before.channel:

        temporary_channels = guild_config.get(
            "temporary_channels",
            []
        )

        if before.channel.id in temporary_channels:

            if len(before.channel.members) == 0:

                try:

                    channel_id = before.channel.id

                    await before.channel.delete()

                    temporary_channels.remove(
                        channel_id
                    )

                    save_config()

                except Exception as error:
                    print(
                        f"JTC deletion error: {error}"
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
            "❌ You don't have the required permissions "
            "to use this command."
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
            f"Slash command error: {error}"
        )

        message = (
            "❌ Something went wrong while running "
            "that command."
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
            f"Could not send error response: {error}"
        )


# ============================================================
# START
# ============================================================

print("Starting Emerald bot...")

bot.run(TOKEN)
