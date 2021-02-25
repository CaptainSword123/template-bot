import discord
import asyncio
import datetime
import os


intents = discord.Intents.all()
client = discord.Client(intents=intents)

reaction_emoji = "\U0001F4DD"  # Der Emoji, zur Zeit: 📝

server_id = int(os.environ.get("SERVER_ID"))
if os.environ.get("SUP_ID") is not None:
    supporter_rolle = int(os.environ.get("SUP_ID"))                                 #Die ID der Rolle, die gepingt werden soll

    support_voice_channel = int(os.environ.get("SVC"))                              #Die ID des Support *Voicechannels*, der beim betreten eine Benachrichtigung auslösen soll
    support_text_channel = int(os.environ.get("STC"))                                 #Die ID des Support *Textchannels*, in den die Benachrichtigung gesendet werden soll

    acitve_support_channels = []
    for i in str(os.environ.get("ASC")).replace(" ", "").split(","):
        acitve_support_channels.append(int(i))

active_clients = {}

invites = {}

lila = hex(int(str(os.environ.get("COL")).replace("#", ""), 16))

@client.event
async def on_ready():
    if os.environ.get("SUP_ID") is not None:
        global v, t, a
        v = client.get_channel(support_voice_channel)
        t = client.get_channel(support_text_channel)
        a = []
        for id in acitve_support_channels:
            a.append(client.get_channel(id))

        #Aufnehmen vergangener Messages nach einem Neustart
        history = await t.history(limit=100).flatten()
        for msg in history:
            if msg.author == client.user and msg.content.__contains__("@"):
                user = client.get_user(int(msg.embeds[0].description.split("(")[1].split(")")[0]))
                if user in v.members:
                    active_clients[user.id] = msg.id
                else:
                    embed = discord.Embed(title="Supportwarteraum verlassen", description=msg.embeds[0].description, color=0xff0000)
                    embed.set_author(name=msg.embeds[0].author.name, icon_url=msg.embeds[0].author.icon_url)
                    await msg.edit(content=None, embed=embed)
    if os.environ.get("RMI") is not None:
        reac = False
        reac_msg = await client.get_channel(reac_channel_id).fetch_message(reac_message_id)
        for r in reac_msg.reactions:
            if r.me and r.emoji == reaction_emoji:
                reac = True
                break
        if not reac:
            await reac_msg.add_reaction(reaction_emoji)
    for i in await client.get_guild(server_id).invites():
        invites[i.code] = i.uses

@client.event
async def on_member_join(member):
    if os.environ.get("WELCOME") is not None:
        embed = discord.Embed(title="Willkommen", description="auf dem Vize Server " + member.mention, color=lila, timestamp=datetime.datetime.now())
        embed.set_author(name=member.name, icon_url=member.avatar_url)
        newinvites = await member.guild.invites()
        invite = ""
        for i in newinvites:
            if i.code in invites:
                if i.uses > invites[i.code]:
                    invite = i
        invites.clear()
        for i in newinvites:
            invites[i.code] = i.uses
        if invite != "":
            embed.set_footer(text="Eingeladen von " + invite.inviter.name + "#" + invite.inviter.discriminator)
        await client.get_channel(int(os.environ.get("WELCOME"))).send(content=None, embed=embed)

