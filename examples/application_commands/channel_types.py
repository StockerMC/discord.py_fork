from typing import Optional, Union
import discord

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

client = MyClient()

# setting `guild_ids` in development is better when possible because
# registering global commands has a 1 hour delay
@client.application_command
class Info(discord.SlashCommand, guild_ids=[123]):
    """Get information about the provided channel"""

    # we can also set the channel_types kwarg of application_command_option, which should be a list of channel types

    text_channel: Optional[discord.TextChannel] = discord.application_command_option(description='A text channel')
    voice_channel: Optional[discord.VoiceChannel] = discord.application_command_option(description='A voice channel')
    # we could also add `None` to the `Union` or change it to `Optional[Union[...]]` instead of setting required to False
    thread_or_stage: Union[
        discord.Thread, discord.StageChannel
    ] = discord.application_command_option(description='A voice channel', required=False)
    any_channel: Optional[discord.abc.GuildChannel] = discord.application_command_option(description='Any type of channel')

    async def callback(self, response: discord.SlashCommandResponse):
        if not response.options:
            await response.send_message("You didn't provide any channels!", ephemeral=True)
            return

        embeds = []
        for option_name, channel in response.options:
            if channel is None:
                continue

            embed = discord.Embed(title=option_name.replace('_', ' ').title())
            embed.add_field(name=channel.name, value=f'ID: {channel.id}')
            embeds.append(embed)

        msg = f'Info about {len(response.options)} channels:'
        await response.send_message(msg, embeds=embeds, ephemeral=True)

client.run('token')
