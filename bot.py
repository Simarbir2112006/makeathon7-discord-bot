from discord import Intents
from dotenv import load_dotenv
from discord.ext import commands
from os import getenv
import asyncio
import cogs.team_manager

exts =  []

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
    await cogs.team_manager.setup(bot)
    await bot.start(getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    bot = MlscBot(command_prefix="!", intents=Intents.all())
    load_dotenv()
    # bot.run(getenv("DISCORD_TOKEN"))
    asyncio.run(main(bot))