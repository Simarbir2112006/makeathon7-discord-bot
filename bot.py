import asyncio
from os import getenv

from discord import Intents
from discord.ext import commands
from dotenv import load_dotenv

import cogs.team_manager
from db.mongo import MongoDB

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


async def main(bot: MlscBot):
    mdb = MongoDB("./mongod.yml")
    asyncio.create_task(asyncio.to_thread(mdb.run_daemon))
    await cogs.team_manager.setup(bot, mdb)
    if discord_token := getenv("DISCORD_TOKEN"):
        await bot.start(discord_token)
    else:
        raise ValueError("Did not find DISCORD_TOKEN environment variable!")


if __name__ == "__main__":
    bot = MlscBot(command_prefix="!", intents=Intents.all())
    load_dotenv()
    try:
        asyncio.run(main(bot))
    except KeyboardInterrupt:
        print("Shutting down bot ....")
