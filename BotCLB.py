import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal
import datetime
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from keep_alive import keep_alive

# Chargement des variables d'environnement
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Configuration des permissions du bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Configuration
PREFIX = "!"
ROLE_ID = 1345369176994484316  # ID du rôle à attribuer en cas de succès
ADMIN_ROLE_ID = 1345369356720148561  # ID du rôle admin pour les commandes
LOG_FILE = "quiz_attempts.json"
CHANNEL_LOGS_DROGE_ID = 1347969843629916301

def load_attempts():
    try:
        with open(LOG_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"tentatives": []}

def save_attempts(data):
    with open(LOG_FILE, "w") as file:
        json.dump(data, file, indent=4)

bot = commands.Bot(command_prefix=PREFIX, intents=discord.Intents.all())

QUIZ_QUESTIONS = [
    {"question": "Quelle est le code de la porte du QG ?", "answer": "8128", "type": "text"},
    {"question": "Combien nous sommes dans le gang ?", "choices": ["5", "4", "6"], "answer": "5", "type": "choice"},
    {"question": "Quelle est la couleur iconique du gang ?", "choices": ["Rouge - Jaune", "Jaune - Noir", "Bleu - Vert"], "answer": "Jaune - Noir", "type": "choice"},
    {"question": "Sommes nous un groupe caché ou un groupe Public", "choices": ["Groupe Caché", "Groupe Public"], "answer": "Groupe Caché", "type": "choice"}
]

@bot.event
async def on_ready():
    print(f"{bot.user} est pret a niqué les gens")

@bot.command()
async def vérif(ctx):
    user_id = str(ctx.author.id)
    attempts = load_attempts()
    
    if any(a['id'] == user_id for a in attempts["tentatives"]):
        await ctx.send("❌ Tu as déjà tenté la vérification. Si tu as échoué, quitte et reviens sur le serveur.")
        return
    
    correct = True
    for q in QUIZ_QUESTIONS:
        if q["type"] == "text":
            await ctx.message.delete()
            await ctx.send(q["question"])
            msg = await bot.wait_for("message", check=lambda m: m.author == ctx.author)
            if msg.content.strip() != q["answer"]:
                correct = False
        else:
            options = '\n'.join([f"{choice}" for i, choice in enumerate(q["choices"])] )
            await ctx.send(f"{q['question']}\n{options}")
            msg = await bot.wait_for("message", check=lambda m: m.author == ctx.author)
            if msg.content.strip() != q["answer"]:
                correct = False
    
    attempts["tentatives"].append({
        "utilisateur": str(ctx.author),
        "id": user_id,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "réussi": correct
    })
    save_attempts(attempts)
    
    channel = ctx.channel  # Le canal actuel

    if correct:
        role = discord.utils.get(ctx.guild.roles, id=ROLE_ID)
        await ctx.author.add_roles(role)
        await ctx.send("✅ Félicitations, tu as réussi la vérification !")
        await channel.delete()
        log_channel = bot.get_channel(LOGS_CHANNEL_ID)
        if log_channel:
            await log_channel.send(f"🔴 Ticket {channel.name} fermé")
    else:
        await ctx.send("❌ Échec la vérification. Quitte et reviens pour réessayer.")
        await channel.delete()


@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def reset_vérif(ctx, member: discord.Member):
        attempts = load_attempts()
        attempts["tentatives"] = [a for a in attempts["tentatives"] if a["id"] != str(member.id)]
        save_attempts(attempts)
        await ctx.send(f"🔄 Les tentatives de {member.mention} ont été réinitialisées.")

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def list_vérif(ctx):
    attempts = load_attempts()
    if not attempts["tentatives"]:
        await ctx.send("📜 Aucune tentative enregistrée.")
        return
    
    log = "\n".join([f"{a['utilisateur']} | {a['date']} | Réussi: {a['réussi']}" for a in attempts["tentatives"]])
    await ctx.send(f"📜 Liste des tentatives:\n```{log}```")

# ----------------------------------------------------------------

@bot.command()
@commands.has_permissions(administrator=True)
async def say(ctx, *, message: str):
    """Envoie un message avec le bot"""
    await ctx.message.delete()
    await ctx.send(message)

# ----------------------------------------------------------------

tickets = {}
LOGS_CHANNEL_ID = 1345390352181231616  # Remplace par l'ID du salon de logs
TICKET_CATEGORY_ID = 1345368545176981677  # Remplace par l'ID de la catégorie où seront créés les tickets
TICKET_FILE = "tickets.json"


def save_tickets():
    with open("tickets.json", "w") as f:
        json.dump(tickets, f)

