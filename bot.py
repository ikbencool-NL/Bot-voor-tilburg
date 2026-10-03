import os
import re

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN", "")
BOT_NAME = os.getenv("BOT_NAME", "Westhuizen roleplay | asistent")

TICKET_CREATE_CHANNEL_ID = 1554172545597448322
TICKET_CATEGORY_ID = 1554172454417469572
LOG_CHANNEL_ID = 1554172709020242040
SUPPORT_ROLE_ID = 1554172275069292614

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


def server_footer(guild: discord.Guild | None = None) -> discord.Embed:
    embed = discord.Embed()
    if guild and guild.icon:
        embed.set_footer(text=guild.name, icon_url=guild.icon.url)
    elif guild:
        embed.set_footer(text=guild.name)
    return embed


def build_ticket_embed(guild: discord.Guild | None = None) -> discord.Embed:
    embed = discord.Embed(
        title="🎫 Ticket aanmaken",
        description=(
            "Welkom bij het support-systeem van deze server.\n\n"
            "Klik hieronder op de knop om een ticket aan te maken.\n"
            "Vermeld uw probleem of vraag zo duidelijk mogelijk, dan kunnen wij u sneller helpen."
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name="Hoe werkt het?",
        value="- Kies hieronder `Ticket aanmaken`\n- Beschrijf uw probleem\n- Een medewerker reageert zo snel mogelijk",
        inline=False,
    )
    embed.set_thumbnail(url=guild.icon.url if guild and guild.icon else bot.user.avatar.url if bot.user and bot.user.avatar else discord.Embed.Empty)
    if guild:
        embed.set_footer(text=guild.name, icon_url=guild.icon.url if guild.icon else None)
    return embed


def build_log_embed(title: str, description: str, color: discord.Color, guild: discord.Guild | None = None) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color)
    if guild:
        embed.set_footer(text=guild.name, icon_url=guild.icon.url if guild.icon else None)
    return embed


class TicketCreateView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label="Ticket aanmaken",
                emoji="🎫",
                style=discord.ButtonStyle.primary,
                custom_id="ticket_create",
            )
        )


class TicketActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label="Ticket sluiten",
                emoji="🔒",
                style=discord.ButtonStyle.danger,
                custom_id="ticket_close",
            )
        )
        self.add_item(
            discord.ui.Button(
                label="Ticket claimen",
                emoji="✅",
                style=discord.ButtonStyle.success,
                custom_id="ticket_claim",
            )
        )
        self.add_item(
            discord.ui.Button(
                label="Reminder",
                emoji="⏰",
                style=discord.ButtonStyle.secondary,
                custom_id="ticket_reminder",
            )
        )


async def log_ticket_event(guild: discord.Guild, title: str, description: str, color: discord.Color):
    channel = guild.get_channel(LOG_CHANNEL_ID)
    if channel is None:
        return
    embed = build_log_embed(title, description, color, guild)
    await channel.send(embed=embed)


async def create_ticket(interaction: discord.Interaction):
    guild = interaction.guild
    if guild is None:
        return

    category = guild.get_channel(TICKET_CATEGORY_ID)
    if category is None:
        await interaction.response.send_message("❌ De ticketcategorie is niet gevonden.", ephemeral=True)
        return

    safe_name = re.sub(r"[^a-zA-Z0-9-]", "-", interaction.user.name.lower())
    safe_name = re.sub(r"-+", "-", safe_name).strip("-")
    channel_name = f"ticket-{safe_name}-{interaction.user.discriminator}"
    channel_name = channel_name[:80]

    existing = discord.utils.find(
        lambda c: isinstance(c, discord.TextChannel) and c.name.startswith(f"ticket-{safe_name}") and c.category_id == category.id,
        guild.channels,
    )
    if existing is not None:
        await interaction.response.send_message(f"Je hebt al een open ticket: {existing.mention}", ephemeral=True)
        return

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, attach_files=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True),
    }

    ticket_channel = await guild.create_text_channel(
        channel_name,
        category=category,
        overwrites=overwrites,
        reason=f"Ticket aangemaakt door {interaction.user} ({interaction.user.id})",
    )

    support_role = guild.get_role(SUPPORT_ROLE_ID)
    if support_role:
        await ticket_channel.set_permissions(support_role, view_channel=True, send_messages=True, read_message_history=True, manage_messages=True)

    embed = discord.Embed(
        title="🎫 Ticket geopend",
        description=(
            f"Hallo {interaction.user.mention},\n\n"
            "Dankjewel voor je bericht. Een medewerker van het supportteam zal zo snel mogelijk reageren.\n"
            "Beschrijf je vraag of probleem hieronder zo duidelijk mogelijk."
        ),
        color=discord.Color.green(),
    )
    embed.add_field(
        name="Belangrijk",
        value="- Geef zo veel mogelijk informatie\n- Vermeld tijdstippen indien relevant\n- Een van onze supportmedewerkers neemt z.s.m. contact met je op",
        inline=False,
    )
    embed.set_footer(text=guild.name, icon_url=guild.icon.url if guild.icon else None)

    await ticket_channel.send(embed=embed, view=TicketActionView())
    await interaction.response.send_message(f"Je ticket is aangemaakt: {ticket_channel.mention}", ephemeral=True)

    await log_ticket_event(
        guild,
        "🎫 Nieuw ticket aangemaakt",
        f"**Gebruiker:** {interaction.user.mention}\n**Kanaal:** {ticket_channel.mention}\n**Tijd:** <t:{int(discord.utils.utcnow().timestamp())}:F>",
        discord.Color.blue(),
    )


