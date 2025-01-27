import asyncio
from os import getenv

from discord import Intents
from discord.ext import commands
from dotenv import load_dotenv

import cogs.team_manager

exts = []


class MlscBot(commands.Bot):
    def __init__(self, command_prefix: str, intents: Intents, **kwargs):
        super().__init__(command_prefix, intents=intents, **kwargs)

    async def setup_hook(self) -> None:
        for ext in exts:
            await self.load_extension(ext)

        print("Loaded all Cogs .....")

        await self.tree.sync()

    async def on_ready(self):
        print("MLSC Bot is running ......")


def run_mongodb_server():
    import subprocess
    from pathlib import Path

    import pymongo
    import yaml

    mongod_conf_file = "./mongod.yml"
    with open(mongod_conf_file, "r") as file:
        mongod_conf = yaml.safe_load(file)

        dbpath = Path(mongod_conf["storage"]["dbPath"])
        dbpath.mkdir(parents=True, exist_ok=True)
        log_path = dbpath.joinpath("logs")
        log_path.mkdir(exist_ok=True)
        log_path.joinpath("mongod.log").touch()

        mongod_conf["systemLog"]["path"] = str(log_path.joinpath("mongod.log"))
        with open(mongod_conf_file, "w") as yaml_file:
            yaml.dump(mongod_conf, yaml_file)

    try:
        subprocess.Popen(["mongod", "--config", "./mongod.yml"])
    except KeyboardInterrupt:
        print("Shutting down MongoDB server ....")
        client = pymongo.MongoClient(
            host=mongod_conf["net"]["bindIp"], port=mongod_conf["net"]["port"]
        )
        client.admin.command("shutdown")


async def main(bot: MlscBot):
    await asyncio.create_task(asyncio.to_thread(run_mongodb_server))
    await cogs.team_manager.setup(bot)
    await bot.start(getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    bot = MlscBot(command_prefix="!", intents=Intents.all())
    load_dotenv()
    # bot.run(getenv("DISCORD_TOKEN"))
    try:
        asyncio.run(main(bot))
    except KeyboardInterrupt:
        print("Shutting down bot ....")
