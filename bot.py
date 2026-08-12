import os
import json
import asyncio
import random
import re
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands, tasks


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
intents.message_content = False

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ============================================================
# CONFIG FILES
# ============================================================

WELCOME_FILE = "welcome_config.json"
VERIFY_FILE = "verify_config.json"
JTC_FILE = "jtc_config.json"


# ============================================================
# FILE HELPERS
# ============================================================

def load_json(filename):
    if not os.path.exists(filename):
        return {}

    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)

    except Exception as error:
        print(f"Could not load {filename}: {error}")
        return {}


def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    except Exception as error:
        print(f"Could not save {filename}: {error}")


welcome_config = load_json(WELCOME_FILE)
verify_config = load_json(VERIFY_FILE)
jtc_config = load_json(JTC_FILE)


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
    "grey": discord.Color.grey(),
}


def get_color(color):
    color = color.lower().strip()

    if color.startswith("#"):
        try:
            value = int(color[1:], 16)

            if 0 <= value <= 0xFFFFFF:
                return discord.Color(value)

        except ValueError:
            pass

    return COLORS.get(color, discord.Color.green())


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

        print("Streaming status enabled.")

    except Exception as error:
        print(f"Status error: {error}")

    # GLOBAL COMMAND SYNC
    try:
        synced = await bot.tree.sync()

        print(f"Globally synced {len(synced)} commands.")

        for command in synced:
            print(f"Registered: /{command.name}")

    except Exception as error:
        print(f"Global sync error: {error}")


# ============================================================
# WELCOME SETUP
# ============================================================

@bot.tree.command(
    name="welcomesetup",
    description="Set up the welcome system."
)
@app_commands.describe(
    channel="Channel for welcome messages.",
    message="Welcome message. Use {user} to mention the member.",
    embed="Use an embed?",
    color="Embed color.",
    image_url="Optional image URL."
)
@app_commands.choices(
    embed=[
        app_commands.Choice(name="Yes", value="yes"),
        app_commands.Choice(name="No", value="no")
    ]
)
@app_commands.checks.has_permissions(administrator=True)
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

    welcome_config[guild_id] = {
        "channel_id": channel.id,
        "message": message,
        "embed": use_embed,
        "color": color.lower().strip(),
        "image_url": image_url.strip()
    }

    save_json(WELCOME_FILE, welcome_config)

    await interaction.response.send_message(
        "✅ **Welcome system configured!**\n\n"
        f"**Channel:** {channel.mention}\n"
        f"**Embed:** {'Yes' if use_embed else 'No'}\n"
        f"**Color:** `{color}`\n"
        f"**Image:** `{image_url if image_url else 'None'}`",
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
        config.get("channel_id")
    )

    if channel is None:
        return

    message = config.get(
        "message",
        "Welcome {user}!"
    )

    message = message.replace(
        "{user}",
        member.mention
    )

    # Normal message
    if not config.get("embed", False):

        try:
            await channel.send(message)

        except Exception as error:
            print(f"Welcome error: {error}")

        return

    # Embed
    welcome_embed = discord.Embed(
        description=message,
        color=get_color(
            config.get("color", "green")
        )
    )

    # Member avatar
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
    user="Member to give the role to.",
    role="Role to give."
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
            f"✅ Gave {role.mention} to {user.mention}."
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
    user="Member to kick.",
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
    user="Member to ban.",
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

def parse_duration(duration):

    match = re.fullmatch(
        r"(\d+)(s|m|h|d|w)",
        duration.lower().strip()
    )

    if not match:
        return None

    amount = int(match.group(1))
    unit = match.group(2)

    if unit == "s":
        return timedelta(seconds=amount)

    if unit == "m":
        return timedelta(minutes=amount)

    if unit == "h":
        return timedelta(hours=amount)

    if unit == "d":
        return timedelta(days=amount)

    if unit == "w":
        return timedelta(weeks=amount)

    return None


