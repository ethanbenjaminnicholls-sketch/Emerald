import os
import json
import random
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
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ============================================================
# CONFIG FILE
# ============================================================

CONFIG_FILE = "bot_config.json"


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except Exception as error:
        print(f"Could not load config: {error}")
        return {}


def save_config(config):
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


def get_embed_color(color):
    color = color.lower().strip()

    if color.startswith("#"):
        try:
            value = int(color[1:], 16)

            if 0 <= value <= 0xFFFFFF:
                return discord.Color(value)

        except ValueError:
            pass

    return COLORS.get(
        color,
        discord.Color.green()
    )


# ============================================================
# DURATION PARSER
# ============================================================

def parse_duration(duration):
    duration = duration.lower().strip()

    try:
        if duration.endswith("s"):
            return int(duration[:-1])

        if duration.endswith("m"):
            return int(duration[:-1]) * 60

        if duration.endswith("h"):
            return int(duration[:-1]) * 60 * 60

        if duration.endswith("d"):
            return int(duration[:-1]) * 60 * 60 * 24

        return int(duration)

    except ValueError:
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

        print("Status set to: Streaming .gg/emerald")

    except Exception as error:
        print(f"Could not set status: {error}")


    # --------------------------------------------------------
    # COMMANDS LOADED
    # --------------------------------------------------------

    print("========================================")
    print("COMMANDS LOADED INTO BOT:")

    commands_loaded = bot.tree.get_commands()

    for command in commands_loaded:
        print(f"  /{command.name}")

    print(f"TOTAL LOADED: {len(commands_loaded)}")
    print("========================================")


    # --------------------------------------------------------
    # GLOBAL COMMAND SYNC
    # --------------------------------------------------------

    try:

        synced = await bot.tree.sync()

        print("========================================")
        print(f"SYNCED {len(synced)} GLOBAL COMMANDS:")

        for command in synced:
            print(f"  /{command.name}")

        print("========================================")

    except Exception as error:

        print("========================================")
        print("GLOBAL COMMAND SYNC FAILED")
        print(error)
        print("========================================")


# ============================================================
# HELP
# ============================================================

