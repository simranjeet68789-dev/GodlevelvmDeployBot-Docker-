import discord
from discord.ext import commands, tasks
from discord import ui
import asyncio, random, string, sqlite3, time, datetime, os, psutil, docker, re

# ================= [ 💎 CONFIGURATION & BRANDING ] =================
TOKEN = "MTU0NjgxMzYzNzA5ODczMzYxOA.GAn_su.TTuivC9MnPIWk4w-50xoRfU9qIWZtzLA_N1TdM"
PREFIX = "?" # Aapka prefix '?' hai
ADMIN_IDS = [1545006484574830713] # Aapki Owner ID
WHITELIST = ADMIN_IDS.copy()
BRAND = "Bn-Host GodLevel"
DEV_TAG = "Developed by PythonBoyz"

# VPS GOD-SPECS
VPS_COST = 2
RAM_LIMIT = "64g"
CPU_CORES = 8
DISK_SPACE = "200GB"

# ANSI ULTRA-COLORS
R, G, B, C, Y, W, P, RE = "\u001b[0;31m", "\u001b[0;32m", "\u001b[0;34m", "\u001b[0;36m", "\u001b[1;33m", "\u001b[0;37m", "\u001b[0;35m", "\u001b[0m"

# ================= [ 🏦 SECURE DATA CORE ] =================
class DataCore:
    def __init__(self):
        self.conn = sqlite3.connect('bnhost_ultimate.db', check_same_thread=False)
        self.cur = self.conn.cursor()
        self.cur.execute('CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, coins INT DEFAULT 0, invs INT DEFAULT 0)')
        self.cur.execute('CREATE TABLE IF NOT EXISTS vps (v_id TEXT, c_id TEXT, owner TEXT, os TEXT, pwd TEXT)')
        self.conn.commit()

    def sync_user(self, uid):
        self.cur.execute("SELECT coins, invs FROM users WHERE id = ?", (str(uid),))
        res = self.cur.fetchone()
        if not res:
            self.cur.execute("INSERT INTO users VALUES (?, 0, 0)", (str(uid),))
            self.conn.commit()
            return 0, 0
        return res

    def add_credit(self, uid):
        self.cur.execute("UPDATE users SET coins = coins + 1, invs = invs + 1 WHERE id = ?", (str(uid),))
        self.conn.commit()

    def deduct(self, uid):
        self.cur.execute("UPDATE users SET coins = coins - ? WHERE id = ?", (VPS_COST, str(uid)))
        self.conn.commit()

db = DataCore()
docker_client = docker.from_env()

# ================= [ 🛰️ VM HYPERVISOR GUI ] =================

