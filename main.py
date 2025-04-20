import json, iso8601, requests, asyncio
from datetime import datetime
from discord_webhook import DiscordWebhook, DiscordEmbed

class RobloxChecker:
    def __init__(self):
        with open("config.json", "r") as config_file:
            self.config = json.load(config_file)

    async def send_webhook(self, webhook_url, embed, game_id, unix_timestamp):
        webhook = DiscordWebhook(webhook_url, content=f"<@&{self.config['role_ping']}>")
        webhook.add_embed(embed)
        embed.set_timestamp()
        webhook.execute()

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] | Message Sent...")

        with open("database.json", 'r') as json_file:
            data = json.load(json_file)

        data[str(game_id)] = unix_timestamp

        with open("database.json", 'w') as json_file:
            json.dump(data, json_file, indent=2)

    async def check_game(self):
        config = self.config
        try:
            for game_id in config["game_ids"]:
                eco_url = f"https://economy.roblox.com/v2/assets/{game_id}/details"
                eco_response = requests.get(eco_url)

                if eco_response.status_code != 200:
                    continue

                eco_data = eco_response.json()
                asset_name = eco_data.get("Name")
                creator = eco_data.get("Creator", {}).get("Name", "Unknown")
                update_time = eco_data.get("Updated")

                if not update_time:
                    continue

                dt_object = iso8601.parse_date(update_time)
                unix_timestamp = int(dt_object.timestamp())

                with open("database.json", 'r') as json_file:
                    data = json.load(json_file)

                if str(game_id) in data and data[str(game_id)] == unix_timestamp:
                    continue

                embed = DiscordEmbed(
                    title=f"(UPDATED) {asset_name}",
                    description=f"**Owner**: {creator}\n"
                                f"**Last Updated**: {f'<t:{data.get(str(game_id), 0)}>' if str(game_id) in data else '*No previous record*'}\n"
                                f"**Time Updated**: <t:{unix_timestamp}> (<t:{unix_timestamp}:R>)\n"
                                f"**Game Link**: https://www.roblox.com/games/{game_id}"
                )

                thumbnail_response = requests.get(f"https://thumbnails.roblox.com/v1/places/gameicons?placeIds={game_id}&returnPolicy=PlaceHolder&size=128x128&format=Png&isCircular=false")

                if thumbnail_response.status_code == 200:
                    thumbnail_data = thumbnail_response.json()
                    thumbnail = thumbnail_data["data"][0]["imageUrl"]
                    embed.set_thumbnail(url=thumbnail)

                await self.send_webhook(config["webhook"], embed, game_id, unix_timestamp)

        except Exception as e:
            print(e)

    async def main(self):
        print(r"""
        ____                            __        __         _       _             
        / ___| __ _ _ __ ___   ___ _ __  \ \      / /__  _ __| | ____| | ___   __ _ 
        | |  _ / _` | '_ ` _ \ / _ \ '__|  \ \ /\ / / _ \| '__| |/ / _` |/ _ \ / _` |
        | |_| | (_| | | | | | |  __/ |      \ V  V / (_) | |  |   < (_| | (_) | (_| |
        \____|\__,_|_| |_| |_|\___|_|       \_/\_/ \___/|_|  |_|\_\__,_|\___/ \__, |
                                                                                |___/ 
        """)
        print("> Roblox Watcher Started.")
        while True:
            await self.check_game()
            await asyncio.sleep(self.config['watch_speed'])

checker = RobloxChecker()
asyncio.run(checker.main())