def load_tickets():
    global tickets
    try:
        with open(TICKET_FILE, "r") as f:
            content = f.read().strip()
            tickets = json.loads(content) if content else {}  # Vérifie si le fichier n'est pas vide
    except (FileNotFoundError, json.JSONDecodeError):
        tickets = {}  # Initialise un dictionnaire vide si le fichier est vide ou corrompu


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="👤Faire une vérification", style=discord.ButtonStyle.danger)
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild  # Défini correctement interaction ici
        user = interaction.user
        category = discord.utils.get(guild.categories, id=TICKET_CATEGORY_ID)
        mod_role = guild.get_role(ADMIN_ROLE_ID)  # Récupère le rôle modérateur
        
        if any(channel for channel in guild.text_channels if channel.topic == str(user.id)):
            await interaction.response.send_message("🚨 Tu as déjà une vérification en cours imbécile", ephemeral=True)
            return
        
        # Définition des permissions
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),  # Bloque tout le monde
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),  # Permet à l'utilisateur de voir et écrire
            mod_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_messages=True)  # Les modérateurs ont un accès complet
        }

        # Création du salon avec les permissions
        ticket_channel = await guild.create_text_channel(
            f"vérification︱{user.name}",
            category=category,
            topic=str(user.id),
            overwrites=overwrites
        )

        # Sauvegarde du ticket
        tickets[ticket_channel.id] = {"user": user.id, "open": True}
        save_tickets()

        # Envoie du message avec le bouton de fermeture
        embed = discord.Embed(title="👤 Vérification Actif", description=f"{user.mention}, Tu peux faire !vérif pour commencer. Attention si tu loupe tu dégage !", color=discord.Color.red())
        close_button = CloseTicketView(ticket_channel.id)
        await ticket_channel.send(embed=embed, view=close_button)
        await interaction.response.send_message(f"✅ Ta vérification t'attend ici: {ticket_channel.mention}", ephemeral=True)

        # Logs
        log_channel = bot.get_channel(LOGS_CHANNEL_ID)
        if log_channel:
            await log_channel.send(f"📌 Vérification par {user.mention} ({user.id}) dans {ticket_channel.mention}")


class CloseTicketView(discord.ui.View):
    def __init__(self, channel_id):
        super().__init__(timeout=None)
        self.channel_id = channel_id

    @discord.ui.button(label="🔒 Fermer le ticket", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        guild = interaction.guild
        mod_role = discord.utils.get(guild.roles, id=ADMIN_ROLE_ID)

        if mod_role not in user.roles:
            await interaction.response.send_message("🚨 Seuls les modérateurs peuvent fermer un ticket.", ephemeral=True)
            return

        confirm_view = ConfirmCloseView(self.channel_id)
        await interaction.response.send_message("⚠️ **Confirmation requise** - Un modérateur doit valider la fermeture du ticket.", view=confirm_view)

class ConfirmCloseView(discord.ui.View):
    def __init__(self, channel_id):
        super().__init__(timeout=None)
        self.channel_id = channel_id

    @discord.ui.button(label="✅ Confirmer la fermeture", style=discord.ButtonStyle.success)
    async def confirm_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = bot.get_channel(self.channel_id)
        if channel:
            await channel.delete()
            del tickets[self.channel_id]
            save_tickets()
            
            await interaction.response.send_message("✅ Ticket fermé avec succès.")




@bot.command()
async def vérif_pnl(ctx):
    await ctx.message.delete()
    embed = discord.Embed(
        title="👤 Vérification", 
        description="Fais ta vérification avant de rentrer dans le serveur Los Banditos", 
        color=discord.Color.red())
    await ctx.send(embed=embed, view=TicketView())

# ----------------------------------------------------------------

class DrugFormModal(discord.ui.Modal, title="Formulaire de Plantation"):
    nom_planteur = discord.ui.TextInput(label="Nom du Planteur", placeholder="Entrez votre nom")
    type_drogue = discord.ui.TextInput(label="Type de Drogue", placeholder="Ex: Cannabis, Cocaïne...")
    quantite = discord.ui.TextInput(label="Quantité", placeholder="Ex: 10", style=discord.TextStyle.short)
    date = discord.ui.TextInput(label="Date (JJ/MM/AAAA HH:MM)", placeholder="Ex: 08/03/2025 14:30")
    localisation = discord.ui.TextInput(label="Localisation", placeholder="Adresse + Envoie image dans #IMAGE-PLANTATION")

    async def on_submit(self, interaction: discord.Interaction):
        
        embed = discord.Embed(title="Nouvelle Plantation", color=discord.Color.green())
        embed.add_field(name="Nom du Planteur", value=self.nom_planteur.value, inline=False)
        embed.add_field(name="Type de Drogue", value=self.type_drogue.value, inline=False)
        embed.add_field(name="Quantité", value=self.quantite.value, inline=False)
        embed.add_field(name="Date", value=self.date.value, inline=False)
        embed.add_field(name="Localisation", value=self.localisation.value, inline=False)
        embed.set_footer(text=f"Ajouté par {interaction.user.display_name}")

        log_channel = bot.get_channel(CHANNEL_LOGS_DROGE_ID)  # Remplace par l'ID du canal de logs
        if log_channel:
            await log_channel.send(embed=embed)
            await interaction.response.send_message("✅ Formulaire soumis avec succès !", ephemeral=True)

@bot.tree.command(name="planter", description="Remplir un formulaire de plantation")
async def planter(interaction: discord.Interaction):
    await interaction.response.send_modal(DrugFormModal())

# ----------------------------------------------------------------
@bot.command()
async def mp(ctx, user: discord.User, *, message: str):
    """
    Envoie un message privé à un utilisateur.

    :param ctx: Le contexte de la commande
    :param user: L'utilisateur auquel envoyer le message
    :param message: Le message à envoyer
    """
    try:
        # Envoi du message privé
        await user.send(message)
        await ctx.send(f"Le message a été envoyé à {user.name}.")
    except discord.Forbidden:
        # Si le bot ne peut pas envoyer un MP
        await ctx.send(f"Impossible d'envoyer un message privé à {user.name}. Ils ont peut-être désactivé les messages privés.")
    except discord.HTTPException as e:
        # En cas d'erreur d'envoi de message
        await ctx.send(f"Une erreur est survenue : {e}")

# ----------------------------------------------------------------
keep_alive()
# bot.run(TOKEN)
