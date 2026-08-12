import os
import json
import asyncio
import random
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
intents.voice_states = True

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


def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as file:
            json.dump(config, file, indent=4)

    except Exception as error:
        print(f"Config save error: {error}")


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
    "gray": discord.Color.dark_gray(),
    "grey": discord.Color.dark_gray()
}


def get_color(value):
    value = str(value).lower().strip()

    if value.startswith("#"):
        try:
            number = int(value[1:], 16)

            if 0 <= number <= 0xFFFFFF:
                return discord.Color(number)

        except ValueError:
            pass

    return COLORS.get(value, discord.Color.green())


# ============================================================
# READY
# ============================================================

@bot.event
async def on_ready():

    print("======================================")
    print(f"Logged in as {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print("======================================")

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

        print(f"Synced {len(synced)} commands.")

        for command in synced:
            print(f"  /{command.name}")

    except Exception as error:
        print(f"Command sync error: {error}")


# ============================================================
# HELP
# ============================================================

@bot.tree.command(
    name="help",
    description="Show all available bot commands."
)
async def help_command(interaction: discord.Interaction):

    embed = discord.Embed(
        title="💚 Emerald Bot",
        description="Here are all of my available commands.",
        color=discord.Color.green()
    )

    embed.add_field(
        name="🛠️ Moderation",
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
            "`/welcomesetup` — Configure welcome messages"
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
            "`/verifysetup` — Set up the verification system"
        ),
        inline=False
    )

    embed.add_field(
        name="🔊 Voice",
        value=(
            "`/jointocreate` — Create a Join to Create voice channel"
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
    channel="Channel where welcome messages are sent.",
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

    guild_id = str(interaction.guild.id)

    if guild_id not in config:
        config[guild_id] = {}

    use_embed = embed.lower().strip() in (
        "yes",
        "y",
        "true",
        "on"
    )

    config[guild_id]["welcome"] = {
        "channel_id": channel.id,
        "message": message,
        "embed": use_embed,
        "color": color.lower().strip(),
        "image_url": image_url.strip()
    }

    save_config(config)

    await interaction.response.send_message(
        "✅ **Welcome system configured!**\n\n"
        f"**Channel:** {channel.mention}\n"
        f"**Embed:** {'Yes' if use_embed else 'No'}\n"
        f"**Color:** `{color}`\n"
        f"**Image:** `{image_url or 'None'}`",
        ephemeral=True
    )


# ============================================================
# WELCOME MESSAGE
# ============================================================

@bot.event
async def on_member_join(member):

    guild_id = str(member.guild.id)

    guild_config = config.get(guild_id, {})
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

    embed = discord.Embed(
        description=message,
        color=get_color(
            welcome.get("color", "green")
        )
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    image_url = welcome.get(
        "image_url",
        ""
    ).strip()

    if image_url:
        embed.set_image(url=image_url)

    try:
        await channel.send(embed=embed)

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
    user="Member receiving the role.",
    role="Role to give."
)
@app_commands.checks.has_permissions(administrator=True)
async def role(
    interaction: discord.Interaction,
    user: discord.Member,
    role: discord.Role
):

    if role.is_default():
        await interaction.response.send_message(
            "❌ You cannot give the @everyone role.",
            ephemeral=True
        )
        return

    bot_member = interaction.guild.me

    if role >= bot_member.top_role:
        await interaction.response.send_message(
            "❌ That role is above my highest role.",
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
            "❌ I cannot kick this member.",
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
            "❌ I cannot ban this member.",
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
    minutes="How many minutes to timeout them.",
    reason="Reason for the timeout."
)
@app_commands.checks.has_permissions(administrator=True)
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
        duration = discord.utils.utcnow() + discord.timedelta(
            minutes=minutes
        )

        await user.timeout(
            discord.timedelta(minutes=minutes),
            reason=reason
        )

        await interaction.response.send_message(
            f"⏰ {user.mention} has been timed out for "
            f"**{minutes} minutes**.\n"
            f"**Reason:** {reason}"
        )

    except AttributeError:
        await interaction.response.send_message(
            "❌ Timeout failed because of an incompatible "
            "Discord library version.",
            ephemeral=True
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I cannot timeout this member.",
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
    prize="What are you giving away?",
    winners="Number of winners.",
    duration="Duration in seconds."
)
@app_commands.checks.has_permissions(administrator=True)
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
            "❌ Giveaway must last at least 10 seconds.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="🎉 GIVEAWAY!",
        description=(
            f"**Prize:** {prize}\n"
            f"**Winners:** {winners}\n\n"
            "React with 🎉 to enter!"
        ),
        color=discord.Color.green()
    )

    embed.set_footer(
        text=f"Ends in {duration} seconds"
    )

    await interaction.response.send_message(
        embed=embed
    )

    giveaway_message = await interaction.original_response()

    await giveaway_message.add_reaction("🎉")

    await asyncio.sleep(duration)

    try:
        giveaway_message = await interaction.channel.fetch_message(
            giveaway_message.id
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

        winners_list = random.sample(
            users,
            min(winners, len(users))
        )

        mentions = ", ".join(
            user.mention for user in winners_list
        )

        await interaction.channel.send(
            f"🎉 Congratulations {mentions}!\n"
            f"You won **{prize}**!"
        )

    except Exception as error:
        print(f"Giveaway error: {error}")


# ============================================================
# VERIFY SETUP
# ============================================================

@bot.tree.command(
    name="verifysetup",
    description="Set up the verification system."
)
@app_commands.describe(
    channel="Channel where users verify.",
    role="Role given to verified users."
)
@app_commands.checks.has_permissions(administrator=True)
async def verifysetup(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    role: discord.Role
):

    guild_id = str(interaction.guild.id)

    if guild_id not in config:
        config[guild_id] = {}

    config[guild_id]["verify"] = {
        "channel_id": channel.id,
        "role_id": role.id
    }

    save_config(config)

    embed = discord.Embed(
        title="✅ Verification",
        description=(
            "Click the button below to verify yourself."
        ),
        color=discord.Color.green()
    )

    await channel.send(
        embed=embed,
        view=VerifyView()
    )

    await interaction.response.send_message(
        f"✅ Verification system created in {channel.mention}.\n"
        f"Verified role: {role.mention}",
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
        emoji="✅",
        custom_id="emerald_verify"
    )
    async def verify(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        guild_config = config.get(
            str(interaction.guild.id),
            {}
        )

        verify_config = guild_config.get("verify")

        if not verify_config:
            await interaction.response.send_message(
                "❌ Verification hasn't been configured.",
                ephemeral=True
            )
            return

        role = interaction.guild.get_role(
            verify_config["role_id"]
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
                "✅ You have been verified!",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I cannot give you the verified role.",
                ephemeral=True
            )


# ============================================================
# JOIN TO CREATE
# ============================================================

@bot.tree.command(
    name="jointocreate",
    description="Create a Join to Create voice channel."
)
@app_commands.describe(
    category="Category where the Join to Create channel goes."
)
@app_commands.checks.has_permissions(administrator=True)
async def jointocreate(
    interaction: discord.Interaction,
    category: discord.CategoryChannel
):

    guild_id = str(interaction.guild.id)

    if guild_id not in config:
        config[guild_id] = {}

    # Remove previous JTC if configured
    old_id = config[guild_id].get("jtc_channel_id")

    if old_id:
        old_channel = interaction.guild.get_channel(old_id)

        if old_channel:
            try:
                await old_channel.delete()
            except Exception:
                pass

    channel = await interaction.guild.create_voice_channel(
        "Join to Create",
        category=category
    )

    config[guild_id]["jtc_channel_id"] = channel.id

    save_config(config)

    await interaction.response.send_message(
        f"✅ Created {channel.mention}.\n"
        "When someone joins it, their own temporary voice "
        "channel will be created.",
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

    guild_config = config.get(
        str(member.guild.id),
        {}
    )

    jtc_id = guild_config.get(
        "jtc_channel_id"
    )

    if not jtc_id:
        return

    # Someone joined Join to Create
    if after.channel and after.channel.id == jtc_id:

        category = after.channel.category

        try:
            new_channel = await member.guild.create_voice_channel(
                name=f"{member.display_name}'s Channel",
                category=category
            )

            await member.move_to(new_channel)

            guild_config.setdefault(
                "temporary_channels",
                []
            )

            guild_config["temporary_channels"].append(
                new_channel.id
            )

            save_config(config)

        except Exception as error:
            print(f"JTC creation error: {error}")

    # Someone left a temporary channel
    if before.channel:

        temporary_channels = guild_config.get(
            "temporary_channels",
            []
        )

        if before.channel.id in temporary_channels:

            if len(before.channel.members) == 0:

                try:
                    await before.channel.delete()

                except Exception:
                    pass

                temporary_channels.remove(
                    before.channel.id
                )

                save_config(config)


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
            "❌ You need **Administrator** permission "
            "to use this command."
        )

    else:

        print(
            f"Command error: {repr(error)}"
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
            f"Could not send error: {error}"
        )


# ============================================================
# START
# ============================================================

bot.run(TOKEN)
