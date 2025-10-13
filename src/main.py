import os
import discord
from discord import app_commands
from dotenv import load_dotenv
import wave
from scipy.io import wavfile
from uuid import uuid4 as uuid
from pathlib import Path

load_dotenv()

os.makedirs("uploaded_files", exist_ok=True)

TOKEN = os.getenv('BOT_TOKEN')
GUILD_ID = os.getenv("GUILD_ID")
assert GUILD_ID is not None
assert TOKEN is not None

class JustAnon(discord.Client):
    """
    The JustAnon discord bot class

    This is where the magic happens - happyNora
    """
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

    def assert_wav_48khz(self, filepath: Path):
        """
        Asserts that given file is a WAV file and has a sample rate of 48kHz.

        Args:
            filepath (Path): The path to the audio file.

        Raises:
            Exception: raises an exception with a message that tells the user about the issue
        """
        try:
            with wave.open(str(filepath), 'rb'):
                pass 
        except wave.Error:
            raise Exception("the provided file is not a wave file")
        except FileNotFoundError:
            raise Exception("internal error")

        samplerate, _ = wavfile.read(str(filepath))

        if samplerate != 48000:
            raise Exception("provided wave file must be 48khz")

    async def process_file(self, filepath: Path, interaction: discord.Interaction, file: discord.Attachment, deleteOnFail: bool) -> bool:
        """
        Ensures a file is of the correct format and writes it to disk

        Args:
            filepath (Path): The path to write the file to
            interaction (discord.Interaction): The interaction model for discord messaging
            file (discord.Attachment): The attachment containing the file

        Returns:
            A flag indicating true if the file was saved and is the correct format
        """
        if file.size > 8 * 1024 * 1024:
            await interaction.response.send_message("File is too large!", ephemeral=True)
            return False

        try:
            await file.save(filepath)
            self.assert_wav_48khz(filepath)
        except Exception as e:
            await interaction.response.send_message(
                f"""
Encountered an error while processing your file

> {e}

If your file was categorized 'misc' you can ignore this error.
                """,
                ephemeral=True)

            if deleteOnFail:
                os.remove(filepath)

            return False

        return True

    def run_bot(self):
        self.run(TOKEN)

bot = JustAnon()

@bot.tree.command(name="anon_upload", description="give me your barks")
@app_commands.describe(file="# Upload a wav file with a 48khz sample rate")
async def upload_audio_command(interaction: discord.Interaction, file: discord.Attachment):
    view = UploadOptions(file)
    await interaction.response.send_message(
        f"📁 File `{file.filename}` received. Set your options below:",
        view=view,
        ephemeral=True
    )

class UploadOptions(discord.ui.View):
    """The view used in discord for file uploads"""
    def __init__(self, file: discord.Attachment):
        super().__init__(timeout=120)
        self.file = file
        self.anonymize = None
        self.choice = None

    @discord.ui.button(label="please anonymize me", style=discord.ButtonStyle.secondary)
    async def anon_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.anonymize = True
        self.anon_button.style = discord.ButtonStyle.success
        self.public_button.style = discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="i am not ashamed", style=discord.ButtonStyle.secondary)
    async def public_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.anonymize = False
        self.public_button.style = discord.ButtonStyle.success
        self.anon_button.style = discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)

    @discord.ui.select(
        placeholder="Choose one...",
        options=[
            discord.SelectOption(label="bark", description="must be earnest!"),
            discord.SelectOption(label="nya", description="nyyyaaa =^-^="),
            discord.SelectOption(label="ara-ara", description="mhmm"),
            discord.SelectOption(label="clap", description="yippie"),
            discord.SelectOption(label="misc", description="send me something wholesome? idk")
        ]
    )
    async def mode_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.choice = select.values[0]
        await interaction.response.defer()

    @discord.ui.button(label="Submit", style=discord.ButtonStyle.primary)
    async def submit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.choice:
            await interaction.response.send_message(
                "⚠️ Please select a category first.", ephemeral=True
            )
            return
        if self.anonymize == None:
            await interaction.response.send_message(
                "please choose whether you want to be anonymous", ephemeral=True
            )
            return

        path = Path("uploaded_files")
        if self.anonymize:
            path = path/f"{self.choice}-{uuid()}"
        else:
            path = path/f"{self.choice}-{uuid()}-{interaction.user.display_name}"

        if not await bot.process_file(path, interaction, self.file, self.choice != "misc"):
            return

        await interaction.response.send_message("thank you!", ephemeral=True)

        self.stop()

bot.run_bot()