@bot.tree.command(
    name="timeout",
    description="Timeout a member."
)
@app_commands.describe(
    user="Member to timeout.",
    duration="Examples: 10m, 1h, 1d.",
    reason="Reason for the timeout."
)
@app_commands.checks.has_permissions(administrator=True)
async def timeout(
    interaction: discord.Interaction,
    user: discord.Member,
    duration: str,
    reason: str = "No reason provided"
):

    timeout_duration = parse_duration(duration)

    if timeout_duration is None:
        await interaction.response.send_message(
            "❌ Invalid duration.\n"
            "Use formats such as `10m`, `1h`, `1d`, or `1w`.",
            ephemeral=True
        )
        return

    if timeout_duration > timedelta(days=28):
        await interaction.response.send_message(
            "❌ Discord allows a maximum timeout of 28 days.",
            ephemeral=True
        )
        return

    try:

        await user.timeout(
            timeout_duration,
            reason=reason
        )

        await interaction.response.send_message(
            f"⏱️ **{user}** has been timed out for "
            f"**{duration}**.\n"
            f"**Reason:** {reason}"
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I cannot timeout that member.",
            ephemeral=True
        )


# ============================================================
# VERIFY SETUP
# ============================================================

@bot.tree.command(
    name="verifysetup",
    description="Set the role given when a member verifies."
)
@app_commands.describe(
    role="The role members receive when they verify."
)
@app_commands.checks.has_permissions(administrator=True)
async def verifysetup(
    interaction: discord.Interaction,
    role: discord.Role
):

    guild_id = str(interaction.guild.id)

    verify_config[guild_id] = {
        "role_id": role.id
    }

    save_json(
        VERIFY_FILE,
        verify_config
    )

    await interaction.response.send_message(
        "✅ **Verification configured!**\n\n"
        f"Verified role: {role.mention}\n\n"
        "Members can now use `/verify`.",
        ephemeral=True
    )


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

        guild_id = str(interaction.guild.id)

        config = verify_config.get(guild_id)

        if not config:
            await interaction.response.send_message(
                "❌ Verification has not been configured.",
                ephemeral=True
            )
            return

        role = interaction.guild.get_role(
            config.get("role_id")
        )

        if role is None:
            await interaction.response.send_message(
                "❌ The configured verified role no longer exists.",
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
                f"✅ You are now verified and received "
                f"{role.mention}!",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I cannot give you the verified role. "
                "Make sure my bot role is above it.",
                ephemeral=True
            )


@bot.tree.command(
    name="verify",
    description="Verify yourself and receive the verified role."
)
async def verify(
    interaction: discord.Interaction
):

    guild_id = str(interaction.guild.id)

    config = verify_config.get(guild_id)

    if not config:
        await interaction.response.send_message(
            "❌ Verification has not been configured by an administrator.",
            ephemeral=True
        )
        return

    role = interaction.guild.get_role(
        config.get("role_id")
    )

    if role is None:
        await interaction.response.send_message(
            "❌ The verified role no longer exists.",
            ephemeral=True
        )
        return

    try:
        await interaction.user.add_roles(role)

        await interaction.response.send_message(
            f"✅ You are verified! You received {role.mention}.",
            ephemeral=True
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I cannot give you that role. "
            "Move my bot role above the verified role.",
            ephemeral=True
        )


# ============================================================
# JOINT TO CREATE SETUP
# ============================================================

@bot.tree.command(
    name="jointocreate",
    description="Set up a Join to Create voice channel."
)
@app_commands.describe(
    category="Category where the Join to Create channel will be placed."
)
@app_commands.checks.has_permissions(administrator=True)
async def jointocreate(
    interaction: discord.Interaction,
    category: discord.CategoryChannel
):

    guild_id = str(interaction.guild.id)

    # Remove old JTC channel if it exists
    old_config = jtc_config.get(guild_id)

    if old_config:
        old_channel = interaction.guild.get_channel(
            old_config.get("trigger_channel_id")
        )

        if old_channel:
            try:
                await old_channel.delete(
                    reason="Replacing Join to Create channel"
                )
            except Exception:
                pass

    try:

        trigger_channel = await interaction.guild.create_voice_channel(
            name="Join to Create",
            category=category,
            reason="Join to Create setup"
        )

        jtc_config[guild_id] = {
            "trigger_channel_id": trigger_channel.id,
            "category_id": category.id
        }

        save_json(
            JTC_FILE,
            jtc_config
        )

        await interaction.response.send_message(
            "✅ **Join to Create configured!**\n\n"
            f"**Channel:** {trigger_channel.mention}\n"
            f"**Category:** {category.name}\n\n"
            "Members can join the channel to create their own VC.",
            ephemeral=True
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I need **Manage Channels** permission.",
            ephemeral=True
        )


