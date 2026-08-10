import os
import json
import discord
from discord import app_commands
from discord.ext import commands

CONFIG_FILE = "welcome_config.json"

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

welcome_config = load_config()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Slash command sync failed: {e}")

                     ^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/discord/app_commands/commands.py", line 211, in validate_name
    raise ValueError(f'{name!r} must be all lower-case')
ValueError: 'welcomeSetup' must be all lower-case
Traceback (most recent call last):
  File "/app/bot.py", line 38, in <module>
    @bot.tree.command(name="welcomeSetup", description="Set up the server welcome system.")
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/discord/app_commands/tree.py", line 922, in decorator
    command = Command(
              ^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/discord/app_commands/commands.py", line 667, in __init__
    self.name: str = validate_name(name)
                     ^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/discord/app_commands/commands.py", line 211, in validate_name
    raise ValueError(f'{name!r} must be all lower-case')
ValueError: 'welcomeSetup' must be all lower-case
Traceback (most recent call last):
  File "/app/bot.py", line 38, in <module>
    @bot.tree.command(name="welcomeSetup", description="Set up the server welcome system.")
     ^^^^^
^^^^^^^^^^
^^^^^^^^^^
^^^^^^^^^^
^^^^^^^^^^
^^^^^^^^^^
^^^^^^^^^^
^^^^^^^^^^
^^^^^^^^^^
^
  File "/app/.venv/lib/python3.12/site-packages/discord/app_commands/tree.py", line 922, in decorator
    command = Command(
          
    ^^^^^^
^^
  File "/app/.venv/lib/python3.12/site-packages/discord/app_commands/commands.py", line 667, in __init__
    self.name: str = validate_name(name)
          
          
 ^^^^^^^^^
^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/discord/app_commands/commands.py", line 211, in validate_name
    raise ValueError(f'{name!r} must be all lower-case')
ValueError: 'welcomeSetup' must be all lower-case
Traceback (most recent call last):
  File "/app/bot.py", line 38, in <module>
    @bot.tree.command(name="welcomeSetup", description="Set up the server welcome system.")
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/discord/app_commands/tree.py", line 922, in decorator
    command = Command(
              ^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/discord/app_commands/commands.py", line 667, in __init__
    self.name: str = validate_name(name)
                     ^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/discord/app_commands/commands.py", line 211, in validate_name
    raise ValueError(f'{name!r} must be all lower-case')
ValueError: 'welcomeSetup' must be all lower-case
Traceback (most recent call last):
  File "/app/bot.py", line 38, in <module>
    @bot.tree.command(name="welcomeSetup", description="Set up the server welcome system.")
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/discord/app_commands/tree.py", line 922, in decorator
    command = Command(
              ^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/discord/app_commands/commands.py", line 667, in __init__
    self.name: str = validate_name(name)
                     ^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/discord/app_commands/commands.py", line 211, in validate_name
    raise ValueError(f'{name!r} must be all lower-case')
ValueError: 'welcomeSetup' must be all lower-case
ValueError: 'welcomeSetup' must be all lower-case
              ^^^^^^^^
Traceback (most recent call last):
  File "/app/.venv/lib/python3.12/site-packages/discord/app_commands/commands.py", line 667, in __init__
  File "/app/bot.py", line 38, in <module>
    self.name: str = validate_name(name)
    @bot.tree.command(name="welcomeSetup", description="Set up the server welcome system.")
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                     ^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/discord/app_commands/tree.py", line 922, in decorator
  File "/app/.venv/lib/python3.12/site-packages/discord/app_commands/commands.py", line 211, in validate_name
    command = Command(
    raise ValueError(f'{name!r} must be all lower-case')
Traceback (most recent call last):
  File "/app/bot.py", line 38, in <module>
    @bot.tree.command(name="welcomeSetup", description="Set up the server welcome system.")
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/discord/app_commands/tree.py", line 922, in decorator
    command = Command(
              ^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/discord/app_commands/commands.py", line 667, in __init__
    self.name: str = validate_name(name)
                     ^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/discord/app_commands/commands.py", line 211, in validate_name
    raise ValueError(f'{name!r} must be all lower-case')
ValueError: 'welcomeSetup' must be all lower-case
Traceback (most recent call last):
  File "/app/bot.py", line 38, in <module>
    @bot.tree.command(name="welcomeSetup", description="Set up the server welcome system.")
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/discord/app_commands/tree.py", line 922, in decorator
    command = Command(
              ^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/discord/app_commands/commands.py", line 667, in __init__
    self.name: str = validate_name(name)
                     ^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/discord/app_commands/commands.py", line 211, in validate_name
    raise ValueError(f'{name!r} must be all lower-case')
ValueError: 'welcomeSetup' must be all lower-case

@app_commands.describe(
    channel="The channel where welcome messages are sent.",
    message="Welcome message. Use {user} to mention the new member."
)
@app_commands.checks.has_permissions(manage_guild=True)
async def welcome_setup(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    guild_id = str(interaction.guild.id)

    welcome_config[guild_id] = {
        "channel_id": channel.id,
        "message": message
    }
    save_config(welcome_config)

    await interaction.response.send_message(
        f"â Welcome system saved!\n"
        f"**Channel:** {channel.mention}\n"
        f"**Message:** {message}",
        ephemeral=True
    )

@bot.event
async def on_member_join(member: discord.Member):
    settings = welcome_config.get(str(member.guild.id))
    if not settings:
        return

    channel = member.guild.get_channel(settings["channel_id"])
    if channel is None:
        return

    message = settings["message"].replace("{user}", member.mention)

    try:
        await channel.send(message)
    except discord.Forbidden:
        print(f"Cannot send welcome message in guild {member.guild.id}")

@bot.tree.command(name="role", description="Give a role to a user.")
@app_commands.describe(user="The user receiving the role.", role="The role to give.")
@app_commands.checks.has_permissions(manage_roles=True)
async def role_command(interaction: discord.Interaction, user: discord.Member, role: discord.Role):
    if role.managed:
        return await interaction.response.send_message(
            "â I cannot give a managed/integration role.", ephemeral=True
        )

    if role >= interaction.guild.me.top_role:
        return await interaction.response.send_message(
            "â My bot role must be above that role.", ephemeral=True
        )

    if role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
        return await interaction.response.send_message(
            "â You cannot give a role equal to or higher than your highest role.",
            ephemeral=True
        )

    try:
        await user.add_roles(role, reason=f"Role command by {interaction.user}")
        await interaction.response.send_message(f"â Gave {role.mention} to {user.mention}.")
    except discord.Forbidden:
        await interaction.response.send_message("â I don't have permission to give that role.", ephemeral=True)

@bot.tree.command(name="kick", description="Kick a user from the server.")
@app_commands.describe(user="The user to kick.", reason="Reason for the kick.")
@app_commands.checks.has_permissions(kick_members=True)
async def kick_command(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    if user == interaction.user:
        return await interaction.response.send_message("â You cannot kick yourself.", ephemeral=True)

    if user.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
        return await interaction.response.send_message(
            "â You cannot kick someone with an equal or higher role.",
            ephemeral=True
        )

    if user.top_role >= interaction.guild.me.top_role:
        return await interaction.response.send_message(
            "â My bot role must be above that user.", ephemeral=True
        )

    try:
        await user.kick(reason=reason)
        await interaction.response.send_message(f"ð¢ **{user}** was kicked.\n**Reason:** {reason}")
    except discord.Forbidden:
        await interaction.response.send_message("â I don't have permission to kick this user.", ephemeral=True)

@bot.tree.command(name="ban", description="Ban a user from the server.")
@app_commands.describe(user="The user to ban.", reason="Reason for the ban.")
@app_commands.checks.has_permissions(ban_members=True)
async def ban_command(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    if user == interaction.user:
        return await interaction.response.send_message("â You cannot ban yourself.", ephemeral=True)

    if user.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
        return await interaction.response.send_message(
            "â You cannot ban someone with an equal or higher role.",
            ephemeral=True
        )

    if user.top_role >= interaction.guild.me.top_role:
        return await interaction.response.send_message(
            "â My bot role must be above that user.", ephemeral=True
        )

    try:
        await user.ban(reason=reason)
        await interaction.response.send_message(f"ð¨ **{user}** was banned.\n**Reason:** {reason}")
    except discord.Forbidden:
        await interaction.response.send_message("â I don't have permission to ban this user.", ephemeral=True)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        message = "â You don't have permission to use this command."
    else:
        print(f"Command error: {error}")
        message = "â Something went wrong."

    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)

token = os.getenv("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN environment variable is not set.")

bot.run(token)


