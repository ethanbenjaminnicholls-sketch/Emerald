import os
import json
import random
import re
import time
import asyncio

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
            "welcome": {},
            "verify": {},
            "giveaways": {}
        }

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        data.setdefault("welcome", {})
        data.setdefault("verify", {})
        data.setdefault("giveaways", {})

        return data

    except Exception as error:
        print(f"Could not load config: {error}")

        return {
            "welcome": {},
            "verify": {},
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
    "grey": discord.Color.grey()
}


def get_color(value):
    if not value:
        return discord.Color.green()

    value = value.lower().strip()

    if value.startswith("#"):
        try:
            number = int(value[1:], 16)

            if 0 <= number <= 0xFFFFFF:
                return discord.Color(number)

        except ValueError:
            pass

    return COLORS.get(
        value,
        discord.Color.green()
    )


# ============================================================
# DURATION PARSER
# ============================================================

def parse_duration(duration):
    """
    Examples:
    30s
    10m
    2h
    1d
    """

    match = re.fullmatch(
        r"(\d+)\s*(s|m|h|d)",
        duration.lower().strip()
    )

    if not match:
        return None

    amount = int(match.group(1))
    unit = match.group(2)

    multipliers = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400
    }

    seconds = amount * multipliers[unit]

    if seconds <= 0:
        return None

    return seconds


def format_duration(seconds):
    seconds = int(seconds)

    if seconds < 60:
        return f"{seconds}s"

    if seconds < 3600:
        return f"{seconds // 60}m"

    if seconds < 86400:
        return f"{seconds // 3600}h"

    return f"{seconds // 86400}d"


# ============================================================
# GIVEAWAY DATA
# ============================================================

giveaway_tasks = {}


# ============================================================
# VERIFY BUTTON
# ============================================================

class VerifyView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verify",
        style=discord.ButtonStyle.success,
        custom_id="emerald_verify_button"
    )
    async def verify_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "❌ This can only be used inside a server.",
                ephemeral=True
            )
            return

        guild_id = str(guild.id)

        verify_config = config["verify"].get(guild_id)

        if not verify_config:
            await interaction.response.send_message(
                "❌ Verification has not been configured.",
                ephemeral=True
            )
            return

        role = guild.get_role(
            verify_config.get("role_id")
        )

        if role is None:
            await interaction.response.send_message(
                "❌ The verification role no longer exists.",
                ephemeral=True
            )
            return

        member = interaction.user

        if role in member.roles:
            await interaction.response.send_message(
                "✅ You are already verified!",
                ephemeral=True
            )
            return

        try:
            await member.add_roles(role)

            await interaction.response.send_message(
                "✅ **You are now verified!**",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I cannot give you the verification role. "
                "Make sure my bot role is above the verification role.",
                ephemeral=True
            )

        except Exception as error:
            print(f"Verify error: {error}")

            await interaction.response.send_message(
                "❌ Something went wrong while verifying you.",
                ephemeral=True
            )


# ============================================================
# GIVEAWAY VIEW
# ============================================================

class GiveawayView(discord.ui.View):

    def __init__(self, giveaway_id):
        super().__init__(timeout=None)

        self.giveaway_id = giveaway_id

    @discord.ui.button(
        label="🎉 Enter Giveaway",
        style=discord.ButtonStyle.success
    )
    async def enter_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        giveaway = config["giveaways"].get(
            str(self.giveaway_id)
        )

        if not giveaway:
            await interaction.response.send_message(
                "❌ This giveaway no longer exists.",
                ephemeral=True
            )
            return

        if giveaway.get("ended", False):
            await interaction.response.send_message(
                "❌ This giveaway has ended.",
                ephemeral=True
            )
            return

        user_id = interaction.user.id

        entries = giveaway.setdefault(
            "entries",
            []
        )

        if user_id in entries:
            entries.remove(user_id)

            save_config()

            await interaction.response.send_message(
                "❌ You left the giveaway.",
                ephemeral=True
            )

        else:
            entries.append(user_id)

            save_config()

            await interaction.response.send_message(
                "🎉 **You entered the giveaway!**",
                ephemeral=True
            )


# ============================================================
# READY
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

        print("Status: Streaming .gg/emerald")

    except Exception as error:
        print(f"Status error: {error}")

    try:
        bot.add_view(VerifyView())

    except Exception as error:
        print(f"Verify view error: {error}")

    try:
        synced = await bot.tree.sync()

        print(
            f"Successfully synced {len(synced)} "
            "commands globally."
        )

        for command in synced:
            print(f"Registered: /{command.name}")

    except Exception as error:
        print(f"Slash command sync error: {error}")


# ============================================================
# WELCOME SETUP
# ADMINISTRATOR ONLY
# ============================================================

