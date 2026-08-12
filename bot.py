import os
import json
import random
import asyncio
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

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
# PREMIUM SERVER
# ============================================================

PREMIUM_SERVER_ID = 1536942392018599937


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


config = load_config()


def save_config():
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as file:
            json.dump(config, file, indent=4)
    except Exception as error:
        print(f"Config save error: {error}")


def guild_config(guild_id):
    gid = str(guild_id)
    if gid not in config:
        config[gid] = {}
    return config[gid]


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
        "gray": discord.Color.from_rgb(128, 128, 128),
        "grey": discord.Color.from_rgb(128, 128, 128),
        "black": discord.Color.from_rgb(0, 0, 0),
        "white": discord.Color.from_rgb(255, 255, 255),
    }

    if value.startswith("#"):
        try:
            number = int(value[1:], 16)
            if 0 <= number <= 0xFFFFFF:
                return discord.Color(number)
        except ValueError:
            pass

    return colors.get(value, discord.Color.green())


# ============================================================
# PREMIUM CHECK
# ============================================================

async def has_premium(interaction):
    """
    Premium means the user is a member of the configured
    Premium Discord server.
    """

    premium_guild = bot.get_guild(PREMIUM_SERVER_ID)

    if premium_guild is None:
        await interaction.response.send_message(
            "❌ The Premium server is not available to the bot right now.",
            ephemeral=True
        )
        return False

    try:
        premium_member = premium_guild.get_member(interaction.user.id)

        if premium_member is None:
            premium_member = await premium_guild.fetch_member(
                interaction.user.id
            )

    except discord.NotFound:
        premium_member = None

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I cannot check Premium membership right now.",
            ephemeral=True
        )
        return False

    if premium_member is None:
        await interaction.response.send_message(
            "❌ **You don't have Premium.**\n\n"
            "Join the Premium server / open a ticket to buy Premium!",
            ephemeral=True
        )
        return False

    return True


async def require_premium_admin(interaction):
    if not await has_premium(interaction):
        return False

    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ This command can only be used inside a server.",
            ephemeral=True
        )
        return False

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ **Administrator permission required.**",
            ephemeral=True
        )
        return False

    return True


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

        print(f"Synced {len(synced)} commands.")

        for command in synced:
            print(f"Registered: /{command.name}")

        bot.add_view(TicketPanelView())
        bot.add_view(TicketCloseView())

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
        description="Here are the available commands.",
        color=discord.Color.green()
    )

    embed.add_field(
        name="🛡️ Moderation",
        value=(
            "`/kick`\n"
            "`/ban`\n"
            "`/timeout`\n"
            "`/role`\n"
            "`/purgeall` ⭐ Premium"
        ),
        inline=False
    )

    embed.add_field(
        name="👋 Welcome",
        value=(
            "`/welcomesetup` — Admin\n"
            "`/leavemessagesetup` — Premium + Admin"
            "`/ticketsetup` — Admin"
        ),
        inline=False
    )

    embed.add_field(
        name="🎉 Fun / Utility",
        value=(
            "`/giveaway` — Admin\n"
            "`/afk`\n"
            "`/roblox`\n"
            "`/serverage`\n"
            "`/member count`\n"
            "`/show all roles`"
        ),
        inline=False
    )

    embed.add_field(
        name="🎮 Premium Systems",
        value=(
            "`/countingsetup`\n"
            "`/verifysetup`\n"
            "`/jointocreate`\n"
            "`/antinuke setup`\n"
            "`/levelsetup`"
        ),
        inline=False
    )

    embed.set_footer(text="⭐ = Premium")

    await interaction.response.send_message(embed=embed)


# ============================================================
# WELCOME SETUP
# ============================================================

@bot.tree.command(
    name="welcomesetup",
    description="Set up welcome messages."
)
@app_commands.describe(
    channel="Welcome channel.",
    message="Message. Use {user} to mention the member.",
    embed="Use an embed? yes or no.",
    color="Embed color.",
    image_url="Optional image URL."
)
async def welcomesetup(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    message: str,
    embed: str = "no",
    color: str = "green",
    image_url: str = ""
):
    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Use this command in a server.",
            ephemeral=True
        )
        return

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ **Administrator permission required.**",
            ephemeral=True
        )
        return

    data = guild_config(interaction.guild.id)

    data["welcome"] = {
        "channel_id": channel.id,
        "message": message,
        "embed": embed.lower().strip() in ("yes", "y", "true", "on"),
        "color": color,
        "image_url": image_url.strip()
    }

    save_config()

    await interaction.response.send_message(
        "✅ **Welcome system configured!**",
        ephemeral=True
    )


# ============================================================
# LEAVE MESSAGE SETUP - PREMIUM
# ============================================================

@bot.tree.command(
    name="leavemessagesetup",
    description="Set up Premium leave messages."
)
@app_commands.describe(
    channel="Leave message channel.",
    message="Leave message. Use {left user}, {left username}, or {left displayname}.",
    embed="Use an embed? yes or no.",
    color="Embed color.",
    image_url="Optional image URL."
)
async def leavemessagesetup(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    message: str,
    embed: str = "no",
    color: str = "green",
    image_url: str = ""
):
    if not await require_premium_admin(interaction):
        return

    data = guild_config(interaction.guild.id)

    data["leave"] = {
        "channel_id": channel.id,
        "message": message,
        "embed": embed.lower().strip() in ("yes", "y", "true", "on"),
        "color": color,
        "image_url": image_url.strip()
    }

    save_config()

    await interaction.response.send_message(
        "✅ **Premium leave-message system configured!**",
        ephemeral=True
    )


# ============================================================
# WELCOME EVENT
# ============================================================

@bot.event
async def on_member_join(member):

    data = guild_config(member.guild.id)
    welcome = data.get("welcome")

    if welcome:
        channel = member.guild.get_channel(
            welcome.get("channel_id")
        )

        if channel:
            message = welcome.get(
                "message",
                "Welcome {user}!"
            ).replace(
                "{user}",
                member.mention
            )

            if welcome.get("embed"):
                embed = discord.Embed(
                    description=message,
                    color=get_color(
                        welcome.get("color", "green")
                    )
                )

                embed.set_thumbnail(
                    url=member.display_avatar.url
                )

                if welcome.get("image_url"):
                    embed.set_image(
                        url=welcome["image_url"]
                    )

                try:
                    await channel.send(embed=embed)
                except Exception as error:
                    print(f"Welcome embed error: {error}")
            else:
                try:
                    await channel.send(message)
                except Exception as error:
                    print(f"Welcome error: {error}")


# ============================================================
# LEAVE EVENT
# ============================================================

