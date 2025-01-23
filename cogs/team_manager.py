from discord import PermissionOverwrite
from discord.ext import commands
from discord.utils import get


class Channel(commands.Cog):
    def __init__(self, client):
        self.client = client
    

    @commands.Cog.listener()
    async def on_ready(self):
        print("Channel Creator command loaded")


    @commands.command()
    async def channel(self, ctx, *, query: str):

        # list stores discord id as entered by user
        usernames = []
        # dict stores display name as key and 0 if not in csv and 1 if it does
        display_names = {}
        team_name, user_list = query.split("|", 1)

        for i in user_list.split(","):
            usernames.append(i.strip())
        
        ovewrite = {
            ctx.guild.default_role: PermissionOverwrite(read_messages=False)
        }

        for i in usernames:
            await ctx.send(f"Your entered username is {i}")
            member = get(ctx.guild.members, name = i)
            ovewrite[member] = PermissionOverwrite(read_messages=True) if member else await ctx.send(f"user {i} dosnt exist")
            
            # gets display name acc to the discord id
            fullname = ctx.author.display_name or "No nickname"
            display_names[fullname] = 0

        category = get(ctx.guild.categories, name="test")

        if category is None:
            await ctx.send("Category 'test' doesn't exist!")
            return
        

        # --> add csv checking code here <--
        # Use display_name dict and team_name variable to check


        try:
            await ctx.guild.create_text_channel("test2", category=category, overwrites = ovewrite)
            await ctx.send("Text channel created under 'test'")
        except Exception as e:
            await ctx.send(f"Failed to create text channel: {e}")

        try:
            await ctx.guild.create_voice_channel("test2", category=category, overwrites = ovewrite)
            await ctx.send("Voice channel created under 'test'")
        except Exception as e:
            await ctx.send(f"Failed to create voice channel: {e}")


async def setup(client):
    await client.add_cog(Channel(client))