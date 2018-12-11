import discord
import requests
import os
from discord.ext import commands
from PIL import Image
from io import BytesIO
from utils import get_imgs
import config

Client = discord.Client()
client = commands.Bot(command_prefix="q!")

images = {}


@client.async_event
async def on_ready():
    print("Logged on as {}".format(client.user))
    game = discord.Game(name="\'q!hathelp\' for info!")
    await client.change_presence(game=game)


@client.async_event
async def on_message_delete(message):
    """
    If the message deleted is within the dictionaries, pop that key respectively
    in order to clear cache.
    :param message: Message that was deleted
    """
    if message.channel in images:
        images.pop(message.channel)


@client.command(pass_context=True)
async def hathelp(ctx):
    string = "To use: **q!hat**\n" \
             "\n" \
             "You can customize your hat with commands such as 'q!hat left=20 up=50'\n" \
             "Note: specifying no arguments results in default values.\n" \
             "\n" \
             "List of arguments (commands use the format **command=number**):\n" \
             "\t type  \n" \
             "flip  \n" \
             "scale \n" \
             "direction (i.e. left, right, up, down)\n" \

    embed = discord.Embed()
    embed.add_field(name="CrimmisHatBot Usage!", value=string)
    await client.send_message(ctx.message.channel, embed=embed)


def check_hat(args):
    """
    Helper function that checks puthat arguments for specific flags
    Checks flipping the image horizontally and scaling by a factor
    Opens the hat file, manipulates it, and returns it
    :param args: Arguments to parse
    :return: Manipulated hat file
    """
    folder = get_imgs("crimmis_hats/")
    hat = Image.open(folder.get('0'))
    for arg in args:
        if arg.startswith('type='):
            value = arg.split('=')[1]
            hat = Image.open(folder.get(value))

    w_offset, h_offset = 150, 0
    hat_width, hat_height = 350, 300
    for arg in args:
        if arg == 'flip':
            hat = hat.transpose(Image.FLIP_LEFT_RIGHT)
            w_offset, h_offset = 0, 0
        if arg.startswith('scale='):
            value = float(arg.split('=')[1])
            hat_width, hat_height = int(hat.width * value), int(hat.height * value)

    hat = hat.resize((hat_width, hat_height))
    return hat, w_offset, h_offset


def move(args, width, height):
    for arg in args:
        if arg.startswith('left='):
            value = arg.split('=')[1]
            width -= int(value)
        if arg.startswith('right='):
            value = arg.split('=')[1]
            width += int(value)
        if arg.startswith('up='):
            value = arg.split('=')[1]
            height -= int(value)
        if arg.startswith('down='):
            value = arg.split('=')[1]
            height += int(value)
    return width, height


@client.command(pass_context=True)
async def hat(ctx, *args):
    message = ctx.message
    url = message.author.avatar_url
    response = requests.get(url, headers={'User-agent': 'Mozilla/5.0'})

    image = Image.open(BytesIO(response.content)).resize((500, 500))
    hat, width, height = check_hat(args)

    image.paste(hat, move(args, width, height), mask=hat)
    image.save("crimmis_hats/remade.png")

    if message.channel in images:
        await client.delete_message(images.get(message.channel))

    image = await client.send_file(message.channel, "crimmis_hats/remade.png", filename="newhat.png", content="Hat: ")
    images[message.channel] = image
    os.remove("crimmis_hats/remade.png")


client.run(config.BOT_TOKEN)