msg_bools = []
@client.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content == ".newmsg":
        if client.get_guild(server_id).get_role(int(os.environ.get("EMBED"))) in message.author.roles:
            msg_bools.append(False)
            bool_id = len(msg_bools) - 1
            pro = 0
            msg_fragen = ["In welchen Channel soll die Nachricht gesendet werden?", "Welchen Titel soll der Embed haben?", "Was soll im Embed stehen?", "Welches Bild soll der Embed haben?", "Welche Farbe soll der Embed haben?", "Welchen footer soll der Embed haben?"]
            msg_zusatz = ["", "\n\n`n`: Keinen Titel", "", "\n\nBitte den link zum Bild schicken\n`n`: Kein Bild", str(os.environ.get("COL_T")), "\n\nDas ist der kleine Text ganz unten\n`n`: Kein footer"]
            msg_titel = ["Channel", "Titel", "Inhalt", "Bild", "Farbe", "Footer"]
            msg_ans = []
            await message.delete()
            embed = discord.Embed(title="Custom Message über den Bot senden",
                                  description="**In welchen Channel soll die Nachricht gesendet werden?**",
                                  color=lila)
            embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
            embed.set_footer(text="Zum abbrechen auf das \u274C klicken. Der Vorgang wird nach 10 Minuten ohne Antwort automatisch beendet")
            msg = await message.channel.send(embed=embed)
            await msg.add_reaction("\u274C")
            loop = asyncio.get_event_loop()
            loop.create_task(msg_abbruch(msg, message.author, bool_id))
            def check(m):
                return m.channel == message.channel and m.author == message.author
            async def getans(sel, stan=None):
                if not msg_bools[bool_id]:
                    try:
                        ans = await client.wait_for("message", timeout=600.0, check=check)
                        if not msg_bools[bool_id]:
                            if sel:
                                if ans.content == "n":
                                    back = None
                                elif ans.content == "s":
                                    back = stan
                                else:
                                    back = ans.content
                            else:
                                back = ans.content
                            await ans.delete()
                            msg_ans.append(back)
                            await rendermsg()
                            return back
                    except:
                        embed = discord.Embed(title="Custom Message abgebrochen",
                                              description="Die Nachricht wird nicht versendet, da du 10 Minuten lang nicht reagiert hast",
                                              color=0xe74c3c)
                        embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
                        await msg.edit(embed=embed)
                        await msg.remove_reaction("\u274C", message.guild.me)
                        return
            async def rendermsg():
                embed = discord.Embed(title="Custom Message über den Bot senden",
                                      description="**" + msg_fragen[pro+1] + "**" + msg_zusatz[pro+1],
                                      color=lila)
                for i in range(pro+1):
                    if len(msg_ans[i].__str__()) > 500:
                        v = msg_ans[i].__str__()[:-(len(msg_ans[i].__str__())-500)] + "..."
                        embed.add_field(name=msg_titel[i],value=v,inline=False)
                    else:
                        embed.add_field(name=msg_titel[i],value=msg_ans[i],inline=False)
                embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
                embed.set_footer(text="Zum abbrechen auf das \u274C klicken. Der Vorgang wird nach 10 Minuten ohne Antwort automatisch beendet")
                await msg.edit(embed=embed)
            channel = await getans(False)
            try:
                l = client.get_channel(int(channel.__str__()[2:-1]))
            except:
                embed = discord.Embed(title="Custom Message abgebrochen",
                                      description="Ich konnte den Channel " + channel + " leider nicht finden, versuch es erneut",
                                      color=0xe74c3c)
                embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
                await msg.edit(embed=embed)
                await msg.remove_reaction("\u274C", message.guild.me)
                return
            pro = pro + 1
            titel = await getans(True)
            pro = pro + 1
            inhalt = await getans(False)
            pro = pro + 1
            bild = await getans(True)
            pro = pro + 1
            farbe = await getans(True, stan=str(os.environ.get("COL")))
            footer = await getans(True)
            embed = discord.Embed(title="Custom Message über den Bot senden",
                                  description="Soll die Nachricht so abgeschickt werden?\n\n**Bestätige** mit \u2705\n**Abbruch** mit \u274C",
                                  color=lila)
            for i in range(pro + 2):
                if len(msg_ans[i].__str__()) > 500:
                    v = msg_ans[i].__str__()[:-(len(msg_ans[i].__str__())-500)] + "..."
                    embed.add_field(name=msg_titel[i],value=v,inline=False)
                else:
                    embed.add_field(name=msg_titel[i],value=msg_ans[i],inline=False)
            embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
            embed.set_footer(text="Nach 10 Minuten wird der Vorgang automatisch abgebrochen")
            await msg.edit(embed=embed)
            await msg.remove_reaction("\u274C", message.guild.me)
            await msg.add_reaction("\u2705")
            await msg.add_reaction("\u274C")
            def check_r(reaction, user):
                return user == message.author and reaction.message.id == msg.id
            try:
                reaction, user = await client.wait_for("reaction_add", timeout=600.0, check=check_r)
                if reaction.emoji == "\u2705":
                    if farbe is not None:
                        embed = discord.Embed(title=titel, description=inhalt, color=int(farbe.replace("#", "0x"), 16))
                    else:
                        embed = discord.Embed(title=titel, description=inhalt, color=0x2f3136)
                    if bild is not None:
                        embed.set_thumbnail(url=bild)
                    if footer is not None:
                        embed.set_footer(text=footer)
                    await client.get_channel(int(channel.__str__()[2:-1])).send(embed=embed)
                    embed = discord.Embed(title="Custom Message über den Bot versendet",
                                          description="Nachricht versendet!",
                                          color=0x2ecc71)
                    for i in range(pro + 2):
                        if len(msg_ans[i].__str__()) > 500:
                            v = msg_ans[i].__str__()[:-(len(msg_ans[i].__str__())-500)] + "..."
                            embed.add_field(name=msg_titel[i],value=v,inline=False)
                        else:
                            embed.add_field(name=msg_titel[i],value=msg_ans[i],inline=False)
                    embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
                    await msg.edit(embed=embed)
                    await msg.remove_reaction("\u2705", message.guild.me)
                    await msg.remove_reaction("\u274C", message.guild.me)
                    await msg.remove_reaction("\u2705", message.author)
                else:
                    embed = discord.Embed(title="Custom Message abgebrochen",
                                          description="Die Nachricht wird nicht versendet",
                                          color=0xe74c3c)
                    embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
                    await msg.edit(embed=embed)
                    await msg.remove_reaction("\u2705", message.guild.me)
                    await msg.remove_reaction("\u274C", message.guild.me)
                    await msg.remove_reaction("\u274C", message.author)
            except:
                raise
                embed = discord.Embed(title="Custom Message abgebrochen",
                                      description="Die Nachricht wird nicht versendet, da du 10 Minuten lang nicht reagiert hast",
                                      color=0xe74c3c)
                embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
                await msg.edit(embed=embed)
                await msg.remove_reaction("\u2705", message.guild.me)
                await msg.remove_reaction("\u274C", message.guild.me)

