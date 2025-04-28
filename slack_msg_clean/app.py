import os
import time
import sys
import logging
import datetime
import http.client

from slack_bolt import App
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_bolt.adapter.socket_mode import SocketModeHandler

# ─────────────────────────────────────────────────────────────────────────────
# Logging configuration: write to stdout
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Load environment variables
# ─────────────────────────────────────────────────────────────────────────────
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_USER_TOKEN = os.environ["SLACK_USER_TOKEN"]
SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]

# ─────────────────────────────────────────────────────────────────────────────
# Initialize Bolt App and WebClient
# ─────────────────────────────────────────────────────────────────────────────
app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)
user_client = WebClient(token=SLACK_USER_TOKEN)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def human_ts(ts_str: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Convert Slack ts string to human-readable timestamp."""
    dt = datetime.datetime.fromtimestamp(float(ts_str))
    return dt.strftime(fmt)


def post_feedback(client, channel: str, user: str, text: str):
    """
    Send ephemeral feedback if possible; otherwise send a normal message.
    """
    try:
        client.chat_postEphemeral(channel=channel, user=user, text=text)
    except SlackApiError as e:
        if e.response.get("error") == "channel_not_found":
            client.chat_postMessage(channel=channel, text=text)
        else:
            logger.error(f"post_feedback failed: {e.response.get('error')}")


def fetch_history(channel_id: str, cursor: str = None):
    """
    Fetch conversations.history with retry on IncompleteRead.
    """
    while True:
        try:
            return user_client.conversations_history(
                channel=channel_id, cursor=cursor, limit=100
            )
        except http.client.IncompleteRead as e:
            logger.warning(
                f"IncompleteRead during history fetch ({e.partial!r}), retrying..."
            )
            time.sleep(1)


# ─────────────────────────────────────────────────────────────────────────────
# Slash Command handler: delete your messages in the current channel or DM
# ─────────────────────────────────────────────────────────────────────────────
@app.command("/delete_msg")
def delete_my_messages(ack, body, client):
    ack()
    user_id = body.get("user_id")
    channel_id = body.get("channel_id")
    logger.info(f"Request from user={user_id} in channel={channel_id}")

    deleted = 0
    cursor = None

    try:
        while True:
            resp = fetch_history(channel_id, cursor)
            messages = resp.get("messages", [])
            logger.info(
                f"Fetched {len(messages)} messages (has_more={resp.get('has_more')})"
            )

            for msg in messages:
                if msg.get("user") != user_id:
                    continue
                ts = msg.get("ts")
                human = human_ts(ts)
                logger.info(f"Deleting message at {human} (ts={ts})")

                # delete with rate-limit handling
                while True:
                    try:
                        user_client.chat_delete(channel=channel_id, ts=ts)
                        deleted += 1
                        logger.info(f"Deleted message at {human}")
                        break
                    except SlackApiError as e:
                        err = e.response.get("error")
                        if err == "ratelimited":
                            retry = int(e.response.headers.get("Retry-After", 1))
                            logger.warning(f"Rate limited, retrying after {retry}s")
                            time.sleep(retry)
                            continue
                        logger.error(f"chat_delete failed: {err}")
                        break
                time.sleep(0.1)

            next_cursor = resp.get("response_metadata", {}).get("next_cursor")
            logger.info(f"Next cursor: {next_cursor!r}")
            if not next_cursor:
                # no valid cursor → end paging
                break
            cursor = next_cursor

        logger.info(f"Total deleted={deleted}")
    except SlackApiError as e:
        err = e.response.get("error")
        logger.error(f"Error during deletion: {err}")
        post_feedback(client, channel_id, user_id, f"Error: {err}")
        return

    # Skip feedback in 1:1 DMs (channel IDs starting with 'D')
    if not channel_id.startswith("D"):
        post_feedback(client, channel_id, user_id, f"✅ Deleted {deleted} messages.")


# ─────────────────────────────────────────────────────────────────────────────
# Main: start the app in Socket Mode
# ─────────────────────────────────────────────────────────────────────────────
def main():
    handler = SocketModeHandler(app, app_token=SLACK_APP_TOKEN)
    logger.info("Starting Slack Bolt app with Socket Mode")
    handler.start()


if __name__ == "__main__":
    main()
