import discord
import requests
import os
from discord.ext import commands
from PIL import Image
from io import BytesIO
from utils import get_imgs

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
    string = "Usage q!hat -argument1 -argument2:\n\n" \
             " \t -type=NUM [selects which hat to use]\n" \
             " \t -flip [flips hat horizontally]\n" \
             " \t -scaled=NUM [resizes hat by a factor of NUMBER]\n" \
             " \t -w=NUM [shifts hat horizontally by NUM px]\n" \
             " \t -h=NUM [shifts hat vertically by NUM px]\n\n" \
             "*Note: specifying no arguments results in default values.*"
    await client.send_message(ctx.message.channel, content=string)


def check_hat(args, image):
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
        if arg.startswith('-type='):
            value = arg.split('=')[1]
            hat = Image.open(folder.get(value))

    # Resizing image to appropriate size
    image_w, image_h = image.size
    hat.resize((int(image_w * 0.5), int(image_w * 0.5)))

    for arg in args:
        if arg == '-flip':
            hat = hat.transpose(Image.FLIP_LEFT_RIGHT)
        if arg.startswith('-scaled='):
            value = float(arg.split('=')[1])
            w, h = hat.size
            w_scaled, h_scaled = (int(w * value), int(h * value))
            hat = hat.resize((w_scaled, h_scaled))
    return hat


def check_dim(args, image_h, image_w, hat_w):
    """
    Helper function to shift the x/y coords of the hat, as well as setting default values
    :param args: Arguments to parse
    :param image_h: Height of the image
    :param image_w: Width of the image
    :param hat_w: Width of the hat
    :return: Tuple with manipulated coordinates
    """
    width = int((image_w - hat_w) * 0.75)
    height = int(image_h - (.9 * image_h))
    for arg in args:
        if arg.startswith('-w='):
            value = int(arg.split('=')[1])
            width = ((image_w - hat_w) // 2) + value
        if arg.startswith('-h='):
            height = int(arg.split('=')[1])

    return width, height


@client.command(pass_context=True)
async def hat(ctx, *args):
    """
    Main command of the bot, creates a new avatar for a user with a Christmas hat on it.
    Grabs the user avatar and puts the hat in the top middle location with optional flags
    on x/y coords and image scaling
    :param ctx: Context of the message, i.e. sender/channel/attachments
    :param args: Optional flags to manipulate image
    """
    message = ctx.message
    url = message.author.avatar_url
    response = requests.get(url, headers={'User-agent': 'Mozilla/5.0'})

    image = Image.open(BytesIO(response.content))
    hat = check_hat(args, image)
    image_w, image_h = image.size
    hat_w, hat_h = hat.size

    w_offset, h_offset = check_dim(args, image_h, image_w, hat_w)
    image.paste(hat, (w_offset, h_offset), mask=hat)
    image.save("crimmis_hats/remade.png")

    channel = message.channel
    if channel in images:
        await client.delete_message(images.get(channel))

    message = await client.send_file(message.channel, "crimmis_hats/remade.png", filename="newhat.png", content="Hat: ")
    images[channel] = message
    os.remove("crimmis_hats/remade.png")


client.run('Bot_token)