async def msg_abbruch(msg, member, bool_id):
    def check(reaction, user):
        return reaction.message.id == msg.id and user == member and reaction.emoji == "\u274C"
    try:
        reaction, user = await client.wait_for("reaction_add", timeout=600.0, check=check)
        embed = discord.Embed(title="Custom Message abgebrochen",
                              description="Die Nachricht wird nicht versendet",
                              color=0xe74c3c)
        embed.set_author(name=member.name, icon_url=member.avatar_url)
        await msg.remove_reaction("\u274C", client.user)
        await msg.remove_reaction("\u274C", member)
        await msg.edit(embed=embed)
        msg_bools[bool_id] = True
    except:
        pass

if os.environ.get("SUP_ID") is not None:
    @client.event
    async def on_voice_state_update(member, before, after):
        #Überprüfen, ob der Support channel betreten wurde
        if before.channel != v and after.channel == v:
            embed = discord.Embed(title="Support benötigt", description="%s(%s)" % (member.mention, member.id), color=lila)
            embed.set_author(name=member.name, icon_url=member.avatar_url)
            embed.set_footer(text="Zum annehmen den User moven")
            msg = await t.send(content=client.get_guild(server_id).get_role(supporter_rolle).mention, embed=embed)
            #await msg.add_reaction(emoji="✅")
            active_clients[member.id] = msg.id

        #Überprüfen, ob der Support channel verlassen wurde
        elif before.channel == v and after.channel != v and member.id in active_clients:
            msg = await t.fetch_message(active_clients[member.id])
            if after.channel in a:
                if len(after.channel.members) == 2:
                    if after.channel.members[0] != member:
                        add = "\nAngenommen von " + after.channel.members[0].mention
                    else:
                        add = "\nAngenommen von " + after.channel.members[1].mention
                else:
                    add = ""
                embed = discord.Embed(title="Support angenommen", description=("%s(%s)%s" % (member.mention, member.id, add)), color=0x00ff00)
                embed.set_author(name=member.name, icon_url=member.avatar_url)
                await msg.edit(content=None, embed=embed)
            else:
                embed = discord.Embed(title="Supportwarteraum verlassen", description=("%s(%s)" % (member.mention, member.id)), color=0xff0000)
                embed.set_author(name=member.name, icon_url=member.avatar_url)
                await msg.edit(content=None, embed=embed)
            #await msg.remove_reaction("✅", client.user)
            del active_clients[member.id]



