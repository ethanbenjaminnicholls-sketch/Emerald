import os
import json
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

CONFIG_FILE = "welcome_config.json"


# ============================================================
# CONFIG
# ============================================================

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


welcome_config = load_config()


# ============================================================
# BOT READY
# ============================================================

@bot.event
async def on_ready():
    print("================================")
    print(f"Logged in as: {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print("================================")

    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.CustomActivity(name=".gg/emerald")
    )

    print("Custom status set to .gg/emerald")

    try:
        synced = await bot.tree.sync()
        print(f"Successfully synced {len(synced)} commands.")

        for command in synced:
            print(f"Command registered: /{command.name}")

    except Exception as error:
        print(f"Failed to sync commands: {error}")
# ============================================================
# WELCOME SETUP
# ADMINISTRATOR ONLY
# ============================================================

@bot.tree.command(
    name="welcomesetup",
    description="Set up the welcome system."
)
@app_commands.describe(
    channel="The channel where welcome messages will be sent.",
    message="Welcome message. Use {user} to mention the new member."
)
@app_commands.checks.has_permissions(administrator=True)
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
        "✅ **Welcome system configured!**\n\n"
        f"**Channel:** {channel.mention}\n"
        f"**Message:** {preview}",
        ephemeral=True
    )


# ============================================================
# WELCOME MESSAGE
# ============================================================

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
        print(
            f"I don't have permission to send messages "
            f"in #{channel.name}."
        )

    except Exception as error:
        print(f"Welcome message error: {error}")


# ============================================================
# ROLE
# ADMINISTRATOR ONLY
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

    if bot_member is None:
        await interaction.response.send_message(
            "❌ I couldn't find my member information.",
            ephemeral=True
        )
        return

    # Cannot give a role above/equal to bot's highest role
    if role >= bot_member.top_role:
        await interaction.response.send_message(
            "❌ I cannot give that role because it is "
            "above or equal to my highest role.",
            ephemeral=True
        )
        return

    # Cannot give @everyone
    if role.is_default():
        await interaction.response.send_message(
            "❌ You cannot give the @everyone role.",
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

    except Exception as error:
        print(f"Role error: {error}")

        await interaction.response.send_message(
            "❌ Something went wrong while giving the role.",
            ephemeral=True
        )


# ============================================================
# KICK
# ADMINISTRATOR ONLY
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

    except Exception as error:
        print(f"Kick error: {error}")

        await interaction.response.send_message(
            "❌ Something went wrong while kicking this member.",
            ephemeral=True
        )


# ============================================================
# BAN
# ADMINISTRATOR ONLY
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

    except Exception as error:
        print(f"Ban error: {error}")

        await interaction.response.send_message(
            "❌ Something went wrong while banning this member.",
            ephemeral=True
        )


# ============================================================
# COMMAND ERROR HANDLER
# ============================================================

@bot.tree.error
async def command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
):

    if isinstance(error, app_commands.MissingPermissions):

        message = (
            "❌ **Administrator permission required.**\n"
            "You must have the **Administrator** permission "
            "to use this command."
        )

    elif isinstance(error, app_commands.CheckFailure):

        message = (
            "❌ You don't have permission to use this command."
        )

    else:

        print(f"Command error: {error}")

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
        print(f"Could not send error message: {error}")


# ============================================================
# START BOT
# ============================================================

bot.run(TOKEN)
