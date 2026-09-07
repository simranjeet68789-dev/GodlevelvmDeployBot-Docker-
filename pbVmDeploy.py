import discord
from discord.ext import commands
from discord import ui
import docker
import sqlite3
import random
import string
import datetime
import asyncio
import logging

# ================= [ 🚀 BN-HOST CONFIGURATION ] =================
TOKEN = "YOUR_BOT_TOKEN_HERE"
ADMIN_IDS = [1210291131301101618]
PREFIX = "!"

BRAND = "Bn-Host"
DEV = "Developed by Pythonboyz"
VPS_COST = 2
RAM_LIMIT = "64g"

# ANSI ULTRA-COLORS
R = "\u001b[0;31m"    # Red
G = "\u001b[0;32m"    # Green
B = "\u001b[0;34m"    # Blue
C = "\u001b[0;36m"    # Cyan
Y = "\u001b[1;33m"    # Bold Yellow
W = "\u001b[0;37m"    # White
RE = "\u001b[0m"      # Reset

logging.basicConfig(level=logging.INFO)

# ================= [ 🏦 DATA CORE ] =================
class DataCore:
    def __init__(self):
        self.conn = sqlite3.connect('bn_ultimate.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users 
            (user_id TEXT PRIMARY KEY, coins INTEGER DEFAULT 0, invites INTEGER DEFAULT 0)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS vps 
            (vps_id TEXT PRIMARY KEY, container_id TEXT, owner_id TEXT, os TEXT, pwd TEXT)''')
        self.conn.commit()

    def sync(self, uid):
        self.cursor.execute("SELECT coins, invites FROM users WHERE user_id = ?", (str(uid),))
        res = self.cursor.fetchone()
        if not res:
            self.cursor.execute("INSERT INTO users VALUES (?, 0, 0)", (str(uid),))
            self.conn.commit()
            return 0, 0
        return res

    def reward(self, uid):
        self.cursor.execute("UPDATE users SET coins = coins + 1, invites = invites + 1 WHERE user_id = ?", (str(uid),))
        self.conn.commit()

    def charge(self, uid):
        self.cursor.execute("UPDATE users SET coins = coins - ? WHERE user_id = ?", (VPS_COST, str(uid)))
        self.conn.commit()

db = DataCore()

# ================= [ 🖥️ UI COMPONENTS ] =================

class OSSelect(ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = [
            discord.SelectOption(label="Ubuntu 22.04 LTS", description="High-Speed Infrastructure", emoji="🐧", value="ubuntu:22.04"),
            discord.SelectOption(label="Debian 12 Pro", description="Stable Enterprise OS", emoji="🌀", value="debian:12"),
            discord.SelectOption(label="Alpine X-Light", description="Ultra Lightweight", emoji="🏔️", value="alpine:latest")
        ]
        super().__init__(placeholder="⚡ CHOOSE CLOUD ARCHITECTURE...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await self.bot.get_cog('Engine').provision_vps(interaction, self.values[0])

# ================= [ ⚙️ THE "ULTIMATE" DEPLOY ENGINE ] =================

class Engine(commands.Cog):
    def __init__(self, bot): self.bot = bot

    async def provision_vps(self, interaction: discord.Interaction, image: str):
        await interaction.response.defer(ephemeral=True)
        vps_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        pwd = ''.join(random.choices(string.ascii_letters + string.digits, k=15))
        
        # --- ALAG LEVEL KA ANIMATION START ---
        msg = await interaction.followup.send(f"```ansi\n{R}[!] INITIALIZING BN-HOST HYPER-CORE...{RE}\n```")
        
        frames = [
            f"{C}Establishing Neural Uplink...{RE}",
            f"{C}Accessing Hardware Layer...{RE}\n{Y}Detected: 2GB Host Machine{RE}",
            f"{C}Executing RAM Overclock Bypass...{RE}\n{G}Memory Set: 64.00 GB Dedicated{RE}",
            f"{C}Pulling Molecular OS Layers...{RE}\n{W}Progress: [██████░░░░░░░░░░] 30%{RE}",
            f"{C}Injecting Pythonboyz Security...{RE}\n{W}Progress: [████████████░░░░░░] 60%{RE}",
            f"{C}Establishing Quantum Tunnel...{RE}\n{W}Progress: [██████████████████░░] 90%{RE}",
            f"{G}FINALIZING NODE VIRTUALIZATION...{RE}\n{W}Progress: [████████████████████] 100%{RE}"
        ]

        current_text = ""
        for frame in frames:
            current_text += f"\n{frame}"
            terminal = (
                f"```ansi\n"
                f"{B}╔═══════════════════════════════════════════════╗{RE}\n"
                f"  {Y}SYSTEM DEPLOYMENT: NODE-{vps_id}{RE}\n"
                f"  {W}{DEV}{RE}\n"
                f"{B}╚═══════════════════════════════════════════════╝{RE}\n"
                f"{current_text}\n"
                f"```"
            )
            await msg.edit(content=terminal)
            await asyncio.sleep(1.2)

        try:
            # Docker 64GB Allocation
            container = self.bot.docker.containers.run(
                image, detach=True, privileged=True, mem_limit=RAM_LIMIT,
                nano_cpus=4 * 1000000000, name=f"BN_{vps_id}",
                hostname=f"bnhost-{vps_id.lower()}", command="tail -f /dev/null",
                restart_policy={"Name": "always"}
            )
            
            # Setup SSH
            setup = f"apt-get update && apt-get install -y openssh-server tmate && echo 'root:{pwd}' | chpasswd && service ssh start"
            container.exec_run(["/bin/bash", "-c", setup])
            
            # Billing
            if interaction.user.id not in ADMIN_IDS: db.charge(interaction.user.id)
            
            db.cursor.execute("INSERT INTO vps VALUES (?,?,?,?,?)", (vps_id, container.id, str(interaction.user.id), image, pwd))
            db.conn.commit()

            # Final Flash
            final_embed = discord.Embed(title="🌌 BN-HOST | CLOUD ONLINE", color=0x00ffff)
            final_embed.description = f"**{vps_id}** is now broadcasting from the cloud."
            final_embed.add_field(name="💾 MEMORY", value="`64 GB DEDICATED`", inline=True)
            final_embed.add_field(name="⚡ CPU", value="`4 vCPU CORES`", inline=True)
            final_embed.add_field(name="🔑 ACCESS", value=f"User: `root` \nPass: ||`{pwd}`||", inline=False)
            final_embed.set_footer(text=f"{DEV} | God-Level Hosting")
            
            await msg.edit(content=None, embed=final_embed)
            await interaction.user.send(f"🎉 **Instance `{vps_id}` has been provisioned!**", embed=final_embed)

        except Exception as e:
            await msg.edit(content=f"```ansi\n{R}[ERROR] DEPLOYMENT FAILED: {e}{RE}\n```")

# ================= [ 👑 BOT SYSTEM ] =================

class BnHostBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members, intents.message_content, intents.invites = True, True, True
        super().__init__(command_prefix=PREFIX, intents=intents, help_command=None)
        self.docker = docker.from_env()
        self.invite_map = {}

    async def on_ready(self):
        for guild in self.guilds:
            try: self.invite_map[guild.id] = await guild.invites()
            except: pass
        print(f"✅ Bn-Host God-Level Online | {DEV}")

bot = BnHostBot()

@bot.command()
async def help(ctx):
    embed = discord.Embed(title=f"👑 {BRAND} TERMINAL", color=0x2b2d31)
    embed.description = f"**{DEV}**\n\n`{PREFIX}deploy` - New 64GB Instance\n`{PREFIX}balance` - Check Credits\n`{PREFIX}invite` - Get Coins"
    embed.add_field(name="💎 PRICING", value=f"1 Invite = 1 Coin\n1 VPS = {VPS_COST} Coins", inline=True)
    embed.set_footer(text=DEV)
    await ctx.send(embed=embed)

@bot.command()
async def balance(ctx):
    coins, invites = db.sync(ctx.author.id)
    status = "∞ (Admin)" if ctx.author.id in ADMIN_IDS else f"{coins} Coins"
    embed = discord.Embed(title="💳 CLOUD WALLET", color=0x00ffff)
    embed.add_field(name="Balance", value=f"```fix\n{status}\n```", inline=True)
    embed.add_field(name="Invites", value=f"```fix\n{invites}\n```", inline=True)
    embed.set_footer(text=DEV)
    await ctx.send(embed=embed)

@bot.command()
async def deploy(ctx):
    coins, _ = db.sync(ctx.author.id)
    if ctx.author.id not in ADMIN_IDS and coins < VPS_COST:
        return await ctx.send(f"❌ Need **{VPS_COST} Coins** (2 Invites).")
    
    view = ui.View()
    view.add_item(OSSelect(bot))
    await ctx.send(f"⚙️ **{BRAND} ENGINE:** Choose architecture.", view=view)

@bot.event
async def on_member_join(member):
    try:
        prev = bot.invite_map.get(member.guild.id)
        curr = await member.guild.invites()
        bot.invite_map[member.guild.id] = curr
        for i in prev:
            for n in curr:
                if i.code == n.code and i.uses < n.uses:
                    db.reward(i.inviter.id)
                    return
    except: pass

async def main():
    await bot.add_cog(Engine(bot))
    async with bot: await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())