@bot.event
async def on_member_remove(member):

    data = guild_config(member.guild.id)
    leave = data.get("leave")

    if not leave:
        return

    channel = member.guild.get_channel(
        leave.get("channel_id")
    )

    if channel is None:
        return

    message = leave.get(
        "message",
        "A member has left the server."
    )

    message = message.replace("{left user}", member.mention)
    message = message.replace("{left username}", member.name)
    message = message.replace("{left displayname}", member.display_name)

    if leave.get("embed"):
        embed = discord.Embed(
            description=message,
            color=get_color(
                leave.get("color", "green")
            )
        )

        if leave.get("image_url"):
            embed.set_image(
                url=leave["image_url"]
            )

        try:
            await channel.send(embed=embed)
        except Exception as error:
            print(f"Leave embed error: {error}")

    else:
        try:
            await channel.send(message)
        except Exception as error:
            print(f"Leave error: {error}")


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
async def role(
    interaction: discord.Interaction,
    user: discord.Member,
    role: discord.Role
):
    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Use this in a server.",
            ephemeral=True
        )
        return

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ **Administrator permission required.**",
            ephemeral=True
        )
        return

    bot_member = interaction.guild.me

    if role.is_default():
        await interaction.response.send_message(
            "❌ You cannot give @everyone.",
            ephemeral=True
        )
        return

    if bot_member is None or role >= bot_member.top_role:
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
async def kick(
    interaction: discord.Interaction,
    user: discord.Member,
    reason: str = "No reason provided"
):
    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Use this in a server.",
            ephemeral=True
        )
        return

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ **Administrator permission required.**",
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
async def ban(
    interaction: discord.Interaction,
    user: discord.Member,
    reason: str = "No reason provided"
):
    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Use this in a server.",
            ephemeral=True
        )
        return

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ **Administrator permission required.**",
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
async def timeout(
    interaction: discord.Interaction,
    user: discord.Member,
    minutes: int,
    reason: str = "No reason provided"
):
    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Use this in a server.",
            ephemeral=True
        )
        return

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ **Administrator permission required.**",
            ephemeral=True
        )
        return

    if minutes < 1 or minutes > 40320:
        await interaction.response.send_message(
            "❌ Timeout must be between 1 minute and 28 days.",
            ephemeral=True
        )
        return

    try:
        await user.timeout(
            timedelta(minutes=minutes),
            reason=reason
        )

        await interaction.response.send_message(
            f"⏰ {user.mention} has been timed out "
            f"for **{minutes} minutes**."
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
    prize="Prize.",
    winners="Number of winners.",
    duration="Duration in seconds."
)
async def giveaway(
    interaction: discord.Interaction,
    prize: str,
    winners: int,
    duration: int
):
    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Use this in a server.",
            ephemeral=True
        )
        return

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ **Administrator permission required.**",
            ephemeral=True
        )
        return

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

    await interaction.response.send_message(embed=embed)

    message = await interaction.original_response()
    await message.add_reaction("🎉")

    await asyncio.sleep(duration)

    try:
        message = await interaction.channel.fetch_message(
            message.id
        )

        reaction = discord.utils.get(
            message.reactions,
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

        winners_selected = random.sample(
            users,
            min(winners, len(users))
        )

        mentions = ", ".join(
            user.mention
            for user in winners_selected
        )

        await interaction.channel.send(
            f"🎉 Congratulations {mentions}!\n"
            f"You won **{prize}**!"
        )

    except Exception as error:
        print(f"Giveaway error: {error}")


# ============================================================
# VERIFY
# ============================================================

class VerifyView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

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
        data = guild_config(interaction.guild.id)
        verify = data.get("verify")

        if not verify:
            await interaction.response.send_message(
                "❌ Verification is not configured.",
                ephemeral=True
            )
            return

        role = interaction.guild.get_role(
            verify.get("role_id")
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
                "✅ You are now verified!",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I cannot give you the verified role.",
                ephemeral=True
            )


@bot.tree.command(
    name="verifysetup",
    description="Set up Premium verification."
)
@app_commands.describe(
    channel="Verification channel.",
    role="Verified role."
)
async def verifysetup(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    role: discord.Role
):
    if not await require_premium_admin(interaction):
        return

    data = guild_config(interaction.guild.id)

    data["verify"] = {
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
# COUNTING SETUP
# ============================================================

@bot.tree.command(
    name="countingsetup",
    description="Set up Premium counting."
)
@app_commands.describe(
    channel="The counting channel."
)
async def countingsetup(
    interaction: discord.Interaction,
    channel: discord.TextChannel
):
    if not await require_premium_admin(interaction):
        return

    data = guild_config(interaction.guild.id)

    data["counting"] = {
        "channel_id": channel.id,
        "next": 1,
        "last_user_id": None
    }

    save_config()

    embed = discord.Embed(
        title="🔢 Counting Started",
        description=(
            f"Use {channel.mention}.\n\n"
            "Start with **1**.\n"
            "Then another member can type **2**, "
            "then **3**, and so on."
        ),
        color=discord.Color.green()
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# ============================================================
# JOIN TO CREATE
# ============================================================

@bot.tree.command(
    name="jointocreate",
    description="Set up Premium Join To Create."
)
@app_commands.describe(
    category="Category for temporary voice channels."
)
async def jointocreate(
    interaction: discord.Interaction,
    category: discord.CategoryChannel
):
    if not await require_premium_admin(interaction):
        return

    guild = interaction.guild
    data = guild_config(guild.id)

    old_id = data.get("jtc_trigger")

    if old_id:
        old_channel = guild.get_channel(old_id)
        if old_channel:
            try:
                await old_channel.delete(
                    reason="Replacing old JTC channel"
                )
            except Exception:
                pass

    try:
        trigger = await guild.create_voice_channel(
            name="Join To Create",
            category=category,
            reason="Premium Join To Create setup"
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I need **Manage Channels** permission.",
            ephemeral=True
        )
        return

    data["jtc_trigger"] = trigger.id
    save_config()

    await interaction.response.send_message(
        f"✅ Join To Create is ready: {trigger.mention}",
        ephemeral=True
    )


# ============================================================
# JTC EVENT
# ============================================================

@bot.event
async def on_voice_state_update(
    member,
    before,
    after
):
    data = guild_config(member.guild.id)
    trigger_id = data.get("jtc_trigger")

    if not trigger_id:
        return

    if (
        after.channel is not None
        and after.channel.id == trigger_id
    ):
        try:
            new_channel = await member.guild.create_voice_channel(
                name=f"{member.display_name}'s Channel",
                category=after.channel.category,
                reason="Join To Create temporary channel"
            )

            await member.move_to(
                new_channel,
                reason="Join To Create"
            )

            print(
                f"JTC created {new_channel.name} "
                f"for {member}"
            )

        except Exception as error:
            print(f"JTC error: {error}")

        return

    if before.channel is None:
        return

    old_channel = before.channel

    if old_channel.id == trigger_id:
        return

    if not old_channel.name.endswith("'s Channel"):
        return

    if old_channel.members:
        return

    try:
        await old_channel.delete(
            reason="Empty Join To Create channel"
        )
    except Exception as error:
        print(f"JTC delete error: {error}")


# ============================================================
# PURGEALL - PREMIUM
# ============================================================

@bot.tree.command(
    name="purgeall",
    description="Delete a number of messages from this channel."
)
@app_commands.describe(
    amount="Number of messages to delete."
)
async def purgeall(
    interaction: discord.Interaction,
    amount: int
):
    if not await require_premium_admin(interaction):
        return

    if amount < 1 or amount > 1000:
        await interaction.response.send_message(
            "❌ Amount must be between 1 and 1000.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    try:
        deleted = await interaction.channel.purge(
            limit=amount
        )

        await interaction.followup.send(
            f"🗑️ Deleted **{len(deleted)}** messages "
            f"in this channel.",
            ephemeral=True
        )

    except discord.Forbidden:
        await interaction.followup.send(
            "❌ I need **Manage Messages** permission.",
            ephemeral=True
        )

    except Exception as error:
        print(f"Purge error: {error}")

        await interaction.followup.send(
            "❌ Failed to purge messages.",
            ephemeral=True
        )


# ============================================================
# ANTI NUKE
# ============================================================

antinuke_hits = {}


async def antinuke_action(guild, executor_id, action_name):
    data = guild_config(guild.id)
    anti = data.get("antinuke")

    if not anti or not anti.get("enabled"):
        return

    now = datetime.now(timezone.utc).timestamp()

    key = (guild.id, executor_id, action_name)

    hits = antinuke_hits.setdefault(key, [])

    hits[:] = [
        timestamp
        for timestamp in hits
        if now - timestamp <= 10
    ]

    hits.append(now)

    threshold = int(
        anti.get("threshold", 3)
    )

    if len(hits) < threshold:
        return

    member = guild.get_member(executor_id)

    if member is None:
        return

    if member.id == bot.user.id:
        return

    if member.id == guild.owner_id:
        return

    try:
        await guild.ban(
            member,
            reason=f"Anti-Nuke: {action_name} threshold exceeded"
        )

        print(
            f"ANTI-NUKE: Banned {member} "
            f"for {action_name}"
        )

    except discord.Forbidden:
        print(
            "ANTI-NUKE: Could not ban executor. "
            "Check Ban Members permission."
        )

    hits.clear()


async def find_audit_executor(
    guild,
    action,
    target_id=None
):
    try:
        async for entry in guild.audit_logs(
            limit=10,
            action=action
        ):
            if target_id is not None:
                if getattr(entry.target, "id", None) != target_id:
                    continue

            if (
                datetime.now(timezone.utc) - entry.created_at
            ).total_seconds() > 8:
                continue

            return entry.user

    except discord.Forbidden:
        print(
            "ANTI-NUKE: Bot needs View Audit Log."
        )

    except Exception as error:
        print(
            f"Audit log error: {error}"
        )

    return None


@bot.event
async def on_guild_channel_delete(channel):
    executor = await find_audit_executor(
        channel.guild,
        discord.AuditLogAction.channel_delete,
        channel.id
    )

    if executor:
        await antinuke_action(
            channel.guild,
            executor.id,
            "channel deletion"
        )


@bot.event
async def on_guild_role_delete(role):
    executor = await find_audit_executor(
        role.guild,
        discord.AuditLogAction.role_delete,
        role.id
    )

    if executor:
        await antinuke_action(
            role.guild,
            executor.id,
            "role deletion"
        )


@bot.event
async def on_member_ban(guild, user):
    executor = await find_audit_executor(
        guild,
        discord.AuditLogAction.ban,
        user.id
    )

    if executor:
        await antinuke_action(
            guild,
            executor.id,
            "member banning"
        )


@bot.event
async def on_member_join(member):
    # Anti-nuke bot-add detection
    if member.bot:
        executor = await find_audit_executor(
            member.guild,
            discord.AuditLogAction.bot_add,
            member.id
        )

        if executor:
            await antinuke_action(
                member.guild,
                executor.id,
                "bot additions"
            )

            data = guild_config(member.guild.id)

            if data.get("antinuke", {}).get("enabled"):
                try:
                    await member.kick(
                        reason="Anti-Nuke: suspicious bot addition"
                    )
                except Exception:
                    pass

    # Welcome system
    data = guild_config(member.guild.id)
    welcome = data.get("welcome")

    if welcome:
        channel = member.guild.get_channel(
            welcome.get("channel_id")
        )

        if channel:
            message = welcome.get(
                "message",
                "Welcome {user}!"
            ).replace(
                "{user}",
                member.mention
            )

            if welcome.get("embed"):
                embed = discord.Embed(
                    description=message,
                    color=get_color(
                        welcome.get("color", "green")
                    )
                )

                embed.set_thumbnail(
                    url=member.display_avatar.url
                )

                if welcome.get("image_url"):
                    embed.set_image(
                        url=welcome["image_url"]
                    )

                try:
                    await channel.send(embed=embed)
                except Exception as error:
                    print(f"Welcome error: {error}")
            else:
                try:
                    await channel.send(message)
                except Exception as error:
                    print(f"Welcome error: {error}")


# ============================================================
# ANTI NUKE SETUP
# ============================================================

antinuke_group = app_commands.Group(
    name="antinuke",
    description="Premium anti-nuke protection."
)


@antinuke_group.command(
    name="setup",
    description="Enable Premium anti-nuke protection."
)
@app_commands.describe(
    threshold="Actions within 10 seconds before protection activates."
)
async def antinuke_setup(
    interaction: discord.Interaction,
    threshold: int = 3
):
    if not await require_premium_admin(interaction):
        return

    if threshold < 2 or threshold > 10:
        await interaction.response.send_message(
            "❌ Threshold must be between 2 and 10.",
            ephemeral=True
        )
        return

    data = guild_config(interaction.guild.id)

    data["antinuke"] = {
        "enabled": True,
        "threshold": threshold
    }

    save_config()

    await interaction.response.send_message(
        "🛡️ **Anti-Nuke enabled.**\n"
        f"Threshold: **{threshold} actions in 10 seconds**.",
        ephemeral=True
    )


bot.tree.add_command(antinuke_group)


# ============================================================
# LEVEL SYSTEM
# ============================================================

@bot.tree.command(
    name="levelsetup",
    description="Set a Premium level requirement and create its role."
)
@app_commands.describe(
    level="Level number.",
    messages="Messages required to reach this level."
)
async def levelsetup(
    interaction: discord.Interaction,
    level: int,
    messages: int
):
    if not await require_premium_admin(interaction):
        return

    if level < 1:
        await interaction.response.send_message(
            "❌ Level must be 1 or higher.",
            ephemeral=True
        )
        return

    if messages < 1:
        await interaction.response.send_message(
            "❌ Messages must be 1 or higher.",
            ephemeral=True
        )
        return

    data = guild_config(interaction.guild.id)

    level_data = data.setdefault(
        "levels",
        {
            "enabled": True,
            "thresholds": {},
            "xp": {}
        }
    )

    level_data["enabled"] = True
    level_data["thresholds"][str(level)] = messages

    role_name = f"Level {level}"

    role = discord.utils.find(
        lambda r: r.name == role_name,
        interaction.guild.roles
    )

    if role is None:
        try:
            role = await interaction.guild.create_role(
                name=role_name,
                color=discord.Color.green(),
                reason="Premium level system"
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I need **Manage Roles** to create level roles.",
                ephemeral=True
            )
            return

    save_config()

    await interaction.response.send_message(
        f"✅ **Level system updated!**\n\n"
        f"**Level:** {level}\n"
        f"**Messages:** {messages}\n"
        f"**Role:** {role.mention}",
        ephemeral=True
    )


# ============================================================
# MEMBER COUNT
# ============================================================

member_group = app_commands.Group(
    name="member",
    description="Member information."
)


@member_group.command(
    name="count",
    description="Show the server member count."
)
async def member_count(
    interaction: discord.Interaction
):
    guild = interaction.guild

    if guild is None:
        await interaction.response.send_message(
            "❌ Use this in a server.",
            ephemeral=True
        )
        return

    humans = sum(
        1 for member in guild.members
        if not member.bot
    )

    bots = sum(
        1 for member in guild.members
        if member.bot
    )

    embed = discord.Embed(
        title="👥 Server Members",
        color=discord.Color.green()
    )

    embed.add_field(
        name="👤 Humans",
        value=str(humans),
        inline=True
    )

    embed.add_field(
        name="🤖 Bots",
        value=str(bots),
        inline=True
    )

    embed.add_field(
        name="📊 Total",
        value=str(humans + bots),
        inline=True
    )

    await interaction.response.send_message(
        embed=embed
    )


bot.tree.add_command(member_group)


# ============================================================
# AFK
# ============================================================

@bot.tree.command(
    name="afk",
    description="Set your AFK status."
)
@app_commands.describe(
    reason="Why you are AFK."
)
async def afk(
    interaction: discord.Interaction,
    reason: str
):
    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Use this in a server.",
            ephemeral=True
        )
        return

    data = guild_config(interaction.guild.id)

    afk_data = data.setdefault(
        "afk",
        {}
    )

    afk_data[str(interaction.user.id)] = {
        "reason": reason,
        "time": datetime.now(
            timezone.utc
        ).isoformat()
    }

    save_config()

    await interaction.response.send_message(
        f"💤 You are now AFK: **{reason}**"
    )


# ============================================================
# ROBLOX HELPERS
# ============================================================

def roblox_request(
    url,
    method="GET",
    body=None
):
    headers = {
        "User-Agent": "EmeraldDiscordBot/1.0"
    }

    data = None

    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method
    )

    with urllib.request.urlopen(
        request,
        timeout=10
    ) as response:
        return json.loads(
            response.read().decode("utf-8")
        )


async def roblox_lookup(username):
    def lookup():
        result = roblox_request(
            "https://users.roblox.com/v1/usernames/users",
            method="POST",
            body={
                "usernames": [username],
                "excludeBannedUsers": False
            }
        )

        users = result.get("data", [])

        if not users:
            return None

        user = users[0]
        user_id = user["id"]

        details = roblox_request(
            f"https://users.roblox.com/v1/users/{user_id}"
        )

        try:
            friends = roblox_request(
                f"https://friends.roblox.com/v1/users/"
                f"{user_id}/friends/count"
            ).get("count", 0)
        except Exception:
            friends = 0

        try:
            followers = roblox_request(
                f"https://friends.roblox.com/v1/users/"
                f"{user_id}/followers/count"
            ).get("count", 0)
        except Exception:
            followers = 0

        return {
            "id": user_id,
            "name": details.get(
                "name",
                user.get("name", username)
            ),
            "display_name": details.get(
                "displayName",
                user.get("displayName", "")
            ),
            "created": details.get("created"),
            "friends": friends,
            "followers": followers
        }

    try:
        return await asyncio.to_thread(lookup)
    except Exception as error:
        print(f"Roblox API error: {error}")
        return None


# ============================================================
# ROBLOX
# ============================================================

@bot.tree.command(
    name="roblox",
    description="Look up a Roblox username."
)
@app_commands.describe(
    username="Roblox username."
)
async def roblox(
    interaction: discord.Interaction,
    username: str
):
    await interaction.response.defer()

    result = await roblox_lookup(username)

    if result is None:
        await interaction.followup.send(
            "❌ I couldn't find that Roblox username."
        )
        return

    created_text = "Unknown"

    if result.get("created"):
        try:
            created_date = datetime.fromisoformat(
                result["created"].replace(
                    "Z",
                    "+00:00"
                )
            )

            created_text = discord.utils.format_dt(
                created_date,
                style="F"
            )

        except Exception:
            created_text = result["created"]

    embed = discord.Embed(
        title=f"🎮 Roblox — {result['name']}",
        color=discord.Color.green()
    )

    embed.add_field(
        name="👤 Username",
        value=result["name"],
        inline=True
    )

    embed.add_field(
        name="✨ Display Name",
        value=result["display_name"],
        inline=True
    )

    embed.add_field(
        name="🆔 User ID",
        value=str(result["id"]),
        inline=True
    )

    embed.add_field(
        name="📅 Created",
        value=created_text,
        inline=False
    )

    embed.add_field(
        name="👥 Friends",
        value=str(result["friends"]),
        inline=True
    )

    embed.add_field(
        name="❤️ Followers",
        value=str(result["followers"]),
        inline=True
    )

    await interaction.followup.send(
        embed=embed
    )


# ============================================================
# SHOW ALL ROLES
# ============================================================

show_group = app_commands.Group(
    name="show",
    description="Show server information."
)

show_all_group = app_commands.Group(
    name="all",
    description="Show all information.",
    parent=show_group
)


@show_all_group.command(
    name="roles",
    description="Show all server roles."
)
async def show_all_roles(
    interaction: discord.Interaction
):
    guild = interaction.guild

    if guild is None:
        await interaction.response.send_message(
            "❌ Use this in a server.",
            ephemeral=True
        )
        return

    roles = list(
        reversed(guild.roles)
    )

    lines = []

    for role in roles:
        if role.is_default():
            continue

        lines.append(
            f"{role.mention} — `{role.id}`"
        )

    if not lines:
        text = "No custom roles."
    else:
        text = "\n".join(lines)

    # Keep within Discord embed limits.
    if len(text) > 3900:
        text = text[:3890] + "\n..."

    embed = discord.Embed(
        title="📋 Server Roles",
        description=text,
        color=discord.Color.green()
    )

    await interaction.response.send_message(
        embed=embed
    )


bot.tree.add_command(show_group)


# ============================================================
# SERVER AGE
# ============================================================

@bot.tree.command(
    name="serverage",
    description="Show how old the server is."
)
async def serverage(
    interaction: discord.Interaction
):
    guild = interaction.guild

    if guild is None:
        await interaction.response.send_message(
            "❌ Use this in a server.",
            ephemeral=True
        )
        return

    created = guild.created_at
    now = datetime.now(timezone.utc)

    days = (now - created).days

    years = days // 365
    remaining_days = days % 365

    embed = discord.Embed(
        title="📅 Server Age",
        color=discord.Color.green()
    )

    embed.add_field(
        name="Created",
        value=discord.utils.format_dt(
            created,
            style="F"
        ),
        inline=False
    )

    embed.add_field(
        name="Age",
        value=(
            f"**{years} years, "
            f"{remaining_days} days**\n"
            f"({days} total days)"
        ),
        inline=False
    )

    await interaction.response.send_message(
        embed=embed
    )


import os
import json
import random
import asyncio
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

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
# PREMIUM SERVER
# ============================================================

PREMIUM_SERVER_ID = 1536942392018599937


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


config = load_config()


def save_config():
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as file:
            json.dump(config, file, indent=4)
    except Exception as error:
        print(f"Config save error: {error}")


def guild_config(guild_id):
    gid = str(guild_id)
    if gid not in config:
        config[gid] = {}
    return config[gid]


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
        "gray": discord.Color.from_rgb(128, 128, 128),
        "grey": discord.Color.from_rgb(128, 128, 128),
        "black": discord.Color.from_rgb(0, 0, 0),
        "white": discord.Color.from_rgb(255, 255, 255),
    }

    if value.startswith("#"):
        try:
            number = int(value[1:], 16)
            if 0 <= number <= 0xFFFFFF:
                return discord.Color(number)
        except ValueError:
            pass

    return colors.get(value, discord.Color.green())


# ============================================================
# PREMIUM CHECK
# ============================================================

async def has_premium(interaction):
    """
    Premium means the user is a member of the configured
    Premium Discord server.
    """

    premium_guild = bot.get_guild(PREMIUM_SERVER_ID)

    if premium_guild is None:
        await interaction.response.send_message(
            "❌ The Premium server is not available to the bot right now.",
            ephemeral=True
        )
        return False

    try:
        premium_member = premium_guild.get_member(interaction.user.id)

        if premium_member is None:
            premium_member = await premium_guild.fetch_member(
                interaction.user.id
            )

    except discord.NotFound:
        premium_member = None

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I cannot check Premium membership right now.",
            ephemeral=True
        )
        return False

    if premium_member is None:
        await interaction.response.send_message(
            "❌ **You don't have Premium.**\n\n"
            "Join the Premium server / open a ticket to buy Premium!",
            ephemeral=True
        )
        return False

    return True


