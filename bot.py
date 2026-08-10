import os
import json
import discord
from discord import app_commands
from discord.ext import commands

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

CONFIG_FILE = "welcome_config.json"


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except:
        return {}


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=4)


welcome_config = load_config()


# =========================
# BOT READY
# =========================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"Bot ID: {bot.user.id}")

    try:
        synced = await bot.tree.sync()
        print(f"Successfully synced {len(synced)} commands.")

        for command in synced:
            print(f"Command registered: /{command.name}")

    except Exception as error:
        print(f"Failed to sync commands: {error}")


# =========================
# WELCOME SETUP
# =========================

@bot.tree.command(
    name="welcomesetup",
    description="Set up the welcome system."
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

    preview = message.replace(
        "{user}",
        interaction.user.mention
    )

    await interaction.response.send_message(
        f"✅ Welcome system configured!\n\n"
        f"**Channel:** {channel.mention}\n"
        f"**Message:** {preview}",
        ephemeral=True
    )


# =========================
# WELCOME MESSAGE
# =========================

@bot.event
async def on_member_join(member):

    guild_id = str(member.guild.id)

    config = welcome_config.get(guild_id)

    if not config:
        return

    channel = member.guild.get_channel(
        config["channel_id"]
    )

    if channel is None:
        return

    message = config["message"].replace(
        "{user}",
        member.mention
    )

    try:
        await channel.send(message)
    except discord.Forbidden:
        print("I don't have permission to send messages there.")


# =========================
# ROLE
# =========================

@bot.tree.command(
    name="role",
    description="Give a user a role."
)
@app_commands.describe(
    user="The user to give the role to.",
    role="The role to give."
)
@app_commands.checks.has_permissions(manage_roles=True)
async def role(
    interaction: discord.Interaction,
    user: discord.Member,
    role: discord.Role
):

    if role >= interaction.guild.me.top_role:
        await interaction.response.send_message(
            "❌ I cannot give that role because it is above my highest role.",
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


# =========================
# KICK
# =========================

@bot.tree.command(
    name="kick",
    description="Kick a member."
)
@app_commands.describe(
    user="The member to kick.",
    reason="Reason for the kick."
)
@app_commands.checks.has_permissions(kick_members=True)
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


# =========================
# BAN
# =========================

@bot.tree.command(
    name="ban",
    description="Ban a member."
)
@app_commands.describe(
    user="The member to ban.",
    reason="Reason for the ban."
)
@app_commands.checks.has_permissions(ban_members=True)
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


# =========================
# COMMAND ERROR HANDLER
# =========================

@bot.tree.error
async def command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
):

    if isinstance(error, app_commands.MissingPermissions):
        message = "❌ You don't have permission to use this command."
    else:
        print(f"Command error: {error}")
        message = "❌ An error occurred."

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

if not TOKEN:
    raise RuntimeError("TOKEN environment variable is missing!")

bot.run(TOKEN)