@bot.tree.command(
    name="welcomesetup",
    description="Set up the welcome system."
)
@app_commands.describe(
    channel="The channel for welcome messages.",
    message="Welcome message. Use {user} to mention the member.",
    embed="Use an embed for the welcome message.",
    color="Embed color, e.g. green, red, blue, or #00ff00.",
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
    ]
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def welcomesetup(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    message: str,
    embed: app_commands.Choice[str],
    color: str = "green",
    image_url: str = ""
):

    guild_id = str(interaction.guild.id)

    use_embed = embed.value == "yes"

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
        f"**Color:** `{color_name}`\n"
        f"**Image:** "
        f"`{image_url.strip() if image_url.strip() else 'None'}`",
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

    if not welcome.get("embed", False):

        try:
            await channel.send(message)

        except Exception as error:
            print(f"Welcome message error: {error}")

        return

    embed_color = get_color(
        welcome.get("color", "green")
    )

    welcome_embed = discord.Embed(
        description=message,
        color=embed_color
    )

    welcome_embed.set_thumbnail(
        url=member.display_avatar.url
    )

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
        description=(
            "Here are all of my commands.\n\n"
            "Commands marked 🔒 require Administrator."
        ),
        color=discord.Color.green()
    )

    embed.add_field(
        name="🛡️ Moderation",
        value=(
            "`/role` — Give a member a role 🔒\n"
            "`/kick` — Kick a member 🔒\n"
            "`/ban` — Ban a member 🔒"
        ),
        inline=False
    )

    embed.add_field(
        name="👋 Welcome",
        value=(
            "`/welcomesetup` — Configure welcome messages 🔒"
        ),
        inline=False
    )

    embed.add_field(
        name="🎉 Giveaways",
        value=(
            "`/giveaway` — Start a giveaway 🔒\n"
            "`/giveawayend` — End a giveaway early 🔒\n"
            "`/giveawayreroll` — Reroll winners 🔒"
        ),
        inline=False
    )

    embed.add_field(
        name="✅ Verification",
        value=(
            "`/verifysetup` — Configure verification 🔒\n"
            "`/verify` — Send the verification panel 🔒"
        ),
        inline=False
    )

    embed.set_footer(
        text=".gg/emerald"
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# ============================================================
# VERIFY SETUP
# ADMINISTRATOR ONLY
# ============================================================

@bot.tree.command(
    name="verifysetup",
    description="Set up the verification role."
)
@app_commands.describe(
    role="The role members receive when they verify."
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def verifysetup(
    interaction: discord.Interaction,
    role: discord.Role
):

    guild_id = str(interaction.guild.id)

    if role.is_default():
        await interaction.response.send_message(
            "❌ You cannot use @everyone as the verification role.",
            ephemeral=True
        )
        return

    if role >= interaction.guild.me.top_role:
        await interaction.response.send_message(
            "❌ My bot role must be above the verification role.",
            ephemeral=True
        )
        return

    config["verify"][guild_id] = {
        "role_id": role.id
    }

    save_config()

    await interaction.response.send_message(
        "✅ **Verification configured!**\n\n"
        f"Members will receive {role.mention} when they verify.",
        ephemeral=True
    )


# ============================================================
# VERIFY PANEL
# ADMINISTRATOR ONLY
# ============================================================

@bot.tree.command(
    name="verify",
    description="Send the verification panel."
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def verify(
    interaction: discord.Interaction
):

    guild_id = str(interaction.guild.id)

    verify_config = config["verify"].get(
        guild_id
    )

    if not verify_config:
        await interaction.response.send_message(
            "❌ Run `/verifysetup` first.",
            ephemeral=True
        )
        return

    role = interaction.guild.get_role(
        verify_config["role_id"]
    )

    if role is None:
        await interaction.response.send_message(
            "❌ The verification role no longer exists.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="✅ Verification",
        description=(
            "Click the button below to verify yourself "
            f"and receive {role.mention}."
        ),
        color=discord.Color.green()
    )

    embed.set_footer(
        text=".gg/emerald"
    )

    await interaction.response.send_message(
        embed=embed,
        view=VerifyView()
    )


# ============================================================
# GIVEAWAY
# ADMINISTRATOR ONLY
# ============================================================

@bot.tree.command(
    name="giveaway",
    description="Start a giveaway."
)
@app_commands.describe(
    duration="Duration such as 30s, 10m, 2h or 1d.",
    winners="Number of winners.",
    prize="What are you giving away?"
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def giveaway(
    interaction: discord.Interaction,
    duration: str,
    winners: app_commands.Range[int, 1, 100],
    prize: str
):

    seconds = parse_duration(duration)

    if seconds is None:
        await interaction.response.send_message(
            "❌ Invalid duration. Use something like "
            "`30s`, `10m`, `2h`, or `1d`.",
            ephemeral=True
        )
        return

    if seconds > 604800:
        await interaction.response.send_message(
            "❌ The maximum giveaway duration is 7 days.",
            ephemeral=True
        )
        return

    giveaway_id = str(
        int(time.time() * 1000)
    )

    end_time = time.time() + seconds

    giveaway_data = {
        "channel_id": interaction.channel.id,
        "message_id": None,
        "prize": prize,
        "winners": int(winners),
        "end_time": end_time,
        "entries": [],
        "ended": False
    }

    config["giveaways"][giveaway_id] = giveaway_data

    save_config()

    embed = discord.Embed(
        title="🎉 GIVEAWAY",
        description=(
            f"**Prize:** {prize}\n\n"
            f"**Winners:** {winners}\n"
            f"**Ends:** <t:{int(end_time)}:R>\n\n"
            "Click **🎉 Enter Giveaway** below to enter!"
        ),
        color=discord.Color.green()
    )

    embed.set_footer(
        text=f"Giveaway ID: {giveaway_id}"
    )

    view = GiveawayView(giveaway_id)

    await interaction.response.send_message(
        embed=embed,
        view=view
    )

    message = await interaction.original_response()

    giveaway_data["message_id"] = message.id

    save_config()

    task = asyncio.create_task(
        finish_giveaway(giveaway_id)
    )

    giveaway_tasks[giveaway_id] = task


# ============================================================
# FINISH GIVEAWAY
# ============================================================

async def finish_giveaway(giveaway_id):

    giveaway = config["giveaways"].get(
        giveaway_id
    )

    if not giveaway:
        return

    wait_time = max(
        0,
        giveaway["end_time"] - time.time()
    )

    await asyncio.sleep(wait_time)

    giveaway = config["giveaways"].get(
        giveaway_id
    )

    if not giveaway:
        return

    if giveaway.get("ended"):
        return

    await complete_giveaway(
        giveaway_id
    )


# ============================================================
# COMPLETE GIVEAWAY
# ============================================================

async def complete_giveaway(giveaway_id):

    giveaway = config["giveaways"].get(
        giveaway_id
    )

    if not giveaway:
        return

    if giveaway.get("ended"):
        return

    giveaway["ended"] = True

    save_config()

    guild = bot.get_guild(
        int(
            next(
                (
                    guild_id
                    for guild_id, data in config["giveaways"].items()
                    if data is giveaway
                ),
                0
            )
        )
    )

    # Find guild/channel more reliably from channel.
    channel = bot.get_channel(
        giveaway.get("channel_id")
    )

    if channel is None:
        return

    entries = list(
        dict.fromkeys(
            giveaway.get("entries", [])
        )
    )

    if not entries:
        await channel.send(
            f"🎉 The giveaway for **{giveaway['prize']}** "
            "ended, but nobody entered."
        )
        return

    random.shuffle(entries)

    winner_count = min(
        giveaway["winners"],
        len(entries)
    )

    winners = entries[:winner_count]

    mentions = []

    for user_id in winners:
        mentions.append(
            f"<@{user_id}>"
        )

    await channel.send(
        "🎉 **GIVEAWAY ENDED!**\n\n"
        f"**Prize:** {giveaway['prize']}\n"
        f"**Winner{'s' if len(winners) != 1 else ''}:** "
        + ", ".join(mentions)
    )


# ============================================================
# GIVEAWAY END
# ADMINISTRATOR ONLY
# ============================================================

@bot.tree.command(
    name="giveawayend",
    description="End a giveaway early."
)
@app_commands.describe(
    giveaway_id="The giveaway ID."
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def giveawayend(
    interaction: discord.Interaction,
    giveaway_id: str
):

    giveaway = config["giveaways"].get(
        giveaway_id
    )

    if not giveaway:
        await interaction.response.send_message(
            "❌ Giveaway not found.",
            ephemeral=True
        )
        return

    if giveaway.get("ended"):
        await interaction.response.send_message(
            "❌ This giveaway has already ended.",
            ephemeral=True
        )
        return

    giveaway["end_time"] = time.time()

    save_config()

    task = giveaway_tasks.get(
        giveaway_id
    )

    if task:
        task.cancel()

    await complete_giveaway(
        giveaway_id
    )

    await interaction.response.send_message(
        "✅ Giveaway ended.",
        ephemeral=True
    )


# ============================================================
# GIVEAWAY REROLL
# ADMINISTRATOR ONLY
# ============================================================

@bot.tree.command(
    name="giveawayreroll",
    description="Reroll the winner of a giveaway."
)
@app_commands.describe(
    giveaway_id="The giveaway ID."
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def giveawayreroll(
    interaction: discord.Interaction,
    giveaway_id: str
):

    giveaway = config["giveaways"].get(
        giveaway_id
    )

    if not giveaway:
        await interaction.response.send_message(
            "❌ Giveaway not found.",
            ephemeral=True
        )
        return

    if not giveaway.get("ended"):
        await interaction.response.send_message(
            "❌ This giveaway has not ended yet.",
            ephemeral=True
        )
        return

    entries = list(
        dict.fromkeys(
            giveaway.get("entries", [])
        )
    )

    if not entries:
        await interaction.response.send_message(
            "❌ There are no entries to reroll.",
            ephemeral=True
        )
        return

    winner = random.choice(entries)

    await interaction.response.send_message(
        f"🎉 **New winner:** <@{winner}>\n"
        f"**Prize:** {giveaway['prize']}"
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
            "❌ **Administrator permission required.**\n"
            "You need the **Administrator** permission "
            "to use this command."
        )

    elif isinstance(
        error,
        app_commands.TransformerError
    ):
        message = (
            "❌ One of the values you entered is invalid."
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

    except Exception as error:
        print(
            f"Could not send error message: {error}"
        )


# ============================================================
# START
# ============================================================

bot.run(TOKEN)