async def require_premium_admin(interaction):
    if not await has_premium(interaction):
        return False

    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ This command can only be used inside a server.",
            ephemeral=True
        )
        return False

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ **Administrator permission required.**",
            ephemeral=True
        )
        return False

    return True


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

        print(f"Synced {len(synced)} commands.")

        for command in synced:
            print(f"Registered: /{command.name}")

        bot.add_view(TicketPanelView())
        bot.add_view(TicketCloseView())

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
        description="Here are the available commands.",
        color=discord.Color.green()
    )

    embed.add_field(
        name="🛡️ Moderation",
        value=(
            "`/kick`\n"
            "`/ban`\n"
            "`/timeout`\n"
            "`/role`\n"
            "`/purgeall` ⭐ Premium"
        ),
        inline=False
    )

    embed.add_field(
        name="👋 Welcome",
        value=(
            "`/welcomesetup` — Admin\n"
            "`/leavemessagesetup` — Premium + Admin"
            "`/ticketsetup` — Admin"
        ),
        inline=False
    )

    embed.add_field(
        name="🎉 Fun / Utility",
        value=(
            "`/giveaway` — Admin\n"
            "`/afk`\n"
            "`/roblox`\n"
            "`/serverage`\n"
            "`/member count`\n"
            "`/show all roles`"
        ),
        inline=False
    )

    embed.add_field(
        name="🎮 Premium Systems",
        value=(
            "`/countingsetup`\n"
            "`/verifysetup`\n"
            "`/jointocreate`\n"
            "`/antinuke setup`\n"
            "`/levelsetup`"
        ),
        inline=False
    )

    embed.set_footer(text="⭐ = Premium")

    await interaction.response.send_message(embed=embed)


