import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
import os

# ⚙️ CONFIGURAÇÕES
API_URL = os.environ.get("API_URL", "http://SUA_API_AQUI")
TOKEN = os.environ.get("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ──────────────────────────────────────────
# 🎮 VIEW - Painel da Sala
# ──────────────────────────────────────────
class PainelSala(discord.ui.View):
    def __init__(self, sala_id: str, senha: str, nome: str, tempo: int):
        super().__init__(timeout=None)
        self.sala_id = sala_id
        self.senha = senha
        self.nome = nome
        self.tempo = tempo
        self.contador = 0
        self.go_iniciado = False
        self.message = None

    async def iniciar_contador(self):
        while self.contador < self.tempo and not self.go_iniciado:
            await asyncio.sleep(1)
            self.contador += 1
            await self.atualizar_embed()

    async def atualizar_embed(self):
        if self.message:
            embed = self.criar_embed()
            await self.message.edit(embed=embed, view=self)

    def criar_embed(self):
        restante = self.tempo - self.contador
        minutos = restante // 60
        segundos = restante % 60

        progresso = int((self.contador / self.tempo) * 20) if self.tempo > 0 else 0
        barra = "🟩" * progresso + "⬛" * (20 - progresso)

        embed = discord.Embed(
            title="🎮 Sala Free Fire Criada!",
            color=0xFF6600
        )
        embed.add_field(name="🏷️ Nome da Sala", value=f"`{self.nome}`", inline=True)
        embed.add_field(name="🔒 Senha", value=f"`{self.senha}`", inline=True)
        embed.add_field(name="🔑 ID da Sala", value=f"`{self.sala_id}`", inline=True)

        if self.go_iniciado:
            embed.add_field(name="🚀 Status", value="**✅ GO INICIADO!**", inline=False)
        else:
            embed.add_field(
                name=f"⏱️ Tempo para GO: `{minutos:02d}:{segundos:02d}`",
                value=barra,
                inline=False
            )

        embed.set_footer(text="🤖 Bot Free Fire • Use os botões abaixo")
        return embed

    @discord.ui.button(label="📋 Copiar ID", style=discord.ButtonStyle.blurple, custom_id="copiar_id")
    async def copiar_id(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"🔑 ID da Sala: ```{self.sala_id}```",
            ephemeral=True
        )

    @discord.ui.button(label="🚀 Dar GO", style=discord.ButtonStyle.green, custom_id="dar_go")
    async def dar_go(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.go_iniciado = True

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{API_URL}/criar-sala") as resp:
                    pass
            except:
                pass

        button.disabled = True
        button.label = "✅ GO!"
        await self.atualizar_embed()

# ──────────────────────────────────────────
# ⚙️ MODAL - Configurações da Sala
# ──────────────────────────────────────────
class ConfigModal(discord.ui.Modal, title="⚙️ Configurar Sala"):
    nome_sala = discord.ui.TextInput(
        label="🏷️ Nome da Sala",
        placeholder="Ex: MinhaRooms (deixe vazio para automático)",
        required=False,
        max_length=30
    )
    senha_sala = discord.ui.TextInput(
        label="🔒 Senha da Sala",
        placeholder="Padrão: 22",
        required=False,
        max_length=20,
        default="22"
    )
    tempo_sala = discord.ui.TextInput(
        label="⏱️ Tempo para GO (em minutos)",
        placeholder="Padrão: 5",
        required=False,
        max_length=3,
        default="5"
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        nome = self.nome_sala.value or f"sala{discord.utils.utcnow().microsecond % 1000}"
        senha = self.senha_sala.value or "22"
        tempo_min = int(self.tempo_sala.value or "5")

        async with aiohttp.ClientSession() as session:
            await session.post(f"{API_URL}/config/nome", json={"nome": nome})
            await session.post(f"{API_URL}/config/senha", json={"senha": senha})
            await session.post(f"{API_URL}/config/tempo", json={"tempo": tempo_min})
            await session.post(f"{API_URL}/criar-sala")
            async with session.get(f"{API_URL}/sala/id") as resp:
                sala_id = await resp.json()

        await interaction.followup.send("✅ Sala configurada e criada!", ephemeral=True)

        tempo_seg = tempo_min * 60
        view = PainelSala(
            sala_id=str(sala_id),
            senha=senha,
            nome=nome,
            tempo=tempo_seg
        )

        embed = view.criar_embed()
        msg = await interaction.channel.send(embed=embed, view=view)
        view.message = msg

        bot.loop.create_task(view.iniciar_contador())

# ──────────────────────────────────────────
# 🎮 SLASH COMMAND - /criar-sala
# ──────────────────────────────────────────
@bot.tree.command(name="criar-sala", description="🎮 Cria uma sala no Free Fire")
async def criar_sala(interaction: discord.Interaction):
    await interaction.response.send_modal(ConfigModal())

# ──────────────────────────────────────────
# ✅ ON READY
# ──────────────────────────────────────────
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot conectado como {bot.user}")
    print(f"📡 Slash commands sincronizados!")

bot.run(TOKEN)