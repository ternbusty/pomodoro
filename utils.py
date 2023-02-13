import requests
import json
import config


class Utils:
    def __init__(self) -> None:
        pass

    def format_date(self, datetime) -> str:
        return datetime.strftime("%Y-%m-%d %H:%M")

    def convert_timedelta_to_str(self, timedelta):
        hours, remainder = divmod(timedelta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return '{:02}:{:02}'.format(int(hours), int(minutes))

    def call_me(self):
        url = config.TELEGRAM_URL
        requests.get(url)

    def send_to_discord(self, message):
        webhook_url = config.DISCORD_WEBHOOK_URL
        main_content = {'content': message}
        headers = {'Content-Type': 'application/json'}
        requests.post(webhook_url, json.dumps(main_content), headers=headers)


if __name__ == "__main__":
    utils = Utils()
    utils.call_me()