# ============================================================
# WELCOME SETUP
# ============================================================

@bot.tree.command(
    name="welcomesetup",
    description="Set up welcome messages."
)
@app_commands.describe(
    channel="Welcome channel.",
    message="Message. Use {user} to mention the member.",
    embed="Use an embed? yes or no.",
    color="Embed color.",
    image_url="Optional image URL."
)
async def welcomesetup(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    message: str,
    embed: str = "no",
    color: str = "green",
    image_url: str = ""
):
    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Use this command in a server.",
            ephemeral=True
        )
        return

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ **Administrator permission required.**",
            ephemeral=True
        )
        return

    data = guild_config(interaction.guild.id)

    data["welcome"] = {
        "channel_id": channel.id,
        "message": message,
        "embed": embed.lower().strip() in ("yes", "y", "true", "on"),
        "color": color,
        "image_url": image_url.strip()
    }

    save_config()

    await interaction.response.send_message(
        "✅ **Welcome system configured!**",
        ephemeral=True
    )


# ============================================================
# LEAVE MESSAGE SETUP - PREMIUM
# ============================================================

@bot.tree.command(
    name="leavemessagesetup",
    description="Set up Premium leave messages."
)
@app_commands.describe(
    channel="Leave message channel.",
    message="Leave message. Use {left user}, {left username}, or {left displayname}.",
    embed="Use an embed? yes or no.",
    color="Embed color.",
    image_url="Optional image URL."
)
async def leavemessagesetup(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    message: str,
    embed: str = "no",
    color: str = "green",
    image_url: str = ""
):
    if not await require_premium_admin(interaction):
        return

    data = guild_config(interaction.guild.id)

    data["leave"] = {
        "channel_id": channel.id,
        "message": message,
        "embed": embed.lower().strip() in ("yes", "y", "true", "on"),
        "color": color,
        "image_url": image_url.strip()
    }

    save_config()

    await interaction.response.send_message(
        "✅ **Premium leave-message system configured!**",
        ephemeral=True
    )


# ============================================================
# WELCOME EVENT
# ============================================================

@bot.event
async def on_member_join(member):

    data = guild_config(member.guild.id)
    welcome = data.get("welcome")

    if welcome:
        channel = member.guild.get_channel(
            welcome.get("channel_id")
        )

        if channel:
            message = welcome.get(
                "message",
                "Welcome {user}!"
            ).replace(
                "{user}",
                member.mention
            )

            if welcome.get("embed"):
                embed = discord.Embed(
                    description=message,
                    color=get_color(
                        welcome.get("color", "green")
                    )
                )

                embed.set_thumbnail(
                    url=member.display_avatar.url
                )

                if welcome.get("image_url"):
                    embed.set_image(
                        url=welcome["image_url"]
                    )

                try:
                    await channel.send(embed=embed)
                except Exception as error:
                    print(f"Welcome embed error: {error}")
            else:
                try:
                    await channel.send(message)
                except Exception as error:
                    print(f"Welcome error: {error}")


# ============================================================
# LEAVE EVENT
# ============================================================

