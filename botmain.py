import traceback

import pytz
import datetime
import discord
import requests
from discord.ext import commands
from PIL import Image
from io import BytesIO
import os
import numpy as np
from utils import get_imgs
import random
import string
import config
from error_handler import CommandErrorHandler

Client = discord.Client()
client = commands.Bot(command_prefix="q!")
client.add_cog(CommandErrorHandler(client))

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
    hat_counts = np.load('hat_counts.npy')

    print("q!num_servers from: {} in #{} ".format(ctx.message.channel.guild.name, ctx.message.channel.name))
    string = "CrimmisHatBot is in {} servers, having given hats to {} users since 11/15/21!".format(len(client.guilds), hat_counts)
    await ctx.channel.send(string)


@client.command(pass_context=True)
async def feedback(ctx):
    """ Used as a means to get feedback from users """
    m = ctx.message
    print("Feedback from {} in {}: {}".format(m.author, m.channel, m.content))
    await ctx.channel.send("Thanks for providing feedback!")


@client.command(pass_context=True)
async def hathelp(ctx):
    if isinstance(ctx.message.channel, discord.DMChannel):
        print("Help message used for {} in DM".format(ctx.message.author.name))
    else:
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
             "Note that this bot will sometimes be down for maintenance or upgrades. Thanks!\n" \
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
    try:
        # Check for direct message
        if isinstance(ctx.message.channel, discord.DMChannel):
            print("Making hat for {} in DM \t Arguments: {}".format(ctx.message.author, args))
        else:
            print("Making hat for {} in {} \t Arguments: {}".format(ctx.message.author, ctx.message.channel.guild.name, args))
        message = ctx.message

        # Check whether an attachment is provided
        if len(message.attachments) > 0:
            url = message.attachments[0].url
        else:
            url = "https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(ctx.message.author)

        # Get the image via an html request
        response = requests.get(url, headers={'User-agent': 'Mozilla/5.0'})
        image = Image.open(BytesIO(response.content)).resize((500, 500))

        # Apply base transformations as needed (flip and scale)
        hat, width, height = check_hat(args)
        if hat is None:
            await ctx.channel.send("Wrong command formatting, try again!")
            return

        # Apply move given and temporarily save hat
        image.paste(hat, move(args, width, height), mask=hat)
        im_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        image.save("crimmis_hats/createdhats/{}.png".format(im_name))

        # Check whether previous hat already exists and clean it up
        if message.author.id in users.keys() and not isinstance(ctx.message.channel, discord.DMChannel):
            try:
                await ctx.channel.delete_messages([users.get(message.author.id)])
            except discord.errors.NotFound:
                print("Could not delete message for {} - {}".format(message.author.name, message.author.name))

        # Send finalized image
        image = await ctx.channel.send("Here is your hat, {}!".format(ctx.message.author.name),
                                       file=discord.File("crimmis_hats/createdhats/{}.png".format(im_name)))

        # Add current message to the users dictionary and remove hat locally
        users[message.author.id] = image
        os.remove("crimmis_hats/createdhats/{}.png".format(im_name))

        # Add hat counter
        hat_counts = np.load('hat_counts.npy')
        hat_counts += 1
        np.save('hat_counts.npy', hat_counts)
    except Exception as e:
        # Catching general exceptions to give to users, handles traceback print out still
        print("Error making hat for {}, args {}. Exception {}.".format(ctx.message.author, args, e))
        await ctx.channel.send("{}, an error has occurred when making the hat. Make sure the arguments are correct!".format(ctx.message.author.name))


@client.command(pass_context=True)
async def CHAMPION(ctx):
    await ctx.channel.send("THE CHAMPION!", file=discord.File("peepocheer.png"))


@client.command(pass_context=True)
async def ezclap(ctx):
    await ctx.channel.send("https://tenor.com/view/pepe-clap-gif-10184275")


@client.command(pass_context=True)
async def YEP(ctx):
    await ctx.channel.send("YEP Crimmis", file=discord.File("YEPCrimmis.png"))


@client.command(pass_context=True)
async def expansion(ctx):
    # Take the time now and get the datetime of the release date
    tzin = pytz.timezone('US/Eastern')

    now = datetime.datetime.now(tzin)
    release = datetime.datetime(year=2021, month=11, day=19, hour=4, second=0, microsecond=0, tzinfo=tzin)

    # Get total seconds worth of difference between two dates
    difference = (release - now).total_seconds()

    # Calculate raw values for each
    minutes = difference / 60
    hours = minutes / 60
    days = hours / 24

    # Calculate chunks of total seconds between them
    sub_days = np.floor(days)
    sub_hours = np.floor(hours - (np.floor(days) * 24))
    sub_minutes = np.floor(minutes - (np.floor(hours) * 60))
    sub_seconds = np.floor(difference - (np.floor(minutes) * 60))

    # Generate string for difference
    timediff = "{} days, {} hours, {} minutes, and {} seconds!".format(
        int(sub_days), int(sub_hours), int(sub_minutes), int(sub_seconds))

    # Generate Discord embed
    embed = discord.Embed()
    embed.add_field(name="Time until Endwalker:", value=timediff)
    embed.set_image(url="https://cdn.discordapp.com/emojis/663359486769233920.gif?v=1")
    await ctx.channel.send(embed=embed)


client.run(config.BOT_TOKEN)
