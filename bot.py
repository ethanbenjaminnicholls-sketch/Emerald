import os
import json
import random
import asyncio
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
# INTENTS
# ============================================================

intents = discord.Intents.default()

intents.members = True
intents.message_content = True
intents.voice_states = True


# ============================================================
# BOT
# ============================================================

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


# ============================================================
# COLORS
# ============================================================

def get_color(value):

    value = str(value).lower().strip()

    colors = {
        "red": discord.Color.red(),
        "green": discord.Color.green(),
        "blue": discord.Color.blue(),
        "purple": discord.Color.purple(),
        "orange": discord.Color.orange(),
        "yellow": discord.Color.yellow(),
        "pink": discord.Color.magenta(),
        "gold": discord.Color.gold(),
        "teal": discord.Color.teal(),

        # FIXED - no discord.Color.grey()
        "gray": discord.Color.from_rgb(128, 128, 128),
        "grey": discord.Color.from_rgb(128, 128, 128),

        "black": discord.Color.from_rgb(0, 0, 0),
        "white": discord.Color.from_rgb(255, 255, 255)
    }

    if value.startswith("#"):
        try:
            number = int(value[1:], 16)

            if 0 <= number <= 0xFFFFFF:
                return discord.Color(number)

        except ValueError:
            pass

    return colors.get(
        value,
        discord.Color.green()
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

    except Exception as error:
        print(f"Presence error: {error}")

    try:
        synced = await bot.tree.sync()

        print(
            f"Successfully synced {len(synced)} commands."
        )

        for command in synced:
            print(f"Registered: /{command.name}")

    except Exception as error:
        print(f"Command sync error: {error}")


# ============================================================
# HELP
# ============================================================

@bot.tree.command(
    name="help",
    description="Show all bot commands."
)
async def help_command(interaction: discord.Interaction):

    embed = discord.Embed(
        title="💚 Emerald Bot",
        description="Here are all available commands.",
        color=discord.Color.green()
    )

    embed.add_field(
        name="🛡️ Moderation",
        value=(
            "`/kick` — Kick a member\n"
            "`/ban` — Ban a member\n"
            "`/timeout` — Timeout a member\n"
            "`/role` — Give a member a role"
        ),
        inline=False
    )

    embed.add_field(
        name="👋 Welcome",
        value=(
            "`/welcomesetup` — "
            "Set up welcome messages"
        ),
        inline=False
    )

    embed.add_field(
        name="🎉 Giveaways",
        value=(
            "`/giveaway` — Start a giveaway"
        ),
        inline=False
    )

    embed.add_field(
        name="✅ Verification",
        value=(
            "`/verifysetup` — "
            "Set up verification"
        ),
        inline=False
    )

    embed.add_field(
        name="🔊 Voice",
        value=(
            "`/jointocreate` — "
            "Set up Join to Create"
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
    channel="Welcome channel.",
    message="Welcome message. Use {user} for the member.",
    embed="Use an embed? yes or no.",
    color="Embed color.",
    image_url="Optional image URL."
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def welcomesetup(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    message: str,
    embed: str = "no",
    color: str = "green",
    image_url: str = ""
):

    guild_id = str(interaction.guild.id)

    if guild_id not in config:
        config[guild_id] = {}

    config[guild_id]["welcome"] = {
        "channel_id": channel.id,
        "message": message,
        "embed": embed.lower().strip() in (
            "yes",
            "y",
            "true",
            "on"
        ),
        "color": color,
        "image_url": image_url.strip()
    }

    save_config()

    await interaction.response.send_message(
        "✅ **Welcome system configured!**\n\n"
        f"**Channel:** {channel.mention}\n"
        f"**Embed:** `{embed}`\n"
        f"**Color:** `{color}`\n"
        f"**Image:** `{image_url or 'None'}`",
        ephemeral=True
    )


# ============================================================
# MEMBER JOIN
# ============================================================

@bot.event
async def on_member_join(member):

    guild_id = str(member.guild.id)

    guild_config = config.get(
        guild_id,
        {}
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

    if not welcome.get("embed", False):

        try:
            await channel.send(message)

        except Exception as error:
            print(f"Welcome error: {error}")

        return

    welcome_embed = discord.Embed(
        description=message,
        color=get_color(
            welcome.get(
                "color",
                "green"
            )
        )
    )

    welcome_embed.set_thumbnail(
        url=member.display_avatar.url
    )

    image_url = welcome.get(
        "image_url",
        ""
    )

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
    user="Member.",
    role="Role."
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def role(
    interaction: discord.Interaction,
    user: discord.Member,
    role: discord.Role
):

    if role.is_default():

        await interaction.response.send_message(
            "❌ You cannot give @everyone.",
            ephemeral=True
        )

        return

    bot_member = interaction.guild.me

    if bot_member is None:

        await interaction.response.send_message(
            "❌ I could not find my bot member.",
            ephemeral=True
        )

        return

    if role >= bot_member.top_role:

        await interaction.response.send_message(
            "❌ That role is above or equal "
            "to my highest role.",
            ephemeral=True
        )

        return

    try:

        await user.add_roles(role)

        await interaction.response.send_message(
            f"✅ Gave {role.mention} "
            f"to {user.mention}."
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ I cannot give that role.",
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
    user="Member to kick.",
    reason="Reason."
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
    user="Member to ban.",
    reason="Reason."
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
    user="Member to timeout.",
    minutes="Timeout length in minutes.",
    reason="Reason."
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def timeout(
    interaction: discord.Interaction,
    user: discord.Member,
    minutes: int,
    reason: str = "No reason provided"
):

    if minutes < 1:

        await interaction.response.send_message(
            "❌ Minutes must be at least 1.",
            ephemeral=True
        )

        return

    if minutes > 40320:

        await interaction.response.send_message(
            "❌ Maximum timeout is 28 days.",
            ephemeral=True
        )

        return

    try:

        await user.timeout(
            timedelta(minutes=minutes),
            reason=reason
        )

        await interaction.response.send_message(
            f"⏰ {user.mention} has been "
            f"timed out for **{minutes} minutes**."
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ I cannot timeout that member.",
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
    prize="Giveaway prize.",
    winners="Number of winners.",
    duration="Duration in seconds."
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def giveaway(
    interaction: discord.Interaction,
    prize: str,
    winners: int,
    duration: int
):

    if winners < 1:

        await interaction.response.send_message(
            "❌ Winners must be at least 1.",
            ephemeral=True
        )

        return

    if duration < 10:

        await interaction.response.send_message(
            "❌ Duration must be at least 10 seconds.",
            ephemeral=True
        )

        return

    embed = discord.Embed(
        title="🎉 GIVEAWAY!",
        description=(
            f"🎁 **Prize:** {prize}\n"
            f"🏆 **Winners:** {winners}\n\n"
            f"React with 🎉 to enter!"
        ),
        color=discord.Color.green()
    )

    await interaction.response.send_message(
        embed=embed
    )

    giveaway_message = (
        await interaction.original_response()
    )

    await giveaway_message.add_reaction("🎉")

    await asyncio.sleep(duration)

    try:

        giveaway_message = (
            await interaction.channel.fetch_message(
                giveaway_message.id
            )
        )

        reaction = discord.utils.get(
            giveaway_message.reactions,
            emoji="🎉"
        )

        if reaction is None:
            return

        users = [
            user async for user in reaction.users()
            if not user.bot
        ]

        if not users:

            await interaction.channel.send(
                "😔 Nobody entered the giveaway."
            )

            return

        selected = random.sample(
            users,
            min(winners, len(users))
        )

        mentions = ", ".join(
            user.mention
            for user in selected
        )

        await interaction.channel.send(
            f"🎉 Congratulations {mentions}!\n"
            f"You won **{prize}**!"
        )

    except Exception as error:

        print(
            f"Giveaway error: {error}"
        )


# ============================================================
# VERIFY BUTTON
# ============================================================

class VerifyView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="Verify",
        style=discord.ButtonStyle.green,
        emoji="✅",
        custom_id="emerald_verify_button"
    )
    async def verify_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        guild_id = str(
            interaction.guild.id
        )

        guild_config = config.get(
            guild_id,
            {}
        )

        verify = guild_config.get(
            "verify"
        )

        if not verify:

            await interaction.response.send_message(
                "❌ Verification is not configured.",
                ephemeral=True
            )

            return

        role = interaction.guild.get_role(
            verify["role_id"]
        )

        if role is None:

            await interaction.response.send_message(
                "❌ The verified role no longer exists.",
                ephemeral=True
            )

            return

        try:

            await interaction.user.add_roles(
                role
            )

            await interaction.response.send_message(
                "✅ You are now verified!",
                ephemeral=True
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ I cannot give you the "
                "verified role.",
                ephemeral=True
            )


# ============================================================
# VERIFY SETUP
# ============================================================

@bot.tree.command(
    name="verifysetup",
    description="Set up server verification."
)
@app_commands.describe(
    channel="Verification channel.",
    role="Role users receive after verification."
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def verifysetup(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    role: discord.Role
):

    guild_id = str(
        interaction.guild.id
    )

    if guild_id not in config:
        config[guild_id] = {}

    config[guild_id]["verify"] = {
        "channel_id": channel.id,
        "role_id": role.id
    }

    save_config()

    embed = discord.Embed(
        title="✅ Verification",
        description=(
            "Click **Verify** below to receive "
            "the verified role."
        ),
        color=discord.Color.green()
    )

    await channel.send(
        embed=embed,
        view=VerifyView()
    )

    await interaction.response.send_message(
        f"✅ Verification setup completed.\n"
        f"Channel: {channel.mention}\n"
        f"Role: {role.mention}",
        ephemeral=True
    )


# ============================================================
# JOIN TO CREATE SETUP
# ============================================================

@bot.tree.command(
    name="jointocreate",
    description="Set up a temporary Join To Create voice channel."
)
@app_commands.describe(
    category="The category where Join To Create will be created."
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def jointocreate(
    interaction: discord.Interaction,
    category: discord.CategoryChannel
):

    guild = interaction.guild
    guild_id = str(guild.id)

    if guild_id not in config:
        config[guild_id] = {}

    # --------------------------------------------------------
    # DELETE OLD TRIGGER IF ONE EXISTS
    # --------------------------------------------------------

    old_trigger_id = config[guild_id].get(
        "jtc_trigger"
    )

    if old_trigger_id:

        old_trigger = guild.get_channel(
            old_trigger_id
        )

        if old_trigger:

            try:

                await old_trigger.delete(
                    reason="Replacing old Join To Create channel"
                )

            except Exception as error:

                print(
                    f"Could not delete old JTC: {error}"
                )

    # --------------------------------------------------------
    # CREATE PERMANENT TRIGGER
    # --------------------------------------------------------

    try:

        trigger = await guild.create_voice_channel(

            name="Join To Create",

            category=category,

            reason="Join To Create setup"

        )

    except discord.Forbidden:

        await interaction.response.send_message(

            "❌ I need **Manage Channels** permission "
            "to create the Join To Create channel.",

            ephemeral=True

        )

        return

    except Exception as error:

        print(
            f"JTC SETUP ERROR: {error}"
        )

        await interaction.response.send_message(

            "❌ Could not create the Join To Create channel.",

            ephemeral=True

        )

        return

    # Save trigger ID

    config[guild_id]["jtc_trigger"] = trigger.id

    save_config()

    await interaction.response.send_message(

        f"✅ **Join To Create is ready!**\n\n"
        f"🔊 Join: {trigger.mention}\n\n"
        f"When someone joins it, the bot will create "
        f"a temporary voice channel and move them into it.",

        ephemeral=True

    )


# ============================================================
# JOIN TO CREATE SYSTEM
# ============================================================

@bot.event
async def on_voice_state_update(
    member: discord.Member,
    before: discord.VoiceState,
    after: discord.VoiceState
):

    guild = member.guild
    guild_id = str(guild.id)

    guild_config = config.get(
        guild_id,
        {}
    )

    trigger_id = guild_config.get(
        "jtc_trigger"
    )

    # No setup
    if not trigger_id:
        return

    # ========================================================
    # JOINED THE JOIN TO CREATE CHANNEL
    # ========================================================

    if (
        after.channel is not None
        and after.channel.id == trigger_id
    ):

        trigger_channel = after.channel

        try:

            # Create temporary voice channel
            new_channel = await guild.create_voice_channel(

                name=f"{member.display_name}'s Channel",

                category=trigger_channel.category,

                reason="Join To Create temporary channel"

            )

            print(
                f"JTC: Created {new_channel.name}"
            )

            # Move member into their new channel
            await member.move_to(
                new_channel,
                reason="Join To Create"
            )

            print(
                f"JTC: Moved {member} into "
                f"{new_channel.name}"
            )

        except discord.Forbidden:

            print(
                "JTC ERROR: Bot needs "
                "Manage Channels AND Move Members."
            )

        except discord.HTTPException as error:

            print(
                f"JTC Discord error: {error}"
            )

        except Exception as error:

            print(
                f"JTC error: {error}"
            )

        return

    # ========================================================
    # USER LEFT A CHANNEL
    # ========================================================

    if before.channel is None:
        return

    old_channel = before.channel

    # NEVER DELETE THE PERMANENT TRIGGER
    if old_channel.id == trigger_id:
        return

    # --------------------------------------------------------
    # CHECK WHETHER THIS IS ONE OF OUR TEMPORARY CHANNELS
    # --------------------------------------------------------

    # Our temporary channels always end with "'s Channel"
    if not old_channel.name.endswith("'s Channel"):
        return

    # Somebody else is still inside
    if len(old_channel.members) > 0:
        return

    # --------------------------------------------------------
    # DELETE EMPTY TEMPORARY CHANNEL
    # --------------------------------------------------------

    try:

        await old_channel.delete(
            reason="Empty Join To Create channel"
        )

        print(
            f"JTC: Deleted {old_channel.name}"
        )

    except discord.NotFound:

        pass

    except discord.Forbidden:

        print(
            "JTC ERROR: Bot needs Manage Channels "
            "to delete temporary channels."
        )

    except discord.HTTPException as error:

        print(
            f"JTC delete error: {error}"
        )

    except Exception as error:

        print(
            f"JTC delete error: {error}"
        )


# ============================================================
# COMMAND ERROR HANDLER
# ============================================================

@bot.tree.error
async def command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
):

    print(
        f"COMMAND ERROR: {repr(error)}"
    )

    if isinstance(
        error,
        app_commands.MissingPermissions
    ):

        message = (
            "❌ You need **Administrator** "
            "permission to use this command."
        )

    else:

        message = (
            "❌ Something went wrong. "
            "Check the Railway logs."
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
            f"Error handler error: {error}"
        )


# ============================================================
# START
# ============================================================

print("Starting Emerald Bot...")

bot.run(TOKEN)