@bot.event
async def on_member_remove(member):

    data = guild_config(member.guild.id)
    leave = data.get("leave")

    if not leave:
        return

    channel = member.guild.get_channel(
        leave.get("channel_id")
    )

    if channel is None:
        return

    message = leave.get(
        "message",
        "A member has left the server."
    )

    message = message.replace("{left user}", member.mention)
    message = message.replace("{left username}", member.name)
    message = message.replace("{left displayname}", member.display_name)

    if leave.get("embed"):
        embed = discord.Embed(
            description=message,
            color=get_color(
                leave.get("color", "green")
            )
        )

        if leave.get("image_url"):
            embed.set_image(
                url=leave["image_url"]
            )

        try:
            await channel.send(embed=embed)
        except Exception as error:
            print(f"Leave embed error: {error}")

    else:
        try:
            await channel.send(message)
        except Exception as error:
            print(f"Leave error: {error}")


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
async def role(
    interaction: discord.Interaction,
    user: discord.Member,
    role: discord.Role
):
    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Use this in a server.",
            ephemeral=True
        )
        return

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ **Administrator permission required.**",
            ephemeral=True
        )
        return

    bot_member = interaction.guild.me

    if role.is_default():
        await interaction.response.send_message(
            "❌ You cannot give @everyone.",
            ephemeral=True
        )
        return

    if bot_member is None or role >= bot_member.top_role:
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
async def kick(
    interaction: discord.Interaction,
    user: discord.Member,
    reason: str = "No reason provided"
):
    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Use this in a server.",
            ephemeral=True
        )
        return

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ **Administrator permission required.**",
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
async def ban(
    interaction: discord.Interaction,
    user: discord.Member,
    reason: str = "No reason provided"
):
    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Use this in a server.",
            ephemeral=True
        )
        return

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ **Administrator permission required.**",
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
async def timeout(
    interaction: discord.Interaction,
    user: discord.Member,
    minutes: int,
    reason: str = "No reason provided"
):
    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Use this in a server.",
            ephemeral=True
        )
        return

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ **Administrator permission required.**",
            ephemeral=True
        )
        return

    if minutes < 1 or minutes > 40320:
        await interaction.response.send_message(
            "❌ Timeout must be between 1 minute and 28 days.",
            ephemeral=True
        )
        return

    try:
        await user.timeout(
            timedelta(minutes=minutes),
            reason=reason
        )

        await interaction.response.send_message(
            f"⏰ {user.mention} has been timed out "
            f"for **{minutes} minutes**."
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
    prize="Prize.",
    winners="Number of winners.",
    duration="Duration in seconds."
)
async def giveaway(
    interaction: discord.Interaction,
    prize: str,
    winners: int,
    duration: int
):
    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Use this in a server.",
            ephemeral=True
        )
        return

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ **Administrator permission required.**",
            ephemeral=True
        )
        return

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

    await interaction.response.send_message(embed=embed)

    message = await interaction.original_response()
    await message.add_reaction("🎉")

    await asyncio.sleep(duration)

    try:
        message = await interaction.channel.fetch_message(
            message.id
        )

        reaction = discord.utils.get(
            message.reactions,
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

        winners_selected = random.sample(
            users,
            min(winners, len(users))
        )

        mentions = ", ".join(
            user.mention
            for user in winners_selected
        )

        await interaction.channel.send(
            f"🎉 Congratulations {mentions}!\n"
            f"You won **{prize}**!"
        )

    except Exception as error:
        print(f"Giveaway error: {error}")


# ============================================================
# VERIFY
# ============================================================

class VerifyView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

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
        data = guild_config(interaction.guild.id)
        verify = data.get("verify")

        if not verify:
            await interaction.response.send_message(
                "❌ Verification is not configured.",
                ephemeral=True
            )
            return

        role = interaction.guild.get_role(
            verify.get("role_id")
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
                "✅ You are now verified!",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I cannot give you the verified role.",
                ephemeral=True
            )


@bot.tree.command(
    name="verifysetup",
    description="Set up Premium verification."
)
@app_commands.describe(
    channel="Verification channel.",
    role="Verified role."
)
async def verifysetup(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    role: discord.Role
):
    if not await require_premium_admin(interaction):
        return

    data = guild_config(interaction.guild.id)

    data["verify"] = {
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
# COUNTING SETUP
# ============================================================

@bot.tree.command(
    name="countingsetup",
    description="Set up Premium counting."
)
@app_commands.describe(
    channel="The counting channel."
)
async def countingsetup(
    interaction: discord.Interaction,
    channel: discord.TextChannel
):
    if not await require_premium_admin(interaction):
        return

    data = guild_config(interaction.guild.id)

    data["counting"] = {
        "channel_id": channel.id,
        "next": 1,
        "last_user_id": None
    }

    save_config()

    embed = discord.Embed(
        title="🔢 Counting Started",
        description=(
            f"Use {channel.mention}.\n\n"
            "Start with **1**.\n"
            "Then another member can type **2**, "
            "then **3**, and so on."
        ),
        color=discord.Color.green()
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# ============================================================
# JOIN TO CREATE
# ============================================================

@bot.tree.command(
    name="jointocreate",
    description="Set up Premium Join To Create."
)
@app_commands.describe(
    category="Category for temporary voice channels."
)
async def jointocreate(
    interaction: discord.Interaction,
    category: discord.CategoryChannel
):
    if not await require_premium_admin(interaction):
        return

    guild = interaction.guild
    data = guild_config(guild.id)

    old_id = data.get("jtc_trigger")

    if old_id:
        old_channel = guild.get_channel(old_id)
        if old_channel:
            try:
                await old_channel.delete(
                    reason="Replacing old JTC channel"
                )
            except Exception:
                pass

    try:
        trigger = await guild.create_voice_channel(
            name="Join To Create",
            category=category,
            reason="Premium Join To Create setup"
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I need **Manage Channels** permission.",
            ephemeral=True
        )
        return

    data["jtc_trigger"] = trigger.id
    save_config()

    await interaction.response.send_message(
        f"✅ Join To Create is ready: {trigger.mention}",
        ephemeral=True
    )


# ============================================================
# JTC EVENT
# ============================================================

@bot.event
async def on_voice_state_update(
    member,
    before,
    after
):
    data = guild_config(member.guild.id)
    trigger_id = data.get("jtc_trigger")

    if not trigger_id:
        return

    if (
        after.channel is not None
        and after.channel.id == trigger_id
    ):
        try:
            new_channel = await member.guild.create_voice_channel(
                name=f"{member.display_name}'s Channel",
                category=after.channel.category,
                reason="Join To Create temporary channel"
            )

            await member.move_to(
                new_channel,
                reason="Join To Create"
            )

            print(
                f"JTC created {new_channel.name} "
                f"for {member}"
            )

        except Exception as error:
            print(f"JTC error: {error}")

        return

    if before.channel is None:
        return

    old_channel = before.channel

    if old_channel.id == trigger_id:
        return

    if not old_channel.name.endswith("'s Channel"):
        return

    if old_channel.members:
        return

    try:
        await old_channel.delete(
            reason="Empty Join To Create channel"
        )
    except Exception as error:
        print(f"JTC delete error: {error}")


# ============================================================
# PURGEALL - PREMIUM
# ============================================================

@bot.tree.command(
    name="purgeall",
    description="Delete a number of messages from this channel."
)
@app_commands.describe(
    amount="Number of messages to delete."
)
async def purgeall(
    interaction: discord.Interaction,
    amount: int
):
    if not await require_premium_admin(interaction):
        return

    if amount < 1 or amount > 1000:
        await interaction.response.send_message(
            "❌ Amount must be between 1 and 1000.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    try:
        deleted = await interaction.channel.purge(
            limit=amount
        )

        await interaction.followup.send(
            f"🗑️ Deleted **{len(deleted)}** messages "
            f"in this channel.",
            ephemeral=True
        )

    except discord.Forbidden:
        await interaction.followup.send(
            "❌ I need **Manage Messages** permission.",
            ephemeral=True
        )

    except Exception as error:
        print(f"Purge error: {error}")

        await interaction.followup.send(
            "❌ Failed to purge messages.",
            ephemeral=True
        )


# ============================================================
# ANTI NUKE
# ============================================================

antinuke_hits = {}


async def antinuke_action(guild, executor_id, action_name):
    data = guild_config(guild.id)
    anti = data.get("antinuke")

    if not anti or not anti.get("enabled"):
        return

    now = datetime.now(timezone.utc).timestamp()

    key = (guild.id, executor_id, action_name)

    hits = antinuke_hits.setdefault(key, [])

    hits[:] = [
        timestamp
        for timestamp in hits
        if now - timestamp <= 10
    ]

    hits.append(now)

    threshold = int(
        anti.get("threshold", 3)
    )

    if len(hits) < threshold:
        return

    member = guild.get_member(executor_id)

    if member is None:
        return

    if member.id == bot.user.id:
        return

    if member.id == guild.owner_id:
        return

    try:
        await guild.ban(
            member,
            reason=f"Anti-Nuke: {action_name} threshold exceeded"
        )

        print(
            f"ANTI-NUKE: Banned {member} "
            f"for {action_name}"
        )

    except discord.Forbidden:
        print(
            "ANTI-NUKE: Could not ban executor. "
            "Check Ban Members permission."
        )

    hits.clear()


async def find_audit_executor(
    guild,
    action,
    target_id=None
):
    try:
        async for entry in guild.audit_logs(
            limit=10,
            action=action
        ):
            if target_id is not None:
                if getattr(entry.target, "id", None) != target_id:
                    continue

            if (
                datetime.now(timezone.utc) - entry.created_at
            ).total_seconds() > 8:
                continue

            return entry.user

    except discord.Forbidden:
        print(
            "ANTI-NUKE: Bot needs View Audit Log."
        )

    except Exception as error:
        print(
            f"Audit log error: {error}"
        )

    return None


@bot.event
async def on_guild_channel_delete(channel):
    executor = await find_audit_executor(
        channel.guild,
        discord.AuditLogAction.channel_delete,
        channel.id
    )

    if executor:
        await antinuke_action(
            channel.guild,
            executor.id,
            "channel deletion"
        )


@bot.event
async def on_guild_role_delete(role):
    executor = await find_audit_executor(
        role.guild,
        discord.AuditLogAction.role_delete,
        role.id
    )

    if executor:
        await antinuke_action(
            role.guild,
            executor.id,
            "role deletion"
        )


@bot.event
async def on_member_ban(guild, user):
    executor = await find_audit_executor(
        guild,
        discord.AuditLogAction.ban,
        user.id
    )

    if executor:
        await antinuke_action(
            guild,
            executor.id,
            "member banning"
        )


@bot.event
async def on_member_join(member):
    # Anti-nuke bot-add detection
    if member.bot:
        executor = await find_audit_executor(
            member.guild,
            discord.AuditLogAction.bot_add,
            member.id
        )

        if executor:
            await antinuke_action(
                member.guild,
                executor.id,
                "bot additions"
            )

            data = guild_config(member.guild.id)

            if data.get("antinuke", {}).get("enabled"):
                try:
                    await member.kick(
                        reason="Anti-Nuke: suspicious bot addition"
                    )
                except Exception:
                    pass

    # Welcome system
    data = guild_config(member.guild.id)
    welcome = data.get("welcome")

    if welcome:
        channel = member.guild.get_channel(
            welcome.get("channel_id")
        )

        if channel:
            message = welcome.get(
                "message",
                "Welcome {user}!"
            ).replace(
                "{user}",
                member.mention
            )

            if welcome.get("embed"):
                embed = discord.Embed(
                    description=message,
                    color=get_color(
                        welcome.get("color", "green")
                    )
                )

                embed.set_thumbnail(
                    url=member.display_avatar.url
                )

                if welcome.get("image_url"):
                    embed.set_image(
                        url=welcome["image_url"]
                    )

                try:
                    await channel.send(embed=embed)
                except Exception as error:
                    print(f"Welcome error: {error}")
            else:
                try:
                    await channel.send(message)
                except Exception as error:
                    print(f"Welcome error: {error}")


# ============================================================
# ANTI NUKE SETUP
# ============================================================

antinuke_group = app_commands.Group(
    name="antinuke",
    description="Premium anti-nuke protection."
)


@antinuke_group.command(
    name="setup",
    description="Enable Premium anti-nuke protection."
)
@app_commands.describe(
    threshold="Actions within 10 seconds before protection activates."
)
async def antinuke_setup(
    interaction: discord.Interaction,
    threshold: int = 3
):
    if not await require_premium_admin(interaction):
        return

    if threshold < 2 or threshold > 10:
        await interaction.response.send_message(
            "❌ Threshold must be between 2 and 10.",
            ephemeral=True
        )
        return

    data = guild_config(interaction.guild.id)

    data["antinuke"] = {
        "enabled": True,
        "threshold": threshold
    }

    save_config()

    await interaction.response.send_message(
        "🛡️ **Anti-Nuke enabled.**\n"
        f"Threshold: **{threshold} actions in 10 seconds**.",
        ephemeral=True
    )


bot.tree.add_command(antinuke_group)


# ============================================================
# LEVEL SYSTEM
# ============================================================

@bot.tree.command(
    name="levelsetup",
    description="Set a Premium level requirement and create its role."
)
@app_commands.describe(
    level="Level number.",
    messages="Messages required to reach this level."
)
async def levelsetup(
    interaction: discord.Interaction,
    level: int,
    messages: int
):
    if not await require_premium_admin(interaction):
        return

    if level < 1:
        await interaction.response.send_message(
            "❌ Level must be 1 or higher.",
            ephemeral=True
        )
        return

    if messages < 1:
        await interaction.response.send_message(
            "❌ Messages must be 1 or higher.",
            ephemeral=True
        )
        return

    data = guild_config(interaction.guild.id)

    level_data = data.setdefault(
        "levels",
        {
            "enabled": True,
            "thresholds": {},
            "xp": {}
        }
    )

    level_data["enabled"] = True
    level_data["thresholds"][str(level)] = messages

    role_name = f"Level {level}"

    role = discord.utils.find(
        lambda r: r.name == role_name,
        interaction.guild.roles
    )

    if role is None:
        try:
            role = await interaction.guild.create_role(
                name=role_name,
                color=discord.Color.green(),
                reason="Premium level system"
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I need **Manage Roles** to create level roles.",
                ephemeral=True
            )
            return

    save_config()

    await interaction.response.send_message(
        f"✅ **Level system updated!**\n\n"
        f"**Level:** {level}\n"
        f"**Messages:** {messages}\n"
        f"**Role:** {role.mention}",
        ephemeral=True
    )


# ============================================================
# MEMBER COUNT
# ============================================================

member_group = app_commands.Group(
    name="member",
    description="Member information."
)


@member_group.command(
    name="count",
    description="Show the server member count."
)
async def member_count(
    interaction: discord.Interaction
):
    guild = interaction.guild

    if guild is None:
        await interaction.response.send_message(
            "❌ Use this in a server.",
            ephemeral=True
        )
        return

    humans = sum(
        1 for member in guild.members
        if not member.bot
    )

    bots = sum(
        1 for member in guild.members
        if member.bot
    )

    embed = discord.Embed(
        title="👥 Server Members",
        color=discord.Color.green()
    )

    embed.add_field(
        name="👤 Humans",
        value=str(humans),
        inline=True
    )

    embed.add_field(
        name="🤖 Bots",
        value=str(bots),
        inline=True
    )

    embed.add_field(
        name="📊 Total",
        value=str(humans + bots),
        inline=True
    )

    await interaction.response.send_message(
        embed=embed
    )


bot.tree.add_command(member_group)


# ============================================================
# AFK
# ============================================================

@bot.tree.command(
    name="afk",
    description="Set your AFK status."
)
@app_commands.describe(
    reason="Why you are AFK."
)
async def afk(
    interaction: discord.Interaction,
    reason: str
):
    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Use this in a server.",
            ephemeral=True
        )
        return

    data = guild_config(interaction.guild.id)

    afk_data = data.setdefault(
        "afk",
        {}
    )

    afk_data[str(interaction.user.id)] = {
        "reason": reason,
        "time": datetime.now(
            timezone.utc
        ).isoformat()
    }

    save_config()

    await interaction.response.send_message(
        f"💤 You are now AFK: **{reason}**"
    )


# ============================================================
# ROBLOX HELPERS
# ============================================================

def roblox_request(
    url,
    method="GET",
    body=None
):
    headers = {
        "User-Agent": "EmeraldDiscordBot/1.0"
    }

    data = None

    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method
    )

    with urllib.request.urlopen(
        request,
        timeout=10
    ) as response:
        return json.loads(
            response.read().decode("utf-8")
        )


async def roblox_lookup(username):
    def lookup():
        result = roblox_request(
            "https://users.roblox.com/v1/usernames/users",
            method="POST",
            body={
                "usernames": [username],
                "excludeBannedUsers": False
            }
        )

        users = result.get("data", [])

        if not users:
            return None

        user = users[0]
        user_id = user["id"]

        details = roblox_request(
            f"https://users.roblox.com/v1/users/{user_id}"
        )

        try:
            friends = roblox_request(
                f"https://friends.roblox.com/v1/users/"
                f"{user_id}/friends/count"
            ).get("count", 0)
        except Exception:
            friends = 0

        try:
            followers = roblox_request(
                f"https://friends.roblox.com/v1/users/"
                f"{user_id}/followers/count"
            ).get("count", 0)
        except Exception:
            followers = 0

        return {
            "id": user_id,
            "name": details.get(
                "name",
                user.get("name", username)
            ),
            "display_name": details.get(
                "displayName",
                user.get("displayName", "")
            ),
            "created": details.get("created"),
            "friends": friends,
            "followers": followers
        }

    try:
        return await asyncio.to_thread(lookup)
    except Exception as error:
        print(f"Roblox API error: {error}")
        return None


# ============================================================
# ROBLOX
# ============================================================

@bot.tree.command(
    name="roblox",
    description="Look up a Roblox username."
)
@app_commands.describe(
    username="Roblox username."
)
async def roblox(
    interaction: discord.Interaction,
    username: str
):
    await interaction.response.defer()

    result = await roblox_lookup(username)

    if result is None:
        await interaction.followup.send(
            "❌ I couldn't find that Roblox username."
        )
        return

    created_text = "Unknown"

    if result.get("created"):
        try:
            created_date = datetime.fromisoformat(
                result["created"].replace(
                    "Z",
                    "+00:00"
                )
            )

            created_text = discord.utils.format_dt(
                created_date,
                style="F"
            )

        except Exception:
            created_text = result["created"]

    embed = discord.Embed(
        title=f"🎮 Roblox — {result['name']}",
        color=discord.Color.green()
    )

    embed.add_field(
        name="👤 Username",
        value=result["name"],
        inline=True
    )

    embed.add_field(
        name="✨ Display Name",
        value=result["display_name"],
        inline=True
    )

    embed.add_field(
        name="🆔 User ID",
        value=str(result["id"]),
        inline=True
    )

    embed.add_field(
        name="📅 Created",
        value=created_text,
        inline=False
    )

    embed.add_field(
        name="👥 Friends",
        value=str(result["friends"]),
        inline=True
    )

    embed.add_field(
        name="❤️ Followers",
        value=str(result["followers"]),
        inline=True
    )

    await interaction.followup.send(
        embed=embed
    )


# ============================================================
# SHOW ALL ROLES
# ============================================================

show_group = app_commands.Group(
    name="show",
    description="Show server information."
)

show_all_group = app_commands.Group(
    name="all",
    description="Show all information.",
    parent=show_group
)


@show_all_group.command(
    name="roles",
    description="Show all server roles."
)
async def show_all_roles(
    interaction: discord.Interaction
):
    guild = interaction.guild

    if guild is None:
        await interaction.response.send_message(
            "❌ Use this in a server.",
            ephemeral=True
        )
        return

    roles = list(
        reversed(guild.roles)
    )

    lines = []

    for role in roles:
        if role.is_default():
            continue

        lines.append(
            f"{role.mention} — `{role.id}`"
        )

    if not lines:
        text = "No custom roles."
    else:
        text = "\n".join(lines)

    # Keep within Discord embed limits.
    if len(text) > 3900:
        text = text[:3890] + "\n..."

    embed = discord.Embed(
        title="📋 Server Roles",
        description=text,
        color=discord.Color.green()
    )

    await interaction.response.send_message(
        embed=embed
    )


bot.tree.add_command(show_group)


# ============================================================
# SERVER AGE
# ============================================================

@bot.tree.command(
    name="serverage",
    description="Show how old the server is."
)
async def serverage(
    interaction: discord.Interaction
):
    guild = interaction.guild

    if guild is None:
        await interaction.response.send_message(
            "❌ Use this in a server.",
            ephemeral=True
        )
        return

    created = guild.created_at
    now = datetime.now(timezone.utc)

    days = (now - created).days

    years = days // 365
    remaining_days = days % 365

    embed = discord.Embed(
        title="📅 Server Age",
        color=discord.Color.green()
    )

    embed.add_field(
        name="Created",
        value=discord.utils.format_dt(
            created,
            style="F"
        ),
        inline=False
    )

    embed.add_field(
        name="Age",
        value=(
            f"**{years} years, "
            f"{remaining_days} days**\n"
            f"({days} total days)"
        ),
        inline=False
    )

    await interaction.response.send_message(
        embed=embed
    )


# ============================================================
# TICKET SYSTEM
# ============================================================

TICKET_TYPES = {
    "support": ("🎫", "General Support", "Need help with something?"),
    "report": ("🚨", "Report a User", "Report a member or problem."),
    "purchase": ("💳", "Purchase Help", "Questions about purchases or Premium."),
    "partnership": ("🤝", "Partnership", "Business or server partnership requests."),
    "staff": ("🛡️", "Staff Application", "Apply for a staff position."),
}


class TicketTypeSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=label, description=description, emoji=emoji, value=value) for value, (emoji, label, description) in TICKET_TYPES.items()]
        super().__init__(placeholder="Choose what you need help with...", min_values=1, max_values=1, options=options, custom_id="emerald_ticket_select")

    async def callback(self, interaction: discord.Interaction):
        data = guild_config(interaction.guild.id)
        ticket_data = data.get("tickets")
        if not ticket_data or not ticket_data.get("enabled"):
            await interaction.response.send_message("❌ The ticket system is not configured.", ephemeral=True)
            return

        category = interaction.guild.get_channel(ticket_data.get("category_id"))
        staff_role = interaction.guild.get_role(ticket_data.get("staff_role_id"))
        if category is None or not isinstance(category, discord.CategoryChannel):
            await interaction.response.send_message("❌ The ticket category no longer exists.", ephemeral=True)
            return
        if staff_role is None:
            await interaction.response.send_message("❌ The ticket staff role no longer exists.", ephemeral=True)
            return

        for channel in category.channels:
            if isinstance(channel, discord.TextChannel) and channel.topic == f"ticket_owner:{interaction.user.id}":
                await interaction.response.send_message(f"❌ You already have an open ticket: {channel.mention}", ephemeral=True)
                return

        value = self.values[0]
        emoji, label, description = TICKET_TYPES[value]
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, attach_files=True),
            staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True, manage_messages=True),
        }

        safe_name = "".join(c if c.isalnum() or c == "-" else "-" for c in interaction.user.name.lower()).strip("-")[:20]
        try:
            channel = await interaction.guild.create_text_channel(name=f"ticket-{safe_name or interaction.user.id}", category=category, topic=f"ticket_owner:{interaction.user.id}", overwrites=overwrites, reason=f"Ticket created by {interaction.user}")
        except discord.Forbidden:
            await interaction.response.send_message("❌ I need **Manage Channels** permission to create tickets.", ephemeral=True)
            return
        except Exception as error:
            print(f"Ticket creation error: {error}")
            await interaction.response.send_message("❌ I couldn't create the ticket.", ephemeral=True)
            return

        embed = discord.Embed(title=f"{emoji} {label}", description=(f"Welcome {interaction.user.mention}!\n\n**Reason:** {description}\nA member of {staff_role.mention} will help you shortly.\n\nPlease explain your issue with as much detail as possible."), color=discord.Color.green())
        embed.set_footer(text="Emerald Tickets")
        try:
            await channel.send(content=f"{interaction.user.mention} {staff_role.mention}", embed=embed, view=TicketCloseView())
        except Exception as error:
            print(f"Ticket welcome message error: {error}")
        await interaction.response.send_message(f"✅ Your **{label}** ticket has been created: {channel.mention}", ephemeral=True)