@bot.tree.command(
    name="help",
    description="Show all available bot commands."
)
async def help_command(
    interaction: discord.Interaction
):

    embed = discord.Embed(
        title="Emerald Bot",
        description="Here are all the available commands.",
        color=discord.Color.green()
    )

    embed.add_field(
        name="🛠️ Moderation",
        value=(
            "`/role` — Give a member a role\n"
            "`/kick` — Kick a member\n"
            "`/ban` — Ban a member\n"
            "`/timeout` — Timeout a member"
        ),
        inline=False
    )

    embed.add_field(
        name="👋 Welcome",
        value=(
            "`/welcomesetup` — Configure welcome messages"
        ),
        inline=False
    )

    embed.add_field(
        name="🎉 Giveaway",
        value=(
            "`/giveaway` — Start a giveaway"
        ),
        inline=False
    )

    embed.add_field(
        name="✅ Verification",
        value=(
            "`/verifysetup` — Set up verification"
        ),
        inline=False
    )

    embed.add_field(
        name="🔊 Voice",
        value=(
            "`/jointocreate` — Set up Join to Create"
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
    channel="The channel for welcome messages.",
    message="Welcome message. Use {user} to mention the member.",
    embed="Use an embed? Type yes or no.",
    color="Embed color, e.g. green, red, blue, or #00ff00.",
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

    server_id = str(interaction.guild.id)

    use_embed = embed.lower().strip() in (
        "yes",
        "y",
        "true",
        "on"
    )

    color_name = color.lower().strip()

    # Make sure guild config exists
    if server_id not in config:
        config[server_id] = {}

    config[server_id]["welcome"] = {
        "channel_id": channel.id,
        "message": message,
        "embed": use_embed,
        "color": color_name,
        "image_url": image_url.strip()
    }

    save_config(config)

    await interaction.response.send_message(
        "✅ **Welcome system configured!**\n\n"
        f"**Channel:** {channel.mention}\n"
        f"**Embed:** {'Yes' if use_embed else 'No'}\n"
        f"**Color:** `{color_name}`\n"
        f"**Image:** `{image_url.strip() if image_url.strip() else 'None'}`",
        ephemeral=True
    )


# ============================================================
# WELCOME MESSAGE
# ============================================================

@bot.event
async def on_member_join(member):

    server_id = str(member.guild.id)

    server_config = config.get(server_id)

    if not server_config:
        return

    welcome_config = server_config.get("welcome")

    if not welcome_config:
        return

    channel = member.guild.get_channel(
        welcome_config.get("channel_id")
    )

    if channel is None:
        return

    message = welcome_config.get(
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

    if not welcome_config.get("embed", False):

        try:
            await channel.send(message)

        except Exception as error:
            print(f"Welcome message error: {error}")

        return


    # --------------------------------------------------------
    # EMBED
    # --------------------------------------------------------

    color_name = welcome_config.get(
        "color",
        "green"
    )

    embed_color = get_embed_color(
        color_name
    )

    welcome_embed = discord.Embed(
        description=message,
        color=embed_color
    )

    # Member profile picture
    welcome_embed.set_thumbnail(
        url=member.display_avatar.url
    )

    # Optional image
    image_url = welcome_config.get(
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
    description="Give a user a role."
)
@app_commands.describe(
    user="The user to give the role to.",
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
            "❌ I don't have permission to kick this member.",
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
            "❌ I don't have permission to ban this member.",
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
    duration="Duration such as 10m, 1h, or 1d.",
    reason="Reason for the timeout."
)
@app_commands.checks.has_permissions(administrator=True)
async def timeout(
    interaction: discord.Interaction,
    user: discord.Member,
    duration: str,
    reason: str = "No reason provided"
):

    seconds = parse_duration(duration)

    if seconds is None or seconds <= 0:
        await interaction.response.send_message(
            "❌ Invalid duration. Use something like `10m`, `1h`, or `1d`.",
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
            discord.utils.utcnow() + discord.timedelta(seconds=seconds),
            reason=reason
        )

        await interaction.response.send_message(
            f"🔇 **{user}** has been timed out for `{duration}`.\n"
            f"**Reason:** {reason}"
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ I don't have permission to timeout this member.",
            ephemeral=True
        )


# ============================================================
# GIVEAWAY VIEW
# ============================================================

class GiveawayView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

        self.entries = set()
        self.message = None
        self.ended = False

    @discord.ui.button(
        label="Enter Giveaway",
        style=discord.ButtonStyle.green,
        emoji="🎉"
    )
    async def enter(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if self.ended:
            await interaction.response.send_message(
                "❌ This giveaway has ended.",
                ephemeral=True
            )
            return

        user_id = interaction.user.id

        if user_id in self.entries:

            self.entries.remove(user_id)

            await interaction.response.send_message(
                "❌ You left the giveaway.",
                ephemeral=True
            )

        else:

            self.entries.add(user_id)

            await interaction.response.send_message(
                "✅ You entered the giveaway!",
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
    duration="Duration such as 10m, 1h, or 1d.",
    prize="The giveaway prize.",
    winners="Number of winners."
)
@app_commands.checks.has_permissions(administrator=True)
async def giveaway(
    interaction: discord.Interaction,
    duration: str,
    prize: str,
    winners: int = 1
):

    seconds = parse_duration(duration)

    if seconds is None or seconds <= 0:
        await interaction.response.send_message(
            "❌ Invalid duration. Example: `10m`, `1h`, `1d`.",
            ephemeral=True
        )
        return

    if winners < 1:
        await interaction.response.send_message(
            "❌ You need at least 1 winner.",
            ephemeral=True
        )
        return

    view = GiveawayView()

    embed = discord.Embed(
        title="🎉 GIVEAWAY",
        description=(
            f"**Prize:** {prize}\n"
            f"**Winners:** {winners}\n"
            f"**Duration:** {duration}\n\n"
            "Click the button below to enter!"
        ),
        color=discord.Color.green()
    )

    await interaction.response.send_message(
        embed=embed,
        view=view
    )

    view.message = await interaction.original_response()

    await asyncio.sleep(seconds)

    view.ended = True

    for item in view.children:
        item.disabled = True

    if view.entries:

        chosen_ids = random.sample(
            list(view.entries),
            min(winners, len(view.entries))
        )

        mentions = " ".join(
            f"<@{user_id}>"
            for user_id in chosen_ids
        )

        result = (
            f"🎉 **Giveaway ended!**\n\n"
            f"**Prize:** {prize}\n"
            f"**Winner(s):** {mentions}"
        )

    else:

        result = (
            f"🎉 **Giveaway ended!**\n\n"
            f"**Prize:** {prize}\n"
            "❌ Nobody entered."
        )

    await view.message.edit(
        view=view
    )

    await interaction.channel.send(
        result
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
        style=discord.ButtonStyle.green,
        emoji="✅"
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
                "❌ The verified role no longer exists.",
                ephemeral=True
            )
            return

        if role in interaction.user.roles:
            await interaction.response.send_message(
                "✅ You are already verified.",
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


# ============================================================
# VERIFY SETUP
# ============================================================

@bot.tree.command(
    name="verifysetup",
    description="Set up the verification system."
)
@app_commands.describe(
    channel="The channel where the verification message goes.",
    role="The role users receive when verified."
)
@app_commands.checks.has_permissions(administrator=True)
async def verifysetup(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    role: discord.Role
):

    bot_member = interaction.guild.me

    if role >= bot_member.top_role:
        await interaction.response.send_message(
            "❌ The verified role must be below my highest role.",
            ephemeral=True
        )
        return

    server_id = str(interaction.guild.id)

    if server_id not in config:
        config[server_id] = {}

    config[server_id]["verify"] = {
        "role_id": role.id,
        "channel_id": channel.id
    }

    save_config(config)

    embed = discord.Embed(
        title="✅ Verification",
        description=(
            "Click the button below to verify yourself "
            "and receive access to the server."
        ),
        color=discord.Color.green()
    )

    await channel.send(
        embed=embed,
        view=VerifyView(role.id)
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
    description="Set up a Join to Create voice channel."
)
@app_commands.describe(
    category="The category where the voice channel should be created."
)
@app_commands.checks.has_permissions(administrator=True)
async def jointocreate(
    interaction: discord.Interaction,
    category: discord.CategoryChannel
):

    server_id = str(interaction.guild.id)

    if server_id not in config:
        config[server_id] = {}

    # Create the Join to Create channel
    channel = await interaction.guild.create_voice_channel(
        "Join To Create",
        category=category
    )

    config[server_id]["jointocreate"] = {
        "channel_id": channel.id,
        "category_id": category.id
    }

    save_config(config)

    await interaction.response.send_message(
        f"✅ Join to Create has been set up!\n"
        f"Join **{channel.name}** to create your own voice channel.",
        ephemeral=True
    )


# ============================================================
# JOIN TO CREATE HANDLER
# ============================================================

@bot.event
async def on_voice_state_update(
    member,
    before,
    after
):

    if after.channel is None:
        return

    server_id = str(member.guild.id)

    server_config = config.get(server_id)

    if not server_config:
        return

    jtc_config = server_config.get(
        "jointocreate"
    )

    if not jtc_config:
        return

    jtc_channel_id = jtc_config.get(
        "channel_id"
    )

    if after.channel.id != jtc_channel_id:
        return

    category = member.guild.get_channel(
        jtc_config.get("category_id")
    )

    if not isinstance(
        category,
        discord.CategoryChannel
    ):
        return

    try:

        new_channel = await member.guild.create_voice_channel(
            f"{member.display_name}'s Channel",
            category=category
        )

        await member.move_to(
            new_channel
        )

        # Wait for the member to leave
        while True:

            await asyncio.sleep(2)

            if len(new_channel.members) == 0:
                break

        await new_channel.delete()

    except Exception as error:

        print(
            f"Join To Create error: {error}"
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
# FINAL COMMAND CHECK
# ============================================================

print("========================================")
print("COMMANDS REGISTERED IN bot.py:")

for command in bot.tree.get_commands():
    print(f"  /{command.name}")

print(f"TOTAL: {len(bot.tree.get_commands())}")
print("========================================")


# ============================================================
# START BOT
# ============================================================

bot.run(TOKEN)