async def close_ticket(interaction: discord.Interaction):
    if interaction.channel is None or interaction.guild is None:
        return

    channel = interaction.channel
    if not isinstance(channel, discord.TextChannel):
        return

    creator = None
    for member in channel.members:
        if member != interaction.guild.me:
            creator = member
            break

    await log_ticket_event(
        interaction.guild,
        "🔒 Ticket gesloten",
        f"**Kanaal:** {channel.mention}\n**Gebruiker:** {creator.mention if creator else 'Onbekend'}\n**Gesloten door:** {interaction.user.mention}\n**Tijd:** <t:{int(discord.utils.utcnow().timestamp())}:F>",
        discord.Color.orange(),
    )

    await interaction.response.send_message("✅ Ticket wordt gesloten...", ephemeral=True)
    await channel.delete(reason=f"Ticket gesloten door {interaction.user} ({interaction.user.id})")


async def claim_ticket(interaction: discord.Interaction):
    if interaction.channel is None or interaction.guild is None:
        return

    support_role = interaction.guild.get_role(SUPPORT_ROLE_ID)
    if support_role and support_role not in interaction.user.roles:
        try:
            await interaction.response.send_message("❌ Je hebt niet de juiste support-rol om dit ticket te claimen.", ephemeral=True)
        except discord.NotFound:
            pass
        return

    channel = interaction.channel
    creator = None
    for member in channel.members:
        if member != interaction.guild.me:
            creator = member
            break

    embed = discord.Embed(
        title="✅ Ticket geclaimd",
        description=f"Dit ticket is geclaimed door {interaction.user.mention}.",
        color=discord.Color.green(),
    )
    embed.set_footer(text=interaction.guild.name, icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
    await interaction.response.send_message(embed=embed)

    await log_ticket_event(
        interaction.guild,
        "✅ Ticket geclaimd",
        f"**Ticket:** {interaction.channel.mention}\n**Supportmedewerker:** {interaction.user.mention}\n**Tijd:** <t:{int(discord.utils.utcnow().timestamp())}:F>",
        discord.Color.green(),
    )


async def reminder_ticket(interaction: discord.Interaction):
    if interaction.channel is None or interaction.guild is None:
        return

    support_role = interaction.guild.get_role(SUPPORT_ROLE_ID)
    if support_role and support_role not in interaction.user.roles:
        try:
            await interaction.response.send_message("❌ Je hebt niet de juiste support-rol om een reminder te sturen.", ephemeral=True)
        except discord.NotFound:
            pass
        return

    embed = discord.Embed(
        title="⏰ Reminder",
        description=(
            "Deze ticket is nog open en wacht op een reactie.\n\n"
            "Supportteam, kunt u hier zo snel mogelijk op reageren?"
        ),
        color=discord.Color.gold(),
    )
    embed.set_footer(text=interaction.guild.name, icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
    await interaction.response.send_message(embed=embed)

    await log_ticket_event(
        interaction.guild,
        "⏰ Ticket reminder",
        f"**Ticket:** {interaction.channel.mention}\n**Verzonden door:** {interaction.user.mention}\n**Tijd:** <t:{int(discord.utils.utcnow().timestamp())}:F>",
        discord.Color.gold(),
    )


@bot.event
async def on_ready():
    print(f"{BOT_NAME} is online op Discord!")
    print(f"Ingelogd als: {bot.user.name}")

    guild = next(iter(bot.guilds), None)
    if guild is None:
        return

    channel = guild.get_channel(TICKET_CREATE_CHANNEL_ID)
    if channel is None:
        print(f"Ticketkanaal {TICKET_CREATE_CHANNEL_ID} niet gevonden.")
        return

    if not isinstance(channel, discord.TextChannel):
        print(f"Kanaal {TICKET_CREATE_CHANNEL_ID} is geen tekstkanaal.")
        return

    existing = None
    async for message in channel.history(limit=20):
        if message.author == bot.user and message.embeds and message.embeds[0].title == "🎫 Ticket aanmaken":
            existing = message
            break

    if existing is not None:
        await existing.edit(embed=build_ticket_embed(guild), view=TicketCreateView())
        print(f"Ticket embed bijgewerkt in kanaal: {channel.name}")
    else:
        await channel.send(embed=build_ticket_embed(guild), view=TicketCreateView())
        print(f"Ticket embed geplaatst in kanaal: {channel.name}")


@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data.get("custom_id")
        if custom_id == "ticket_create":
            await create_ticket(interaction)
        elif custom_id == "ticket_close":
            await close_ticket(interaction)
        elif custom_id == "ticket_claim":
            await claim_ticket(interaction)
        elif custom_id == "ticket_reminder":
            await reminder_ticket(interaction)


if __name__ == "__main__":
    if not TOKEN:
        print("Geen Discord token gevonden. Voeg je token toe in het .env-bestand.")
    else:
        bot.run(TOKEN)