class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketTypeSelect())


class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="emerald_ticket_close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = guild_config(interaction.guild.id)
        staff_role = interaction.guild.get_role(data.get("tickets", {}).get("staff_role_id"))
        is_staff = interaction.user.guild_permissions.manage_channels or (staff_role is not None and staff_role in interaction.user.roles)
        if not is_staff and interaction.channel.topic != f"ticket_owner:{interaction.user.id}":
            await interaction.response.send_message("❌ Only the ticket owner or ticket staff can close this ticket.", ephemeral=True)
            return
        await interaction.response.send_message("🔒 Closing this ticket...", ephemeral=True)
        await asyncio.sleep(1)
        try:
            await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
        except Exception as error:
            print(f"Ticket close error: {error}")


@bot.tree.command(name="ticketsetup", description="Set up the ticket panel and staff role.")
@app_commands.describe(category="Category where ticket channels will be created.", staff_role="Role that can view and manage tickets.")
async def ticketsetup(interaction: discord.Interaction, category: discord.CategoryChannel, staff_role: discord.Role):
    if interaction.guild is None:
        await interaction.response.send_message("❌ Use this command in a server.", ephemeral=True)
        return
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ **Administrator permission required.**", ephemeral=True)
        return
    data = guild_config(interaction.guild.id)
    data["tickets"] = {"enabled": True, "category_id": category.id, "staff_role_id": staff_role.id}
    save_config()
    embed = discord.Embed(title="🎫 Emerald Tickets", description="Need help? Select the type of ticket you want to open below.\n\nChoose the option that best matches your request. A member of staff will be notified when your ticket is created.", color=discord.Color.green())
    embed.set_footer(text="Please do not open unnecessary tickets.")
    await interaction.channel.send(embed=embed, view=TicketPanelView())
    await interaction.response.send_message(f"✅ **Ticket system configured!**\nCategory: {category.mention}\nStaff role: {staff_role.mention}", ephemeral=True)