# ============================================================
# JOIN TO CREATE
# ============================================================

@bot.event
async def on_voice_state_update(
    member,
    before,
    after
):

    # Someone joined a voice channel
    if after.channel is None:
        return

    guild_id = str(member.guild.id)

    config = jtc_config.get(guild_id)

    if not config:
        return

    trigger_id = config.get(
        "trigger_channel_id"
    )

    if after.channel.id != trigger_id:
        return

    category = member.guild.get_channel(
        config.get("category_id")
    )

    if category is None:
        return

    try:

        new_channel = await member.guild.create_voice_channel(
            name=f"{member.display_name}'s VC",
            category=category,
            reason="Join to Create"
        )

        # Move member into their new channel
        await member.move_to(new_channel)

        # Save owner information in channel topic
        try:
            await new_channel.edit(
                topic=f"JTC_OWNER:{member.id}"
            )
        except Exception:
            pass

    except discord.Forbidden:
        print(
            f"Missing permission to create VC in "
            f"{member.guild.name}"
        )


# ============================================================
# DELETE EMPTY JTC CHANNELS
# ============================================================

@bot.event
async def on_voice_state_update_cleanup(
    member,
    before,
    after
):

    # This event name will NOT be automatically called by Discord.
    # Cleanup is handled below through the same voice event.
    pass


# Replace the previous voice event with cleanup support
_original_voice_handler = on_voice_state_update


@bot.event
async def on_voice_state_update(
    member,
    before,
    after
):

    # ========================================================
    # CREATE VC
    # ========================================================

    if after.channel is not None:

        guild_id = str(member.guild.id)

        config = jtc_config.get(guild_id)

        if config:

            trigger_id = config.get(
                "trigger_channel_id"
            )

            if after.channel.id == trigger_id:

                category = member.guild.get_channel(
                    config.get("category_id")
                )

                if category:

                    try:

                        new_channel = await member.guild.create_voice_channel(
                            name=f"{member.display_name}'s VC",
                            category=category,
                            reason="Join to Create"
                        )

                        try:
                            await new_channel.edit(
                                topic=f"JTC_OWNER:{member.id}"
                            )
                        except Exception:
                            pass

                        await member.move_to(
                            new_channel
                        )

                    except Exception as error:
                        print(
                            f"JTC creation error: {error}"
                        )

    # ========================================================
    # DELETE EMPTY CHANNEL
    # ========================================================

    if before.channel is not None:

        channel = before.channel

        if (
            channel.category is not None
            and channel.topic
            and channel.topic.startswith("JTC_OWNER:")
        ):

            if len(channel.members) == 0:

                try:
                    await channel.delete(
                        reason="Empty Join to Create channel"
                    )

                except Exception as error:
                    print(
                        f"JTC deletion error: {error}"
                    )


# ============================================================
# GIVEAWAYS
# ============================================================

active_giveaways = {}


