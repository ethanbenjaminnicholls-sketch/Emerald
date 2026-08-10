  import os
import json
import discord
from discord import app_commands
from discord.ext import commands

CONFIG_FILE = "welcome_config.json"

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================
# CONFIG
# =========================

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


welcome_config = load_config()


# =========================
# BOT READY
# =========================

@bot.event
async def on_ready():

    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game(name=".gg/emerald")
    )

    print(f"Logged in as {bot.user}")
    print("Status: .gg/emerald")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")

        for command in synced:
            print(f"/{command.name}")

    except Exception as e:
        print(f"Sync error: {e}")


# =========================
# WELCOME SETUP
# =========================

@bot.tree.command(
    name="welcomesetup",
    description="Set up the server welcome system."
)
@app_commands.describe(
    channel="The channel for welcome messages.",
    message="Welcome message. Use {user} to mention the member."
)
@app_commands.checks.has_permissions(manage_guild=True)
async def welcomesetup(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    message: str
):

    guild_id = str(interaction.guild.id)

    welcome_config[guild_id] = {
        "channel_id": channel.id,
        "message": message
    }

    save_config(welcome_config)

    await interaction.response.send_message(
        f"✅ Welcome system set up!\n\n"
        f"**Channel:** {channel.mention}\n"
        f"**Message:** {message}\n\n"
        f"Use `{{user}}` to mention the person who joins.",
        ephemeral=True
    )


# =========================
# MEMBER JOIN
# =========================

@bot.event
async def on_member_join(member):

    guild_id = str(member.guild.id)

    settings = welcome_config.get(guild_id)

    if not settings:
        return

    channel = member.guild.get_channel(
        settings["channel_id"]
    )

    if channel is None:
        return

    message = settings["message"].replace(
        "{user}",
        member.mention
    )

    try:
        await channel.send(message)
    except discord.Forbidden:
        print("Cannot send welcome message.")


# =========================
# ROLE
# =========================

@bot.tree.command(
    name="role",
    description="Give a role to a user."
)
@app_commands.describe(
    user="The user to give the role to.",
    role="The role to give."
)
@app_commands.checks.has_permissions(manage_roles=True)
async def role_command(
    interaction: discord.Interaction,
    user: discord.Member,
    role: discord.Role
):

    if role.managed:
        await interaction.response.send_message(
            "❌ I cannot give a managed role.",
            ephemeral=True
        )
        return

    if role >= interaction.guild.me.top_role:
        await interaction.response.send_message(
            "❌ My bot role must be above that role.",
            ephemeral=True
        )
        return

    try:
        await user.add_roles(role)

        await interaction.response.send_message(
            f"✅ Gave {role.mention} to {user.mention}."
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I cannot give that role.",
            ephemeral=True
        )


# =========================
# KICK
# =========================

@bot.tree.command(
    name="kick",
    description="Kick a user."
)
@app_commands.describe(
    user="The user to kick.",
    reason="Reason for the kick."
)
@app_commands.checks.has_permissions(kick_members=True)
async def kick_command(
    interaction: discord.Interaction,
    user: discord.Member,
    reason: str = "No reason provided"
):

    if user == interaction.user:
        await interaction.response.send_message(
            "❌ You cannot kick yourself.",
            ephemeral=True
        )
        return

    if user.top_role >= interaction.guild.me.top_role:
        await interaction.response.send_message(
            "❌ My bot role must be above that user.",
            ephemeral=True
        )
        return

    try:
        await user.kick(reason=reason)

        await interaction.response.send_message(
            f"👢 **{user}** was kicked.\n"
            f"**Reason:** {reason}"
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I cannot kick that user.",
            ephemeral=True
        )


# =========================
# BAN
# =========================

@bot.tree.command(
    name="ban",
    description="Ban a user."
)
@app_commands.describe(
    user="The user to ban.",
    reason="Reason for the ban."
)
@app_commands.checks.has_permissions(ban_members=True)
async def ban_command(
    interaction: discord.Interaction,
    user: discord.Member,
    reason: str = "No reason provided"
):

    if user == interaction.user:
        await interaction.response.send_message(
            "❌ You cannot ban yourself.",
            ephemeral=True
        )
        return

    if user.top_role >= interaction.guild.me.top_role:
        await interaction.response.send_message(
            "❌ My bot role must be above that user.",
            ephemeral=True
        )
        return

    try:
        await user.ban(reason=reason)

        await interaction.response.send_message(
            f"🔨 **{user}** was banned.\n"
            f"**Reason:** {reason}"
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I cannot ban that user.",
            ephemeral=True
        )


# =========================
# ERRORS
# =========================

@bot.tree.error
async def on_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
):

    if isinstance(error, app_commands.MissingPermissions):
        message = "❌ You don't have permission to use this command."
    else:
        print(f"Command error: {error}")
        message = "❌ Something went wrong."

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


# =========================
# START
# =========================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN environment variable is missing."
    )

bot.run(TOKEN)
