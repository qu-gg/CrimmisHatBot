import discord
import requests
from discord.ext import commands
from PIL import Image
from io import BytesIO
import os
from utils import get_imgs
import random
import string
import config

Client = discord.Client()
client = commands.Bot(command_prefix="q!")

users = {}


@client.event
async def on_ready():
    print("Logged on as {}".format(client.user))
    game = discord.Game(name="\'q!hathelp\' for info!")
    await client.change_presence(activity=game)


@client.event
async def on_message_delete(message):
    """
    # If the message deleted is within the dictionaries, pop that key respectively
    # in order to clear cache.
    # :param message: Message that was deleted
    """
    if message.author.id in users:
        users.pop(message.author.id, None)


@client.command(pass_context=True)
async def num_servers(ctx):
    """ Prints out the number of servers this bot is in """
    print("q!num_servers from: {} in #{} ".format(ctx.message.channel.guild.name, ctx.message.channel.name))
    string = "CrimmisHatBot is in {} servers, giving hats to {} users!".format(len(client.guilds), len(client.users))
    await ctx.channel.send(string)


@client.command(pass_context=True)
async def feedback(ctx):
    """ Used as a means to get feedback from users """
    m = ctx.message
    print("Feedback from {} in {}: {}".format(m.author, m.channel, m.content))
    await ctx.channel.send("Thanks for providing feedback!")


@client.command(pass_context=True)
async def hathelp(ctx):
    print("Help message used in {}".format(ctx.message.channel.guild.name))
    string = "To use: **q!hat**\n" \
             "To see available hats: **q!hats**\n" \
             "\n" \
             "Parameters (commands use the format **command=number**):\n" \
             "type (0-4) - chooses what type of hat to use\n" \
             "flip - flips the image horizontally\n" \
             "scale - scales the image to a different size\n" \
             "left/right/up/down - moves the hat in the given direction\n" \
             "\n" \
             "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ \n" \
             "**Example of use with parameters: 'q!hat type=2 scale=2 up=20 left=50'**\n" \
             "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ \n" \
             "\n" \
             "This command selects hat 2, scales it to 2x size, and moves it accordingly\n" \
             "\n" \
             "Please use the command 'q!feedback <message>' to send your feedback!\n" \
             "Note on image quality: higher resolution avatars results in cleaner images\n" \
             "\n" \
             "If this bot did its job, consider giving it an upvote!\n" \
             "Link: https://discordbots.org/bot/520376798131912720" \

    embed = discord.Embed()
    embed.add_field(name="CrimmisHatBot Usage!", value=string)
    await ctx.channel.send(embed=embed)


@client.command(pass_context=True)
async def hats(ctx):
    print("Showing available hats in {}".format(ctx.message.channel.guild.name))
    await ctx.channel.send("Here are all the available hats!", file=discord.File("crimmis_hats/hats.png"))


def check_hat(args):
    """ Helper function that handles hat manipulations, like flip and scale """
    try:
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
    except:
        return None, None, None

    return hat, w_offset, h_offset


def move(args, width, height):
    """ Helper function used to shift the hat in a certain direction """
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
    """ Handles creating and returning a hat to a user """
    print("Making hat for {} in {} \t Arguments: {}".format(ctx.message.author, ctx.message.channel.guild.name, args))
    message = ctx.message

    if len(message.attachments) > 0:
        url = message.attachments[0].url
    else:
        url = "https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(ctx.message.author)

    response = requests.get(url, headers={'User-agent': 'Mozilla/5.0'})
    image = Image.open(BytesIO(response.content)).resize((500, 500))

    hat, width, height = check_hat(args)

    if hat is None:
        await ctx.channel.send("Wrong command formatting, try again!")
        return

    image.paste(hat, move(args, width, height), mask=hat)
    im_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    image.save("crimmis_hats/createdhats/{}.png".format(im_name))

    if message.author.id in users.keys():
        await ctx.channel.delete_messages([users.get(message.author.id)])

    image = await ctx.channel.send("Here is your hat, {}!".format(ctx.message.author.name),
                                   file=discord.File("crimmis_hats/createdhats/{}.png".format(im_name)))

    users[message.author.id] = image
    os.remove("crimmis_hats/createdhats/{}.png".format(im_name))


@client.command(pass_context=True)
async def CHAMPION(ctx):
    await ctx.channel.send("THE CHAMPION!", file=discord.File("peepocheer.png"))


@client.command(pass_context=True)
async def ezclap(ctx):
    await ctx.channel.send("https://tenor.com/view/pepe-clap-gif-10184275")


client.run(config.BOT_TOKEN)