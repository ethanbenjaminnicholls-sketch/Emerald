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

    # Hex color
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

        print("Status set to: Streaming .gg/emerald")

    except Exception as error:
        print(f"Could not set status: {error}")

    # Global slash command sync
    try:
        synced = await bot.tree.sync()

        print(
            f"Successfully synced {len(synced)} "
            "commands globally."
        )

        for command in synced:
            print(f"Registered: /{command.name}")

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
    channel="The channel for welcome messages.",
    message="The welcome message. Use {user} to mention the member.",
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

    # ========================================================
    # EMBED OPTION
    # ========================================================

    embed_value = embed.lower().strip()

    use_embed = embed_value in (
        "yes",
        "y",
        "true",
        "on"
    )

    # ========================================================
    # COLOR
    # ========================================================

    color_name = color.lower().strip()

    embed_color = get_embed_color(
        color_name
    )

    # ========================================================
    # SAVE CONFIG
    # ========================================================

    welcome_config[guild_id] = {
        "channel_id": channel.id,
        "message": message,
        "embed": use_embed,
        "color": color_name,
        "image_url": image_url.strip()
    }

    save_config(welcome_config)

    # ========================================================
    # CONFIRMATION
    # ========================================================

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

    config = welcome_config.get(
        guild_id
    )

    if not config:
        return

    # Find configured channel
    channel = member.guild.get_channel(
        config.get("channel_id")
    )

    if channel is None:
        print(
            f"Welcome channel no longer exists in "
            f"{member.guild.name}"
        )
        return

    # Replace {user}
    message = config.get(
        "message",
        "Welcome {user}!"
    )

    message = message.replace(
        "{user}",
        member.mention
    )

    # ========================================================
    # NORMAL MESSAGE
    # ========================================================

    if not config.get("embed", False):

        try:
            await channel.send(message)

        except discord.Forbidden:
            print(
                f"No permission to send welcome message "
                f"in #{channel.name}"
            )

        except Exception as error:
            print(
                f"Welcome message error: {error}"
            )

        return

    # ========================================================
    # EMBED MESSAGE
    # ========================================================

    color_name = config.get(
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
    image_url = config.get(
        "image_url",
        ""
    ).strip()

    if image_url:
        welcome_embed.set_image(
            url=image_url
        )

    # Send embed
    try:

        await channel.send(
            embed=welcome_embed
        )

    except discord.Forbidden:

        print(
            f"No permission to send welcome embed "
            f"in #{channel.name}"
        )

    except Exception as error:

        print(
            f"Welcome embed error: {error}"
        )


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

    # Cannot give @everyone
    if role.is_default():
        await interaction.response.send_message(
            "❌ You cannot give the @everyone role.",
            ephemeral=True
        )
        return

    # Bot hierarchy check
    if role >= bot_member.top_role:
        await interaction.response.send_message(
            "❌ I cannot give that role because it is "
            "above or equal to my highest role.",
            ephemeral=True
        )
        return

    try:

        await user.add_roles(role)

        await interaction.response.send_message(
            f"✅ {role.mention} has been given to "
            f"{user.mention}."
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

    if isinstance(
        error,
        app_commands.MissingPermissions
    ):

        message = (
            "❌ **Administrator permission required.**\n"
            "You must have the **Administrator** permission "
            "to use this command."
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
# START BOT
# ============================================================

bot.run(TOKEN)