# ============================================================
# MESSAGE EVENT
# ============================================================

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if message.guild is None:
        await bot.process_commands(message)
        return

    data = guild_config(
        message.guild.id
    )

    # ========================================================
    # AFK
    # ========================================================

    afk_data = data.get(
        "afk",
        {}
    )

    author_id = str(
        message.author.id
    )

    if author_id in afk_data:

        del afk_data[author_id]
        save_config()

        try:
            await message.channel.send(
                f"👋 Welcome back, "
                f"{message.author.mention}! "
                f"Your AFK has been removed.",
                delete_after=5
            )
        except Exception:
            pass

    # Check mentioned AFK users
    for mentioned in message.mentions:

        mentioned_id = str(
            mentioned.id
        )

        if mentioned_id not in afk_data:
            continue

        reason = afk_data[
            mentioned_id
        ].get(
            "reason",
            "No reason provided."
        )

        try:
            await message.channel.send(
                f"❌ You cannot ping {mentioned.mention}; "
                f"they are AFK!\n"
                f"**Reason:** {reason}",
                delete_after=8
            )
        except Exception:
            pass

    # ========================================================
    # COUNTING
    # ========================================================

    counting = data.get("counting")
    if counting:
        channel_id = counting.get("channel_id")
        if message.channel.id == channel_id:
            try:
                number = int(message.content.strip())
            except ValueError:
                await bot.process_commands(message)
                return
            expected = int(counting.get("next", 1))
            last_user_id = counting.get("last_user_id")
            if last_user_id == message.author.id:
                streak = max(0, expected - 1)
                counting["next"] = 1
                counting["last_user_id"] = None
                save_config()
                try:
                    await message.channel.send(f"❌ {message.author.mention} counted twice in a row!\n💥 Streak lost at **{streak}**!\n🔄 Start again with **1**.")
                except Exception:
                    pass
                await bot.process_commands(message)
                return
            if number == expected:
                try:
                    await message.add_reaction("✅")
                except Exception:
                    pass
                counting["next"] = expected + 1
                counting["last_user_id"] = message.author.id
                save_config()
            else:
                streak = max(0, expected - 1)
                counting["next"] = 1
                counting["last_user_id"] = None
                save_config()
                try:
                    await message.channel.send(f"❌ Oh no {message.author.mention} has ruined the streak at **{streak}**!\n🔄 Start again with **1**.")
                except Exception:
                    pass
                await bot.process_commands(message)
                return

    # ========================================================
    # LEVEL SYSTEM
    # ========================================================

    levels = data.get("levels")

    if levels and levels.get("enabled"):

        user_id = str(
            message.author.id
        )

        xp = levels.setdefault(
            "xp",
            {}
        )

        xp[user_id] = int(
            xp.get(user_id, 0)
        ) + 1

        thresholds = levels.get(
            "thresholds",
            {}
        )

        current_level = 0

        for level_string, required_messages in thresholds.items():

            try:
                level_number = int(level_string)
                required = int(required_messages)

                if xp[user_id] >= required:
                    current_level = max(
                        current_level,
                        level_number
                    )

            except (ValueError, TypeError):
                continue

        if current_level > 0:

            role_name = f"Level {current_level}"

            role = discord.utils.find(
                lambda r: r.name == role_name,
                message.guild.roles
            )

            if role and role < message.guild.me.top_role:
                try:
                    await message.author.add_roles(
                        role,
                        reason="Level system"
                    )
                except Exception:
                    pass

        save_config()

    await bot.process_commands(message)


