import os
import discord
import requests
import numpy as np

from PIL import Image
from io import BytesIO
from utils import get_imgs
from bot_token import TOKEN
from discord import app_commands

# Define Discord intents and client
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


class Buttons(discord.ui.View):
    def __init__(self, user_name, user_id, image, hat, hat_type=0, *, timeout=360):
        super().__init__(timeout=timeout)

        # Holds the actual objects of the image and hat
        self.image = image
        self.hat = hat

        # More static variables to track
        self.original_user_name = user_name
        self.original_user_id = user_id
        self.hat_type = hat_type
        self.flip = False

        # Image/Hat parameters for placement
        self.vertical_px = 0
        self.horizontal_px = 150
        self.hat_scale = 1.0
        print(f"New view setup for {user_name}.")

    def return_string(self):
        return f"Horizontal: {self.horizontal_px} " \
               f"Vertical: {self.vertical_px} " \
               f"Flipped: {self.flip} " \
               f"Scale: {np.round(self.hat_scale, 2)}"

    def reapply_hat(self):
        """
        Utility function that handles the application on a fresh image copy with the given user parameters
        :return image_name: local filename of the generated image
        :return file: Discord File object to attach to the response
        """
        # Get copy of base image
        image = self.image.copy()

        # Rescale hat
        hat = self.hat.copy()
        hat_width, hat_height = int(hat.width * self.hat_scale), int(hat.height * self.hat_scale)
        hat = hat.resize((hat_width, hat_height))

        # Apply move given and temporarily save hat
        image.paste(hat, (self.horizontal_px, self.vertical_px), mask=hat)
        image_name = ''.join(str(np.random.randint(0, 10000000)))
        image.save(f"crimmis_hats/createdhats/{image_name}.png")

        # Get the file as a Discord File and return
        file = discord.File(f"crimmis_hats/createdhats/{image_name}.png")
        return image_name, file

    async def modify_placement(self, interaction: discord.Interaction, horizontal_mod: int = 0, vertical_mod: int = 0):
        """
        Utility function to handle the movement commands as well as sending the finish product back
        :param interaction: Discord.py Interaction, holding useful state
        :param horizontal_mod: How much to adjust the x-axis by in terms of raw pixels
        :param vertical_mod: How much to adjust the y-axis by in terms of raw pixels
        """
        # Check if the proper user
        if interaction.user.id != self.original_user_id:
            await interaction.response.send_message(content="Not the original user!", delete_after=10.0)
            return

        # Shift over horizontal by given pixels
        self.horizontal_px += horizontal_mod
        self.vertical_px += vertical_mod

        # Get new hat
        file_name, new_hat = self.reapply_hat()

        # Edit original message for successful interaction
        await interaction.message.delete()
        await interaction.response.send_message(content="", file=new_hat, view=self)

    async def modify_scale(self, interaction: discord.Interaction, scale_modifier: float = 0.05):
        """
        Utility function to handle the hat scale commands as well as sending the finish product back
        :param interaction: Discord.py Interaction, holding useful state
        :param scale_modifier: How much to modify the scale by in terms of %, e.g. 5% smaller
        """
        # Update hat scale
        self.hat_scale += scale_modifier

        # Get new hat
        file_name, new_hat = self.reapply_hat()

        # Edit original message for successful interaction
        await interaction.message.delete()
        await interaction.response.send_message(content="", file=new_hat, view=self)

    @discord.ui.button(label="20px Left", style=discord.ButtonStyle.gray, emoji="⏪")
    async def twentypx_left(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.modify_placement(interaction, horizontal_mod=-20)

    @discord.ui.button(label="1px Left", style=discord.ButtonStyle.gray, emoji="◀")
    async def onepx_left(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.modify_placement(interaction, horizontal_mod=-1)

    @discord.ui.button(label="1px Right", style=discord.ButtonStyle.gray, emoji="▶")
    async def onepx_right(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.modify_placement(interaction, horizontal_mod=1)

    @discord.ui.button(label="20px Right", style=discord.ButtonStyle.gray, emoji="⏩")
    async def twentypx_right(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.modify_placement(interaction, horizontal_mod=20)

    @discord.ui.button(label="Flip Hat", style=discord.ButtonStyle.gray, emoji="🐬")
    async def flip(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Flip the boolean
        self.flip = True if self.flip is False else False

        # Flip the hat and get the new image
        self.hat = self.hat.transpose(Image.FLIP_LEFT_RIGHT)
        file_name, new_hat = self.reapply_hat()

        # Edit original message for successful interaction
        await interaction.message.delete()
        await interaction.response.send_message(content="", file=new_hat, view=self)

    @discord.ui.button(label="20px Up‏‏‎ ‎‏‏‎ ‎", style=discord.ButtonStyle.gray, emoji="⏫")
    async def twentypx_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.modify_placement(interaction, vertical_mod=-20)

    @discord.ui.button(label="1px Up‏‏‎ ‎‏‏‎ ‎", style=discord.ButtonStyle.gray, emoji="🔼")
    async def onepx_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.modify_placement(interaction, vertical_mod=-1)

    @discord.ui.button(label="1px Down", style=discord.ButtonStyle.gray, emoji="🔽")
    async def onepx_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.modify_placement(interaction, vertical_mod=1)

    @discord.ui.button(label="20px Down", style=discord.ButtonStyle.gray, emoji="⏬")
    async def twentypx_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.modify_placement(interaction, vertical_mod=20)

    @discord.ui.button(label="Feedback", style=discord.ButtonStyle.gray, emoji="📝")
    async def feedback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(content="Currently not implemented, but thanks for the thought!", delete_after=5.0)

    @discord.ui.button(label="Scale Up 25%", style=discord.ButtonStyle.gray, emoji="🔎")
    async def scale_up_quarter(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.modify_scale(interaction, scale_modifier=0.25)

    @discord.ui.button(label="Scale Down 25%", style=discord.ButtonStyle.gray, emoji="🔎")
    async def scale_down_quarter(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.modify_scale(interaction, scale_modifier=-0.25)

    @discord.ui.button(label="Scale Up 5%", style=discord.ButtonStyle.gray, emoji="🔎")
    async def scale_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.modify_scale(interaction, scale_modifier=0.05)

    @discord.ui.button(label="Scale Down 5%", style=discord.ButtonStyle.gray, emoji="🔎")
    async def scale_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.modify_scale(interaction, scale_modifier=-0.05)


@tree.command(name="hat", description="Interactive command place a hat on your avatar and adjust it as needed!")
async def hat(interaction, hattype: int = 0):
    """
    Hat Discord command, handles the initial interaction with a user in terms of returning a
    first-try hat placement and setting up the User's class
    :param interaction: Discord.py Interaction, holding useful state
    :param hattype: Which of the available hats to use, currently set in the initial command
    """
    # Get the user's avatar and download image
    avatar_url = interaction.user.avatar.url

    # Get the image via an html request
    response = requests.get(avatar_url, headers={'User-agent': 'Mozilla/5.0'})
    image = Image.open(BytesIO(response.content)).resize((500, 500))

    # Get the type of hat
    folder = get_imgs("crimmis_hats/")
    hat = Image.open(folder.get(str(hattype)))

    # Apply move given and temporarily save hat
    starter_image = image.copy()
    starter_image.paste(hat, (150, 0), mask=hat)
    im_name = ''.join(str(np.random.randint(0, 10000000)))
    starter_image.save("crimmis_hats/createdhats/{}.png".format(im_name))

    # Get the Discord File object and the Buttons View
    file = discord.File("crimmis_hats/createdhats/{}.png".format(im_name))
    view = Buttons(interaction.user.name, interaction.user.id, image, hat, hattype)
    view.add_item(discord.ui.Button(label="Github", style=discord.ButtonStyle.link, url="https://github.com/qu-gg/CrimmisHatBot"))
    await interaction.response.send_message(content=f"Here is your hat, {str(interaction.user)}!", file=file, view=view)


@tree.command(name="displayhats", description="Displays available hats and their IDs!")
async def display_hat(interaction):
    file = discord.File("crimmis_hats/hats.png")
    await interaction.response.send_message(content="Available Hats!", file=file)


@client.event
async def on_ready():
    await tree.sync()
    print("Ready!")


# If created_hats folder doesn't exist, create it
if not os.path.exists("crimmis_hats/createdhats/"):
    os.mkdir("crimmis_hats/createdhats/")

# Run the bot
client.run(TOKEN)
