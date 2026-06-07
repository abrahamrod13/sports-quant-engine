import discord
from discord.ext import commands
import subprocess
import asyncio
import os
from datetime import datetime

# Token se leerá desde variable de entorno en Render
TOKEN = os.environ.get("DISCORD_TOKEN")

# Configurar el bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    print(f"📅 Hora: {datetime.now()}")

@bot.command(name='picks')
async def get_picks(ctx):
    """Ejecuta el análisis de MLB y devuelve los picks"""
    await ctx.send("🔄 Procesando picks de MLB... esto puede tomar unos segundos...")
    
    try:
        result = subprocess.run(
            ["python", "run_live_mlb_v2.py"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        lines = result.stdout.split('\n')
        picks = []
        for line in lines:
            if line.startswith('MLB|') and 'HOME' not in line:
                parts = line.split('|')
                if len(parts) >= 8 and parts[3] != 'NO PICK':
                    picks.append({
                        'home': parts[1],
                        'away': parts[2],
                        'pick': parts[3],
                        'odds': parts[4],
                        'prob': parts[5],
                        'edge': parts[6],
                        'conf': parts[7]
                    })
        
        if picks:
            mensaje = "**⚾ MLB PICKS - HOY**\n\n"
            for p in picks:
                mensaje += f"🔥 **{p['pick']}**\n"
                mensaje += f"   📊 Prob: {p['prob']} | Edge: {p['edge']} | Odds: {p['odds']}\n"
                mensaje += f"   🏟️ {p['home']} vs {p['away']}\n\n"
            await ctx.send(mensaje)
        else:
            await ctx.send("⚠️ No hay picks que cumplan los criterios hoy (Edge > 8%).")
            
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name='ping')
async def ping(ctx):
    await ctx.send(f"🏓 Pong! Latencia: {round(bot.latency * 1000)}ms")

if __name__ == "__main__":
    bot.run(TOKEN)