class GiveawayView(discord.ui.View):

    def __init__(self, giveaway_id):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id

    @discord.ui.button(
        label="🎉 Enter Giveaway",
        style=discord.ButtonStyle.success,
        custom_id="giveaway_enter"
    )
    async def enter(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        giveaway = active_giveaways.get(
            self.giveaway_id
        )

        if not giveaway:
            await interaction.response.send_message(
                "❌ This giveaway has ended.",
                ephemeral=True
            )
            return

        entries = giveaway["entries"]

        if interaction.user.id in entries:

            entries.remove(
                interaction.user.id
            )

            await interaction.response.send_message(
                "❌ You have left the giveaway.",
                ephemeral=True
            )

        else:

            entries.append(
                interaction.user.id
            )

            await interaction.response.send_message(
                "🎉 You entered the giveaway!",
                ephemeral=True
            )


@bot.tree.command(
    name="giveaway",
    description="Start a giveaway."
)
@app_commands.describe(
    prize="What are you giving away?",
    duration="Examples: 10m, 1h, 1d.",
    winners="Number of winners."
)
@app_commands.checks.has_permissions(administrator=True)
async def giveaway(
    interaction: discord.Interaction,
    prize: str,
    duration: str,
    winners: int = 1
):

    if winners < 1:
        await interaction.response.send_message(
            "❌ Winners must be at least 1.",
            ephemeral=True
        )
        return

    giveaway_duration = parse_duration(
        duration
    )

    if giveaway_duration is None:
        await interaction.response.send_message(
            "❌ Invalid duration. Use `10m`, `1h`, `1d`, etc.",
            ephemeral=True
        )
        return

    if giveaway_duration > timedelta(days=30):
        await interaction.response.send_message(
            "❌ Giveaway duration cannot exceed 30 days.",
            ephemeral=True
        )
        return

    giveaway_id = (
        f"{interaction.guild.id}-"
        f"{interaction.channel.id}-"
        f"{interaction.id}"
    )

    active_giveaways[giveaway_id] = {
        "entries": [],
        "prize": prize,
        "winners": winners,
        "channel_id": interaction.channel.id
    }

    embed = discord.Embed(
        title="🎉 GIVEAWAY",
        description=(
            f"**Prize:** {prize}\n\n"
            f"**Winners:** {winners}\n"
            f"**Duration:** {duration}\n\n"
            "Click the button below to enter!"
        ),
        color=discord.Color.green()
    )

    embed.set_footer(
        text=f"Started by {interaction.user}"
    )

    await interaction.response.send_message(
        embed=embed,
        view=GiveawayView(giveaway_id)
    )

    await asyncio.sleep(
        giveaway_duration.total_seconds()
    )

    giveaway_data = active_giveaways.pop(
        giveaway_id,
        None
    )

    if not giveaway_data:
        return

    channel = interaction.guild.get_channel(
        giveaway_data["channel_id"]
    )

    if channel is None:
        return

    entries = giveaway_data["entries"]

    if not entries:

        await channel.send(
            f"🎉 The giveaway for **{prize}** ended, "
            "but nobody entered."
        )

        return

    winner_count = min(
        winners,
        len(entries)
    )

    selected_winners = random.sample(
        entries,
        winner_count
    )

    mentions = " ".join(
        f"<@{user_id}>"
        for user_id in selected_winners
    )

    await channel.send(
        f"🎉 **Giveaway ended!**\n\n"
        f"**Prize:** {prize}\n"
        f"**Winner{'s' if winner_count != 1 else ''}:** "
        f"{mentions}"
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
            "Here are all the commands available."
        ),
        color=discord.Color.green()
    )

    embed.add_field(
        name="🛡️ Moderation",
        value=(
            "`/kick` — Kick a member\n"
            "`/ban` — Ban a member\n"
            "`/timeout` — Timeout a member\n"
            "`/role` — Give a role"
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
            "`/verifysetup` — Select verified role\n"
            "`/verify` — Verify yourself"
        ),
        inline=False
    )

    embed.add_field(
        name="🔊 Voice",
        value=(
            "`/jointocreate` — Create a Join to Create VC"
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

    embed.set_footer(
        text="Emerald • .gg/emerald"
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# ============================================================
# ERROR HANDLER
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
            "❌ You need **Administrator** permission "
            "to use this command."
        )

    elif isinstance(
        error,
        app_commands.CommandOnCooldown
    ):

        message = (
            "❌ Please wait before using this command again."
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
            f"Could not send error: {error}"
        )


# ============================================================
# START BOT
# ============================================================

bot.run(TOKEN)
