import discord
from discord.ext import commands
from PIL import Image
import requests
from io import BytesIO

bot_prefix = "q!"
Client = discord.Client()
client = commands.Bot(command_prefix=bot_prefix)


@client.async_event
async def on_ready():
    print("Logged on as {}".format(client.user))


@client.command(pass_context=True)
async def for_shed(ctx):
    image = Image.open("users/shed/lugia.png")
    await client.send_file(ctx.message.channel, image)


def check_args(args):
    hat = Image.open("crimmis_hats/cryms.png")
    for arg in args:
        if arg == '--flip':
            hat = hat.transpose(Image.FLIP_LEFT_RIGHT)
        if arg.startswith('--scaled='):
            value = float(arg.split('=')[1])
            w, h = hat.size
            w_scaled, h_scaled = (int(w * value), int(h * value))
            hat = hat.resize((w_scaled, h_scaled))
    return hat


@client.command(pass_context=True)
async def puthat(ctx, *args):
    """
    Main command of the bot, creates a new avatar for a user with a Christmas hat on it.
    Grabs the user avatar and puts the hat in the top middle location with optional flags
    on x/y coords and image scaling
    :param ctx: Context of the message, i.e. sender/channel/attachments
    :param args: Optional flags to manipulate image
    """
    message = ctx.message
    url = message.author.avatar_url
    print("{} in {} called put_hat. Executing...".format(message.author, message.channel), end="")
    response = requests.get(url, headers={'User-agent': 'Mozilla/5.0'})

    image = Image.open(BytesIO(response.content))
    hat = check_args(args)
    image_w, image_h = image.size
    hat_w, hat_h = hat.size

    offset = ((image_w - hat_w) // 2, (image_h - hat_h) // 2)
    image.paste(hat, offset, mask=hat)
    image.save("crimmis_hats/remade.png")

    await client.send_file(message.channel, "crimmis_hats/remade.png", filename="newhat.png", content="Hat: ")
    print("...command complete.")


client.run('BOT_TOKEN')
