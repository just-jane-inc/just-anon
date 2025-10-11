import os
import discord
from discord import app_commands, ui
from dotenv import load_dotenv
import wave
from scipy.io import wavfile
from uuid import uuid4 as uuid

load_dotenv()

def assert_wav_48khz(filepath) -> bool:
    """
    Asserts that the given file is a WAV file and has a sample rate of 48kHz.

    Args:
        filepath (str): The path to the audio file.

    Raises:
        AssertionError: If the file is not a WAV file or if its sample rate is not 48kHz.
        FileNotFoundError: If the file does not exist.
    """
    try:
        with wave.open(filepath, 'rb'):
            # we do not need to do anything with this, simply opening the 
            # file asserts its type with the wave library
            pass 
    except wave.Error:
        print("whatever it is not a wave file")
        return False
    except FileNotFoundError:
        print ("erm no file exists")
        return False

    # Read the WAV file using scipy.io.wavfile to get the sample rate
    samplerate, _ = wavfile.read(filepath)

    # Assert the sample rate
    return samplerate == 48000

TOKEN = os.getenv('BOT_TOKEN')
assert TOKEN is not None
GUILD_ID = os.getenv("GUILD_ID")
assert GUILD_ID is not None

class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild) # how do we get commands in the tree?
            print(f"Synced commands to guild {GUILD_ID}")
        else:
            await self.tree.sync()
            print("Synced commands globally")

bot = MyBot()

# slash command -> bot gives you instructions -> presents file upload thing -> you upload file
@bot.tree.command(name="upload_bark", description="give me your barks")
@app_commands.describe(file="# Upload a wav file with a 48khz sample rate\nhello world\nwhat do")
async def upload_file(interaction: discord.Interaction, file: discord.Attachment):
    print(interaction.user.display_name)
    if file.size > 8 * 1024 * 1024:
        await interaction.response.send_message("File is too large!", ephemeral=True)
        return

    try:
        path = f"uploaded_files/barks/{uuid()}-{interaction.user.display_name}"
        await file.save(path)
        if not assert_wav_48khz(path):
            # TODO: delete file if not okay
            await interaction.response.send_message(f"your file must be a 48khz wave file please and thank you!", ephemeral=True)
        else:
            await interaction.response.send_message(f"File '{file.filename}' uploaded and saved locally!", ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(f"Error processing file: {e}", ephemeral=True)

@bot.tree.command(name="upload_clap", description="give me your claps")
@app_commands.describe(file="# Upload a wav file with a 48khz sample rate\nhello world\nwhat do")
async def give_me_your_barks(interaction: discord.Interaction, file: discord.Attachment):
    if file.size > 8 * 1024 * 1024:
        await interaction.response.send_message("File is too large!", ephemeral=True)
        return

    try:
        path = f"uploaded_files/claps/{uuid()}-{interaction.user.display_name}"
        await file.save(path)
        if not assert_wav_48khz(path):
            # TODO: delete file if not okay
            await interaction.response.send_message(f"your file must be a 48khz wave file please and thank you!", ephemeral=True)
        else:
            await interaction.response.send_message(f"File '{file.filename}' uploaded and saved locally!", ephemeral=True)


    except Exception as e:
        await interaction.response.send_message(f"Error processing file: {e}", ephemeral=True)

bot.run(TOKEN)

