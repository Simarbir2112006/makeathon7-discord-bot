import csv
import datetime
import re
from dataclasses import dataclass

import discord
import discord.ext
import pymongo
from discord import Member, PermissionOverwrite
from discord.ext import commands
from discord.role import Role
from rapidfuzz import fuzz


class Channel(commands.Cog):
    def __init__(self, client) -> None:
        self.client = client
        self.global_category = "test"  # "team channel creator"
        self.csv_file = "./Makeathon6.csv"

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        print("[INFO] Channel Creator command loaded")

    def channel_help(self) -> str:
        return (
            f"**Description**: Creates a text and voice channel under the {self.global_category} category"
            "\n"
            "**Usage**: !channel <team name> | <username1>, <username2>, ..."
            "\n"
            "**Note**: Do not include the '<' and '>' symbols"
        )

    def channel_creation_failed(self) -> str:
        return "Failed to create respective team channels. Kindly retry again..."

    @commands.command()
    async def channel(self, ctx: commands.Context, *, query: str) -> None:
        query = query.strip()

        # help command
        if query == "help":
            await ctx.send(self.channel_help())
            return

        try:
            team_name, user_list = query.split("|", 1)
            team_name = re.sub(" +", " ", team_name).strip()
            channel_team_name = team_name.strip().replace(" ", "-").lower()
            usernames = [name.strip() for name in user_list.split(",")]
        except ValueError:
            await ctx.send("Error: Invalid input format.")
            await ctx.send("Try [`!channel help`] for more information.")
            return

        if ctx.guild is None:
            await ctx.send("DevError: Guild not found.")
            await ctx.send(self.channel_creation_failed())
            return

        team_role = discord.utils.get(ctx.guild.roles, name=f"Team {team_name}")
        if team_role:
            await ctx.send(
                f"**Team {team_name}** already created their respective text & audio channels. For help, contact our support team."
            )
            return

        # default role permission for rest of the members
        overwrite: dict[Role | Member, PermissionOverwrite] = {
            ctx.guild.default_role: PermissionOverwrite(read_messages=False)
        }

        # Flag to assume that all users are matched from the csv
        user_match = True
        # List of members to be added to the channel
        user_members: list[Member] = []

        for username in usernames:
            await ctx.send(f"Your entered username is {username}.")
            if member := discord.utils.get(ctx.guild.members, name=username):
                user_members.append(member)
                overwrite[member] = PermissionOverwrite(read_messages=True)
            else:
                await ctx.send(f"Error: user {username} doesn't exist")
                await ctx.send(self.channel_creation_failed())
                return

            # gets display name corresponding to the discord id
            fullname = member.display_name or ""
            if not (user_status := self.csv_check_user(fullname, team_name)):
                user_match = False
                if user_status is None:
                    await ctx.send(
                        f"User: **{username}** is already registered for the event but did not RSVP. You are not allowed to create channels for this user."
                    )
                    break

                await ctx.send(
                    f"User: **{username} ({fullname})** does not match any user in the list of participants."
                )
                break

        if not user_match:
            await ctx.send(self.channel_creation_failed())
            await ctx.send("Try [`!channel help`] for more information.")
            return

        category = discord.utils.get(ctx.guild.categories, name=self.global_category)
        if category is None:
            await ctx.send(f"Error: Category {self.global_category} doesn't exist!")
            await ctx.send(self.channel_creation_failed())
            return

        # [text_channel, voice_channel]
        created_channel: list[discord.TextChannel | discord.VoiceChannel | None] = [
            None,
            None,
        ]
        try:
            created_channel[0] = await ctx.guild.create_text_channel(
                channel_team_name, category=category, overwrites=overwrite
            )
            await ctx.send(
                f"[**{channel_team_name}**] Text channel created under {self.global_category}"
            )
        except discord.Forbidden:
            await ctx.send(
                "I do not have the proper permissions to create this text channel."
            )
            return
        except discord.HTTPException:
            await ctx.send(
                "Error: HTTP request operation failed to create this text channel."
            )
            return
        except Exception as e:
            await ctx.send(f"Error: failed to create text channel: {e}")
            return

        try:
            created_channel[1] = await ctx.guild.create_voice_channel(
                channel_team_name, category=category, overwrites=overwrite
            )
            await ctx.send(
                f"[**{channel_team_name}**] Voice channel created under {self.global_category}"
            )
        except discord.Forbidden:
            await ctx.send(
                "I do not have the proper permissions to create this voice channel."
            )
            return
        except discord.HTTPException as e:
            await ctx.send(
                f"Error: HTTP request operation failed to create this voice channel. {e}"
            )
            return
        except Exception as e:
            await ctx.send(f"Error: failed to create voice channel: {e}")
            return

        if all(created_channel):
            role_name = f"Team {team_name}"
            role = discord.utils.get(ctx.guild.roles, name=role_name)
            if role is None:
                try:
                    role = await ctx.guild.create_role(name=role_name, mentionable=True)
                except discord.Forbidden:
                    await ctx.send(
                        "I do not have the proper permissions to create this role."
                    )
                    return
                except discord.HTTPException as e:
                    await ctx.send(
                        f"Error: HTTP request operation failed to create this role. {e}"
                    )
                    return
                except Exception as e:
                    await ctx.send(f"Error: failed to create role: {e}")
                    return
            for member in user_members:
                await member.add_roles(role)
            await ctx.send(f"**{role_name}** role assigned to the members.")

            mg_client = pymongo.MongoClient("localhost", 27017)
            mg_db = mg_client["mlsc"]
            mg_collection = mg_db["team_channel"]
            mg_document = {
                "user": ctx.author.name,
                "text_channel_id": created_channel[0].id,
                "voice_channel_id": created_channel[1].id,
                "date": int(
                    datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
                ),
            }
            mg_collection.insert_one(mg_document)

    def csv_check_user(self, fullname: str, teamname: str) -> bool | None:
        found = False
        with open(self.csv_file, mode="r") as file:
            csv_file = csv.reader(file)
            for line in csv_file:
                csv_user = Participant(
                    firstname=line[0], lastname=line[1], teamname=line[5], stage=line[7]
                )
                if (
                    fuzz.partial_token_sort_ratio(fullname, csv_user.fullname) > 65
                    and fuzz.partial_token_sort_ratio(teamname, csv_user.teamname) > 85
                ):
                    if csv_user.stage == "rsvp":
                        found = None
                        break

                    found = True
                    break
        return found


@dataclass
class Participant:
    firstname: str
    lastname: str
    teamname: str
    stage: str

    @property
    def fullname(self) -> str:
        return f"{self.firstname} {self.lastname}"


async def setup(client) -> None:
    await client.add_cog(Channel(client))