# ============================================================
# COMMAND ERRORS
# ============================================================

@bot.tree.error
async def command_error(
    interaction,
    error
):

    print(
        f"COMMAND ERROR: {repr(error)}"
    )

    if isinstance(
        error,
        app_commands.MissingPermissions
    ):
        message = (
            "❌ **Administrator permission required.**"
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

    except Exception as send_error:
        print(
            f"Error handler error: {send_error}"
        )


# ============================================================
# START
# ============================================================

print("Starting Emerald Bot...")

bot.run(TOKEN)

# ============================================================
# MESSAGE EVENT
# ============================================================

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if message.guild is None:
        await bot.process_commands(message)
        return

    data = guild_config(
        message.guild.id
    )

    # ========================================================
    # AFK
    # ========================================================

    afk_data = data.get(
        "afk",
        {}
    )

    author_id = str(
        message.author.id
    )

    if author_id in afk_data:

        del afk_data[author_id]
        save_config()

        try:
            await message.channel.send(
                f"👋 Welcome back, "
                f"{message.author.mention}! "
                f"Your AFK has been removed.",
                delete_after=5
            )
        except Exception:
            pass

    # Check mentioned AFK users
    for mentioned in message.mentions:

        mentioned_id = str(
            mentioned.id
        )

        if mentioned_id not in afk_data:
            continue

        reason = afk_data[
            mentioned_id
        ].get(
            "reason",
            "No reason provided."
        )

        try:
            await message.channel.send(
                f"❌ You cannot ping {mentioned.mention}; "
                f"they are AFK!\n"
                f"**Reason:** {reason}",
                delete_after=8
            )
        except Exception:
            pass

    # ========================================================
    # COUNTING
    # ========================================================

    counting = data.get("counting")
    if counting:
        channel_id = counting.get("channel_id")
        if message.channel.id == channel_id:
            try:
                number = int(message.content.strip())
            except ValueError:
                await bot.process_commands(message)
                return
            expected = int(counting.get("next", 1))
            last_user_id = counting.get("last_user_id")
            if last_user_id == message.author.id:
                streak = max(0, expected - 1)
                counting["next"] = 1
                counting["last_user_id"] = None
                save_config()
                try:
                    await message.channel.send(f"❌ {message.author.mention} counted twice in a row!\n💥 Streak lost at **{streak}**!\n🔄 Start again with **1**.")
                except Exception:
                    pass
                await bot.process_commands(message)
                return
            if number == expected:
                try:
                    await message.add_reaction("✅")
                except Exception:
                    pass
                counting["next"] = expected + 1
                counting["last_user_id"] = message.author.id
                save_config()
            else:
                streak = max(0, expected - 1)
                counting["next"] = 1
                counting["last_user_id"] = None
                save_config()
                try:
                    await message.channel.send(f"❌ Oh no {message.author.mention} has ruined the streak at **{streak}**!\n🔄 Start again with **1**.")
                except Exception:
                    pass
                await bot.process_commands(message)
                return

    # ========================================================
    # LEVEL SYSTEM
    # ========================================================

    levels = data.get("levels")

    if levels and levels.get("enabled"):

        user_id = str(
            message.author.id
        )

        xp = levels.setdefault(
            "xp",
            {}
        )

        xp[user_id] = int(
            xp.get(user_id, 0)
        ) + 1

        thresholds = levels.get(
            "thresholds",
            {}
        )

        current_level = 0

        for level_string, required_messages in thresholds.items():

            try:
                level_number = int(level_string)
                required = int(required_messages)

                if xp[user_id] >= required:
                    current_level = max(
                        current_level,
                        level_number
                    )

            except (ValueError, TypeError):
                continue

        if current_level > 0:

            role_name = f"Level {current_level}"

            role = discord.utils.find(
                lambda r: r.name == role_name,
                message.guild.roles
            )

            if role and role < message.guild.me.top_role:
                try:
                    await message.author.add_roles(
                        role,
                        reason="Level system"
                    )
                except Exception:
                    pass

        save_config()

    await bot.process_commands(message)


# ============================================================
# COMMAND ERRORS
# ============================================================

@bot.tree.error
async def command_error(
    interaction,
    error
):

    print(
        f"COMMAND ERROR: {repr(error)}"
    )

    if isinstance(
        error,
        app_commands.MissingPermissions
    ):
        message = (
            "❌ **Administrator permission required.**"
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

    except Exception as send_error:
        print(
            f"Error handler error: {send_error}"
        )


# ============================================================
# START
# ============================================================

print("Starting Emerald Bot...")

bot.run(TOKEN)