"""Diese Sachen musst du anpassen"""
if os.environ.get("RMI") is not None:
    reac_message_id = int(os.environ.get("RMI"))   # Die ID der Nachricht auf die reagiert wird
    reac_channel_id = int(os.environ.get("RCI"))  # Die ID des Channels in dem die Nachricht ist
    fragen = []
    for f in str(os.environ.get("FRAGEN")).split(";"):
        fragen.append(f)
    einführungstext = str(os.environ.get("ET"))
    r_ids = []
    for r in str(os.environ.get("ROLE_ID")).split(";"):
        r_ids.append(int(r))
    bewerberrolle = str(os.environ.get("BR"))

    """Ab hier nichts mehr verändern, höchstens einen Text"""
    bools = []


    @client.event
    async def on_raw_reaction_add(payload):
        try:
            if not payload.member.bot:
                if payload.message_id == reac_message_id:
                    reac_msg = await client.get_channel(reac_channel_id).fetch_message(reac_message_id)
                    await reac_msg.remove_reaction(payload.emoji.name, payload.member)
                    if payload.emoji.name == reaction_emoji:
                        bools.append(False)
                        bool_id = len(bools) - 1
                        embed = discord.Embed(title="Bewerbung",
                                              description=einführungstext + "\n\nWenn du den Berwerbungsvorgang abbrechen willst, kannst du auf das \u274C klicken",
                                              color=lila)
                        embed.set_author(name=reac_msg.guild.name, icon_url=reac_msg.guild.icon_url)
                        await payload.member.send(embed=embed)

                        def check(m):
                            return m.channel == discord.utils.get(client.get_all_members(), id=payload.member.id).dm_channel

                        antworten = []
                        loop = asyncio.get_event_loop()
                        for i in range(len(fragen)):
                            if not bools[bool_id]:
                                embed = discord.Embed(title="Frage " + str((i + 1)),
                                                      description=fragen[i],
                                                      color=lila)
                                embed.set_author(name=reac_msg.guild.name, icon_url=reac_msg.guild.icon_url)
                                embed.set_footer(
                                    text="Wenn ich nach 10 Minuten keine Antwort erhalte, wird die Bewerbung abgebrochen")
                                msg = await payload.member.send(embed=embed)
                                await msg.add_reaction("\u274C")
                                loop.create_task(abbruch(msg, payload.member.id, payload.member.guild, bool_id))
                                try:
                                    ans = await client.wait_for("message", timeout=600.0, check=check)
                                    if bools[bool_id]:
                                        return
                                    antworten.append(ans.content)
                                    await msg.remove_reaction("\u274C", client.user)
                                    embed = discord.Embed(title="Frage " + str((i + 1)),
                                                          description=fragen[i] + "\n\n" + ans.content,
                                                          color=0x2ecc71)
                                    embed.set_author(name=reac_msg.guild.name, icon_url=reac_msg.guild.icon_url)
                                    await msg.edit(embed=embed)
                                except:
                                    if bools[bool_id]:
                                        return
                                    embed = discord.Embed(title="Bewerbungsvorgang abgebrochen",
                                                          description="Du hast 10 Minuten nicht geantwortet. Deine Berwerbung wurde deshalb automatisch abgebrochen. Du kannst dich jederzeit nocheinmal berwerben!",
                                                          color=0xe74c3c)
                                    embed.set_author(name=reac_msg.guild.name, icon_url=reac_msg.guild.icon_url)
                                    await msg.remove_reaction("\u274C", client.user)
                                    await msg.edit(embed=embed)
                                    return
                        embed = discord.Embed(title="Deine Bewerbung",
                                              description="Lies dir deine Bewerbung noch einaml durch, wenn du sie absenden willst, klick auf \u2705, wenn nicht, dann auf \u274C",
                                              color=lila)
                        embed.set_author(name=reac_msg.guild.name, icon_url=reac_msg.guild.icon_url)
                        for i in range(len(fragen)):
                            embed.add_field(name=fragen[i], value=antworten[i], inline=False)
                        embed.set_footer(
                            text="Wenn ich nach 10 Minuten keine Antwort erhalte, wird die Bewerbung abgebrochen")
                        msg = await payload.member.send(embed=embed)
                        await msg.add_reaction("\u2705")
                        await msg.add_reaction("\u274C")

                        def check_r(reaction, user):
                            return reaction.message.id == msg.id and user == discord.utils.get(client.get_all_members(),
                                                                                               id=payload.member.id)

                        try:
                            reaction, user = await client.wait_for("reaction_add", timeout=600.0, check=check_r)

                            if reaction.emoji == "\u2705":
                                embed = discord.Embed(title="Eingehende Bewerbung",
                                                      description=payload.member.mention + " hat sich mit diesen antworten beworben:",
                                                      color=lila)
                                embed.set_author(name=payload.member.name, icon_url=payload.member.avatar_url)
                                for i in range(len(fragen)):
                                    embed.add_field(name=fragen[i], value=antworten[i], inline=False)
                                for a in client.get_guild(server_id).members:
                                    for r in a.roles:
                                        if r.id in r_ids:
                                            try:
                                                await a.send(embed=embed)
                                            except:
                                                pass
                                            break
                                embed = discord.Embed(title="Bewerbung erfolgreich eingereicht",
                                                      description="Deine Berwerbung wurde erfolgreich abgeschickt, du wirst bald von uns hören.",
                                                      color=0x2ecc71)
                                embed.set_author(name=reac_msg.guild.name, icon_url=reac_msg.guild.icon_url)
                                for i in range(len(fragen)):
                                    embed.add_field(name=fragen[i], value=antworten[i], inline=False)
                                await msg.edit(embed=embed)
                                await payload.member.add_roles(
                                    discord.utils.get(payload.member.guild.roles, id=bewerberrolle))
                            else:
                                embed = discord.Embed(title="Bewerbungsvorgang abgebrochen",
                                                      description="Du hast die Bewerbung abgebrochen. Du kannst dich jederzeit nocheinmal berwerben!",
                                                      color=0xe74c3c)
                                embed.set_author(name=reac_msg.guild.name, icon_url=reac_msg.guild.icon_url)
                                await msg.remove_reaction("\u274C", client.user)
                                await msg.remove_reaction("\u2705", client.user)
                                await msg.edit(embed=embed)
                                return
                        except:
                            raise
                            embed = discord.Embed(title="Bewerbungsvorgang abgebrochen",
                                                  description="Du hast 10 Minuten nicht geantwortet. Deine Berwerbung wurde deshalb automatisch abgebrochen. Du kannst dich jederzeit nocheinmal berwerben!",
                                                  color=0xe74c3c)
                            embed.set_author(name=reac_msg.guild.name, icon_url=reac_msg.guild.icon_url)
                            await msg.remove_reaction("\u274C", client.user)
                            await msg.remove_reaction("\u2705", client.user)
                            await msg.edit(embed=embed)
                            return
        except:
            pass



    async def abbruch(msg, member_id, guild, bool_id):
        def check(reaction, user):
            return reaction.message.id == msg.id and user == discord.utils.get(client.get_all_members(),
                                                                               id=member_id) and reaction.emoji == "\u274C"

        try:
            reaction, user = await client.wait_for("reaction_add", timeout=600.0, check=check)
            embed = discord.Embed(title="Bewerbungsvorgang abgebrochen",
                                  description="Du hast die Bewerbung abgebrochen. Du kannst dich jederzeit nocheinmal berwerben!",
                                  color=0xe74c3c)
            embed.set_author(name=guild.name, icon_url=guild.icon_url)
            await msg.remove_reaction("\u274C", client.user)
            await msg.remove_reaction("\u2705", client.user)
            await msg.edit(embed=embed)
            bools[bool_id] = True
        except:
            pass


client.run(str(os.environ.get("BOT_TOKEN")))
