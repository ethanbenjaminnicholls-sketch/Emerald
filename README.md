# One More Day Discord Bot

A public Discord bot with:
- `/welcomeSetup`
- `/role`
- `/kick`
- `/ban`

## Railway setup

1. Upload/deploy this project to Railway.
2. Create a Railway environment variable:
   - Name: `DISCORD_TOKEN`
   - Value: your Discord bot token
3. Deploy/redeploy.
4. The bot will start with `python bot.py`.

Do NOT put your Discord token in any file in this project.

## Discord permissions

The bot needs:
- View Channels
- Send Messages
- Manage Roles
- Kick Members
- Ban Members

Enable the **Server Members Intent** in the Discord Developer Portal.

The bot's role must be above roles it needs to assign or users it needs to moderate.

## Welcome setup

Use:

`/welcomeSetup channel:#welcome message:Welcome {user} to the server!`

`{user}` is replaced with the joining member's mention.

Each Discord server has its own welcome configuration.

## Public installation

For a public bot, invite it with the OAuth2 scopes:
- `bot`
- `applications.commands`

Then select the permissions listed above.