class VMManager(ui.View):
    def __init__(self, v_id, c_id, owner):
        super().__init__(timeout=None)
        self.v_id, self.c_id, self.owner = v_id, c_id, owner

    async def secure_edit(self, interaction, status, color):
        embed = discord.Embed(title=f"🛰️ INSTANCE CONTROL | {self.v_id}", color=color)
        embed.add_field(name="📡 Node Status", value=f"```ansi\n{G}{status}{RE}\n```")
        embed.add_field(name="🧬 Resources", value=f"```yaml\nRAM: {RAM_LIMIT}\nCPU: {CPU_CORES} Cores\nDisk: {DISK_SPACE}\n```", inline=False)
        embed.set_footer(text=DEV_TAG)
        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="START", style=discord.ButtonStyle.green, emoji="🚀")
    async def boot(self, interaction: discord.Interaction, btn: ui.Button):
        if str(interaction.user.id) != self.owner: return await interaction.response.send_message("❌ Not your VM!", ephemeral=True)
        docker_client.containers.get(self.c_id).start()
        await self.secure_edit(interaction, "SYSTEM ONLINE", 0x2ecc71)

    @ui.button(label="STOP", style=discord.ButtonStyle.red, emoji="🛑")
    async def shutdown(self, interaction: discord.Interaction, btn: ui.Button):
        if str(interaction.user.id) != self.owner: return await interaction.response.send_message("❌ Not your VM!", ephemeral=True)
        docker_client.containers.get(self.c_id).stop()
        await self.secure_edit(interaction, "SYSTEM SHUTDOWN", 0xe74c3c)

    @ui.button(label="SSHX ACCESS", style=discord.ButtonStyle.secondary, emoji="🔗")
    async def ssh_access(self, interaction: discord.Interaction, btn: ui.Button):
        if str(interaction.user.id) != self.owner: return await interaction.response.send_message("❌ Not your VM!", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        container = docker_client.containers.get(self.c_id)
        res = container.exec_run("tmate -S /tmp/tmate.sock display -p '#{tmate_ssh}'")
        link = res.output.decode().strip() or "Initializing SSH... wait 5s and try again."
        emb = discord.Embed(title="🛸 REMOTE SSHX ACCESS", description=f"Login link:\n`{link}`", color=0x00ffff)
        await interaction.followup.send(embed=emb, ephemeral=True)

# ================= [ 🚀 DEPLOYMENT UI COMPONENTS ] =================

class OSSelect(ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = [
            discord.SelectOption(label="Ubuntu 22.04 LTS", emoji="🐧", value="ubuntu:22.04"),
            discord.SelectOption(label="Debian 12 Pro", emoji="🌀", value="debian:12"),
            discord.SelectOption(label="Alpine Light", emoji="🏔️", value="alpine:latest")
        ]
        super().__init__(placeholder="⚡ SELECT ARCHITECTURE...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.bot.get_cog('VMEngine').provision(interaction, self.values[0])

# ================= [ ⚙️ DEPLOYMENT ENGINE ] =================

class VMEngine(commands.Cog):
    def __init__(self, bot): self.bot = bot

    async def provision(self, interaction, image):
        user_id = interaction.user.id
        is_admin = user_id in ADMIN_IDS
        coins, _ = db.sync_user(user_id)

        if not is_admin and coins < VPS_COST:
            return await interaction.followup.send(f"❌ **Low Balance:** Need {VPS_COST} coins.", ephemeral=True)

        v_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        pwd = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

        msg = await interaction.followup.send(f"```ansi\n{P}[!] INITIALIZING BN-HOST GOD-CORE...{RE}```")
        
        frames = [
            f"{C}📡 Neural Link: SUCCESS{RE}",
            f"{Y}⚡ Allocating {RAM_LIMIT} Dedicated RAM...{RE}",
            f"{Y}🔥 Parallelizing {CPU_CORES} vCPU Cores...{RE}",
            f"{G}🔒 Security Layer: GOD-MODE ACTIVE{RE}",
            f"{W}[████████████████████] 100%{RE}\n{G}DEPLOYMENT SUCCESSFUL!{RE}"
        ]
        
        terminal = ""
        for frame in frames:
            await asyncio.sleep(1)
            terminal += f"\n{frame}"
            await msg.edit(content=f"```ansi\n{terminal}\n```")

        try:
            container = docker_client.containers.run(
                image, detach=True, tty=True, privileged=True,
                mem_limit=RAM_LIMIT, nano_cpus=CPU_CORES * 1000000000,
                name=f"BN_{v_id}", command="tail -f /dev/null", restart_policy={"Name": "always"}
            )
            
            setup_cmd = f"apt-get update && apt-get install -y openssh-server tmate && echo 'root:{pwd}' | chpasswd && service ssh start"
            container.exec_run(["/bin/bash", "-c", setup_cmd])
            
            if not is_admin: db.deduct(user_id)
            db.cur.execute("INSERT INTO vps VALUES (?,?,?,?,?)", (v_id, container.id, str(user_id), image, pwd))
            db.conn.commit()

            final_emb = discord.Embed(title="🌌 BN-HOST | CLOUD NODE ONLINE", color=0x00ffff)
            final_emb.add_field(name="ID", value=f"`{v_id}`", inline=True)
            final_emb.add_field(name="ROOT ACCESS", value=f"User: `root` \nPass: ||`{pwd}`||", inline=False)
            final_emb.set_footer(text=DEV_TAG)
            await msg.edit(content=None, embed=final_emb)
        except Exception as e:
            await msg.edit(content=f"```ansi\n{R}[CRITICAL ERROR]: {e}{RE}\n```")

# ================= [ 📋 PROFESSIONAL HELP GUI ] =================

class HelpInterface(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Security", emoji="🛡️", description="Anti-Nuke & Anti-Link"),
            discord.SelectOption(label="Cloud VPS", emoji="🛰️", description="Deploy & Manage 64GB Nodes"),
            discord.SelectOption(label="Economy", emoji="💰", description="Earn Coins per Invite")
        ]
        super().__init__(placeholder="📂 ACCESS ENCRYPTED MODULES...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        val = self.values[0]
        embed = discord.Embed(title=f"💎 {val} System", color=0x2b2d31)
        if "Security" in val: embed.description = "`?antinuke`, `?antilink`, `?whitelist`"
        elif "Cloud" in val: embed.description = "`?deploy` - Create VM\n`?manage [ID]` - Manage VM"
        elif "Economy" in val: embed.description = "`?balance` - Check Coins\n`?invite` - 1 Invite = 1 Coin"
        
        embed.set_footer(text=DEV_TAG)
        await interaction.followup.send(embed=embed, ephemeral=True)

# ================= [ 👑 MASTER BOT CORE ] =================

class BnHostGod(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=PREFIX, intents=intents, help_command=None)
        self.invite_cache = {}

    async def on_ready(self):
        os.system('clear')
        for guild in self.guilds:
            try: self.invite_cache[guild.id] = await guild.invites()
            except: pass
        print(f"✅ Bn-Host GodLevel Online | {DEV_TAG}")

    async def on_member_join(self, member):
        try:
            old = self.invite_cache.get(member.guild.id)
            new = await member.guild.invites()
            self.invite_cache[member.guild.id] = new
            for o in old:
                for n in new:
                    if o.code == n.code and n.uses > o.uses:
                        db.add_credit(o.inviter.id)
                        return
        except: pass

bot = BnHostGod()

@bot.command()
async def deploy(ctx):
    view = ui.View(); view.add_item(OSSelect(bot))
    embed = discord.Embed(title="⚙️ VIRTUALIZATION HUB", description="Choose architecture to provision 64GB Node.", color=0x2b2d31)
    await ctx.send(embed=embed, view=view)

@bot.command()
async def help(ctx):
    view = ui.View(); view.add_item(HelpInterface())
    embed = discord.Embed(title="💎 Bn-Host Control Panel", color=0x2b2d31)
    embed.set_footer(text=DEV_TAG)
    await ctx.send(embed=embed, view=view)

@bot.command()
async def balance(ctx):
    coins, invs = db.sync_user(ctx.author.id)
    is_adm = "∞ (GOD)" if ctx.author.id in ADMIN_IDS else f"{coins}"
    embed = discord.Embed(title="💳 CLOUD WALLET", color=0x00ffff)
    embed.add_field(name="Balance", value=f"```ansi\n\u001b[0;34m{is_adm}\u001b[0m\n```", inline=True)
    embed.add_field(name="Invites", value=f"```ansi\n\u001b[0;34m{invs}\u001b[0m\n```", inline=True)
    embed.set_footer(text=DEV_TAG)
    await ctx.send(embed=embed)

@bot.command()
async def manage(ctx, v_id: str = None):
    if not v_id:
        res = db.cur.execute("SELECT v_id FROM vps WHERE owner = ?", (str(ctx.author.id),)).fetchall()
        ids = ", ".join([f"`{v[0]}`" for v in res]) if res else "None"
        return await ctx.send(f"❓ **Usage:** `{PREFIX}manage [ID]`\nYour Nodes: {ids}")
    
    data = db.cur.execute("SELECT * FROM vps WHERE v_id = ?", (v_id,)).fetchone()
    if not data or (data[2] != str(ctx.author.id) and ctx.author.id not in ADMIN_IDS):
        return await ctx.send("❌ Node not found or Access Denied.")
    
    embed = discord.Embed(title=f"🛰️ VM MANAGER: {v_id}", color=0x2b2d31)
    embed.add_field(name="Resource Plan", value="```yaml\nRAM: 64GB\nCPU: 8 Cores\n```")
    await ctx.send(embed=embed, view=VMManager(data[0], data[1], data[2]))

# ================= [ 🚀 STARTING ENGINE ] =================
async def run_bot():
    await bot.add_cog(VMEngine(bot))
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(run_bot())