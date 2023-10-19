import time
import discord
import requests
import numpy as np

from PIL import Image
from io import BytesIO
from bot_token import TOKEN
from discord import app_commands

# Define Discord intents and client
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


class Buttons(discord.ui.View):
    def __init__(self, user_name, user_id, image, base_hat, hat_type="0", *, timeout=360):
        super().__init__(timeout=timeout)

        # Holds the actual objects of the image and hat
        self.image = image
        self.hat = base_hat

        # More static variables to track
        self.original_user_name = user_name
        self.original_user_id = user_id
        self.hat_type = hat_type
        self.flip = False

        # Image/Hat parameters for placement
        self.vertical_px = 0
        self.horizontal_px = 150
        self.hat_scale = 1.0
        self.hat_rotation = 0
        print(f"[{time.ctime():25}] New view setup for {user_name}.")

    async def send_hat(self, interaction, new_hat):
        """
        Handles sending the hat for the various modification commands.
        Since we don't want to save the file locally and only use the PIL file, this requires a BytesIO object
        to hold the PIL image in its binary state, from which we save and seek it.
        :param interaction:
        :param new_hat:
        :return:
        """
        with BytesIO() as image_binary:
            new_hat.save(image_binary, 'PNG')
            image_binary.seek(0)
            await interaction.message.delete()
            await interaction.response.send_message(
                content=self.return_string(),
                file=discord.File(image_binary, filename='image.png'),
                view=self
            )

    def return_string(self):
        return f"**Parameters**:\n" \
               f"- X Location: {self.horizontal_px}\n" \
               f"- Y Location: {self.vertical_px}\n" \
               f"- Flipped: {self.flip}\n" \
               f"- Scale: {np.round(self.hat_scale, 2)}x\n" \
               f"- Rotation: {self.hat_rotation}°\n"

    def reapply_hat(self):
        """
        Utility function that handles the application on a fresh image copy with the given user parameters
        :return image_name: local filename of the generated image
        :return file: Discord File object to attach to the response
        """
        # Get copy of base image
        image = self.image.copy()

        # Rescale hat
        modified_hat = self.hat.copy()
        hat_width, hat_height = int(modified_hat.width * self.hat_scale), int(modified_hat.height * self.hat_scale)
        modified_hat = modified_hat.resize((hat_width, hat_height))

        # Rotate the hat
        if self.hat_rotation != 0:
            modified_hat = modified_hat.rotate(self.hat_rotation, expand=1)

        # Apply move given and temporarily save hat
        image.paste(modified_hat, (self.horizontal_px, self.vertical_px), mask=modified_hat)
        return image

    async def modify_placement(self, interaction: discord.Interaction, horizontal_mod: int = 0, vertical_mod: int = 0):
        """
        Utility function to handle the movement commands as well as sending the finish product back
        :param interaction: Discord.py Interaction, holding useful state
        :param horizontal_mod: How much to adjust the x-axis by in terms of raw pixels
        :param vertical_mod: How much to adjust the y-axis by in terms of raw pixels
        """
        # Check if the proper user
        if interaction.user.id != self.original_user_id:
            await interaction.response.send_message(content="Not the original user!", delete_after=5.0)
            return

        # Shift over horizontal by given pixels
        self.horizontal_px += horizontal_mod
        self.vertical_px += vertical_mod

        # Reapply the hat and send it
        await self.send_hat(interaction, self.reapply_hat())

    async def modify_scale(self, interaction: discord.Interaction, scale_modifier: float = 0.05):
        """
        Utility function to handle the hat scale commands as well as sending the finish product back
        :param interaction: Discord.py Interaction, holding useful state
        :param scale_modifier: How much to modify the scale by in terms of %, e.g. 5% smaller
        """
        # Check if the proper user
        if interaction.user.id != self.original_user_id:
            await interaction.response.send_message(content="Not the original user!", delete_after=5.0)
            return

        # Check if scale would go negative here
        if self.hat_scale + scale_modifier <= 0:
            await interaction.response.send_message(content="Hat Scale has to be above 0!", delete_after=5.0)
            return

        # Update hat scale
        self.hat_scale += scale_modifier

        # Reapply the hat and send it
        await self.send_hat(interaction, self.reapply_hat())

    async def modify_rotation(self, interaction: discord.Interaction, rotation_modifier: int = 30):
        """
        Utility function to handle the hat rotation commands as well as sending the finish product back
        :param interaction: Discord.py Interaction, holding useful state
        :param rotation_modifier: How much to rotate the image by, in terms of degrees
        """
        # Check if the proper user
        if interaction.user.id != self.original_user_id:
            await interaction.response.send_message(content="Not the original user!", delete_after=5.0)
            return

        # Update hat scale
        self.hat_rotation += rotation_modifier

        # Reapply the hat and send it
        await self.send_hat(interaction, self.reapply_hat())

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
        # Check if the proper user
        if interaction.user.id != self.original_user_id:
            await interaction.response.send_message(content="Not the original user!", delete_after=5.0)
            return

        # Flip the boolean
        self.flip = True if self.flip is False else False

        # Flip the hat and get the new image
        self.hat = self.hat.transpose(Image.FLIP_LEFT_RIGHT)

        # Reapply the hat and send it
        await self.send_hat(interaction, self.reapply_hat())

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
        await interaction.response.send_message(content="Currently Feedback sending is not implemented, but thanks for the thought!", delete_after=5.0)

    @discord.ui.button(label="Scale Up 25%", style=discord.ButtonStyle.gray, emoji="🔎")
    async def scale_up_quarter(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.modify_scale(interaction, scale_modifier=0.25)

    @discord.ui.button(label="Scale Up 5%", style=discord.ButtonStyle.gray, emoji="🔎")
    async def scale_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.modify_scale(interaction, scale_modifier=0.05)

    @discord.ui.button(label="Scale Down 5%", style=discord.ButtonStyle.gray, emoji="🔎")
    async def scale_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.modify_scale(interaction, scale_modifier=-0.05)

    @discord.ui.button(label="Scale Down 25%", style=discord.ButtonStyle.gray, emoji="🔎")
    async def scale_down_quarter(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.modify_scale(interaction, scale_modifier=-0.25)

    @discord.ui.button(label="Github", style=discord.ButtonStyle.gray, emoji="🔗")
    async def github_link(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(content="Source code is available at: https://github.com/qu-gg/CrimmisHatBot", delete_after=10.0)

    @discord.ui.button(label="Rotate 30°", style=discord.ButtonStyle.gray, emoji="↪")
    async def rotate_thirty_ccw(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.modify_rotation(interaction, rotation_modifier=30)

    @discord.ui.button(label="Rotate 1°", style=discord.ButtonStyle.gray, emoji="↪")
    async def rotate_one_ccw(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.modify_rotation(interaction, rotation_modifier=1)

    @discord.ui.button(label="Rotate 1°", style=discord.ButtonStyle.gray, emoji="↩")
    async def rotate_one_cw(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.modify_rotation(interaction, rotation_modifier=-1)

    @discord.ui.button(label="Rotate 30°", style=discord.ButtonStyle.gray, emoji="↩")
    async def rotate_thirty_cw(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.modify_rotation(interaction, rotation_modifier=-30)

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.gray, emoji="❌")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if the proper user
        if interaction.user.id != self.original_user_id:
            await interaction.response.send_message(content="Not the original user!", delete_after=5.0)
            return

        await interaction.message.delete()


@tree.command(name="hat", description="Interactive command place a hat on your avatar and adjust it as needed! Hat Types are 0-4.")
@app_commands.choices(hattype=[
        app_commands.Choice(name="Crimmis - 0", value="0"),
        app_commands.Choice(name="Crimmis - 1", value="1"),
        app_commands.Choice(name="Crimmis - 2", value="2"),
        app_commands.Choice(name="Crimmis - 3", value="3"),
        app_commands.Choice(name="Crimmis - 4", value="4"),
        app_commands.Choice(name="Halloween - Pumpkin", value="pumpkin"),
        app_commands.Choice(name="Halloween - Witch Hat", value="witch_hat"),
        app_commands.Choice(name="Halloween - Jason Mask", value="jason_mask"),
        app_commands.Choice(name="Halloween - Freddy Sweater", value="freddy_sweater")
    ])
async def hat(interaction, hattype: app_commands.Choice[str], url: str=""):
    """
    Hat Discord command, handles the initial interaction with a user in terms of returning a
    first-try hat placement and setting up the User's class
    :param interaction: Discord.py Interaction, holding useful state
    :param hattype: Which of the available hats to use, currently set in the initial command
    :param url: Allows user to input an image url rather than using their avatar
    """
    # Local log
    print(f"[{time.ctime():25}] Making hat for {interaction.user.name} in {interaction.guild.name} with hattype {hattype.name}.")

    # Get hat.value from Choice
    hattype = hattype.value

    # Get the user's avatar and download image
    avatar_url = interaction.user.avatar.url
    if url != "":
        avatar_url = url

    # Get the image via a html request
    try:
        response = requests.get(avatar_url, headers={'User-agent': 'Mozilla/5.0'})
        image = Image.open(BytesIO(response.content)).resize((500, 500))
    except Exception as e:
        await interaction.response.send_message(content=f"Invalid URL for {avatar_url}!", delete_after=5.0)
        return

    # Get the type of hat
    base_hat = Image.open(f"crimmis_hats/{hattype}.png")

    # Get the starter hat placement
    starter_image = image.copy()
    starter_image.paste(base_hat, (150, 0), mask=base_hat)

    # Build the view and send the message
    view = Buttons(interaction.user.name, interaction.user.id, image, base_hat, hattype)
    with BytesIO() as image_binary:
        starter_image.save(image_binary, 'PNG')
        image_binary.seek(0)
        await interaction.response.send_message(
            content=f"Here is your hat, {str(interaction.user.name.title())}!\n{view.return_string()}",
            file=discord.File(image_binary, filename='image.png'),
            view=view
        )


@tree.command(name="displayhats", description="Displays available hats and their IDs!")
async def display_hat(interaction):
    file = discord.File("crimmis_hats/hats.png")
    await interaction.response.send_message(content="Available Hats!", file=file)


@client.event
async def on_ready():
    await tree.sync()
    print(f"[{time.ctime():25}] Ready!")


# Run the bot
client.run(TOKEN)
