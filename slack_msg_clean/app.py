import os
import time
import datetime
import logging
import sys
from slack_bolt import App
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_bolt.adapter.socket_mode import SocketModeHandler

# logging configuration: stdout
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# environment variables
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_USER_TOKEN = os.environ.get("SLACK_USER_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")

# Bolt app & WebClient initialization
app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)
user_client = WebClient(token=SLACK_USER_TOKEN)


@app.command("/delete_msg")
def delete_my_messages(ack, body, client):
    ack()
    user_id = body.get("user_id")
    channel_id = body.get("channel_id")
    logger.info(f"Request from {user_id} in {channel_id}")

    deleted = 0
    cursor = None
    try:
        while True:
            resp = user_client.conversations_history(
                channel=channel_id, cursor=cursor, limit=200
            )
            for msg in resp.get("messages", []):
                if msg.get("user") != user_id:
                    continue
                ts = msg.get("ts")
                while True:
                    try:
                        user_client.chat_delete(channel=channel_id, ts=ts)
                        deleted += 1
                        logger.info(f"Deleted ts={human_ts(ts)}")

                        break
                    except SlackApiError as e:
                        if e.response.get("error") == "ratelimited":
                            retry = int(e.response.headers.get("Retry-After", 1))
                            time.sleep(retry)
                            continue
                        else:
                            logger.error(e.response.get("error"))
                            break
                time.sleep(0.1)
            if not resp.get("has_more"):
                break
            cursor = resp.get("response_metadata", {}).get("next_cursor")
        logger.info(f"Total deleted={deleted}")
    except SlackApiError as e:
        logger.error(e.response.get("error"))
        post_feedback(client, channel_id, user_id, f"Error: {e.response.get('error')}")
        return
    if not channel_id.startswith("D"):
        post_feedback(client, channel_id, user_id, f"Deleted {deleted} messages.")


def post_feedback(client, channel, user, text):
    try:
        client.chat_postEphemeral(channel=channel, user=user, text=text)
    except SlackApiError as e:
        if e.response.get("error") == "channel_not_found":
            client.chat_postMessage(channel=channel, text=text)


def human_ts(ts_str: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    ts_float = float(ts_str)
    # Use .fromtimestamp for local time, or .utcfromtimestamp for UTC
    dt = datetime.datetime.fromtimestamp(ts_float)
    return dt.strftime(fmt)


def main():
    handler = SocketModeHandler(app, app_token=SLACK_APP_TOKEN)
    logger.info("Starting app with Socket Mode")
    handler.start()


if __name__ == "__main__":
    main()
