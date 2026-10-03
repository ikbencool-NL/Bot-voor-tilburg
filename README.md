# Nederlandse Discord-bot met slash commands

Deze bot is een eenvoudige Discord-bot in het Nederlands met moderne slash commands.

## Stap 1: bot token invullen

Open [.env](.env) en controleer of je token correct staat.

```env
DISCORD_TOKEN=JOUW_DISCORD_TOKEN_HIER
BOT_PREFIX=!
BOT_NAME=Westhuizen roleplay | asistent
```

## Stap 2: afhankelijkheden installeren

Gebruik deze opdracht in PowerShell:

```powershell
& "$env:LOCALAPPDATA\Microsoft\WindowsApps\python.exe" -m pip install -r requirements.txt
```

## Stap 3: bot starten

```powershell
& "$env:LOCALAPPDATA\Microsoft\WindowsApps\python.exe" bot.py
```

## Railway-hosting

De `Procfile` start de bot als een worker met `python bot.py`. Zet de projectbestanden in de GitHub-repository die je aan Railway koppelt en kies in Railway **Deploy from GitHub repo**.

Voeg in Railway bij **Variables** deze variabelen toe:

- `DISCORD_TOKEN` - gebruik de opnieuw gegenereerde bot-token; zet deze nooit in GitHub
- `BOT_NAME` - bijvoorbeeld `Westhuizen roleplay | asistent`

Kies geen webserver: een Discord-bot is een worker die continu draait. Controleer na deploy de Railway-deploylogs op de melding dat de bot online is. Railway kan kosten rekenen voor de service.

## Slash commands

- `/hello` - begroet de bot
- `/ping` - controleer de online status
- `/info` - laat informatie zien
- `/help` - toont alle commands

## Tekstcommando's

- `!hallo`
- `!ping`
- `!info`
- `!help`

## Opmerking

Na het starten moet je de bot in een Discord-server hebben toegevoegd en de juiste botrechten hebben gegeven.
