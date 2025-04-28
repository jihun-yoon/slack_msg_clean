# slack_msg_clean

A Python package to delete your messages in any Slack channel or direct message.

## Slack App Creation & Setup

1. **Create a Slack App**
   - Go to https://api.slack.com/apps and click **Create New App**.
   - Choose **From scratch**, give it a name (e.g. `Slack MSG Clean Bot`), and select your workspace.
2. **Retrieve Signing Secret**
   - In your app settings under **Basic Information**, find **App Credentials**.
   - Copy the **Signing Secret** value.
3. **Enable Socket Mode & App-Level Token**
   - Under **Settings > Socket Mode**, enable **Socket Mode**.
   - Scroll to **App-Level Tokens**, click **Generate Token and Scopes**:
     - Name: `socket-mode`
     - Scope: `connections:write`
   - Copy the generated **App-Level Token** (`xapp-…`).
4. **Configure OAuth & Permissions**
   - Go to **OAuth & Permissions**.
   - Add **Bot Token Scopes**:
     - `chat:write`
   - Add **User Token Scopes**:
     - `im:history`
     - `mpim:history`
     - `channels:history`
     - `groups:history`
     - `chat:write`
   - Click **Install to Workspace** (or **Reinstall to Workspace**) and authorize.
   - Copy the **Bot User OAuth Token** (`xoxb-…`) and the **OAuth Access Token** (`xoxp-…`).
5. **Create a Slash Command**
   - In **Features > Slash Commands**, click **Create New Command**.
   - Command: `/delete_dm_messages`
   - Request URL: (Socket Mode ignores this, you may enter a placeholder.)
   - Short description: `Delete my messages in the current channel or DM.`
   - Save and **Reinstall to Workspace** to apply.

## Environment Variables

Set the following in your shell:

```bash
export SLACK_SIGNING_SECRET='your-signing-secret'
export SLACK_BOT_TOKEN='xoxb-your-bot-token'
export SLACK_USER_TOKEN='xoxp-your-user-token'
export SLACK_APP_TOKEN='xapp-your-app-token'

## Installation
```bash
pip install git_https://github.com/jihun-yoon/slack_msg_clean.git
```

## Usage
Start the bot with one of thte following:
```bash
# Using console script entry point
slack-dm-clean

# Or directly with Python
python -m slack_dm_clean.app
```

Then, in any Slack channel or DM, type:
```bash
/delete_dm_messages
```

Your messages in that channel or DM will be deleted, and processing logs will appear in your terminal.