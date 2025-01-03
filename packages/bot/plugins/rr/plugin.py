import discord
from discord.ext import commands

import logging; log = logging.getLogger()

from .. import AutoModPluginBlueprint, ShardedBotInstance
from ...types import Embed, Emote, Message



class ReactionRolesPlugin(AutoModPluginBlueprint):
    """Plugin for reaction roles"""
    def __init__(
        self, 
        bot: ShardedBotInstance
    ) -> None:
        super().__init__(bot)


    @AutoModPluginBlueprint.listener()
    async def on_raw_reaction_add(
        self, 
        payload: discord.RawReactionActionEvent
    ) -> None: 
        if f"{payload.user_id}" == f"{self.bot.user.id}": return
        if payload.member.bot == True: return

        rrs = self.db.configs.get(payload.guild_id, "reaction_roles")
        if not f"{payload.message_id}" in rrs: return

        data = rrs[f"{payload.message_id}"]
        if len(data["pairs"]) < 1: return

        if payload.emoji.id == None:
            possible_name = payload.emoji.name
        else:
            possible_name = f"<:{payload.emoji.name}:{payload.emoji.id}>"

        role_id = [list(x.values())[1] for x in data["pairs"] if list(x.values())[0] == possible_name]
        if len(role_id) < 1: 
            return
        else:
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(int(role_id[0]))

            if role != None:
                if role not in payload.member.roles:
                    try:
                        await payload.member.add_roles(
                            role
                        )
                    except Exception:
                        pass


    @AutoModPluginBlueprint.listener()
    async def on_raw_reaction_remove(
        self, 
        payload: discord.RawReactionActionEvent
    ) -> None:
        if f"{payload.user_id}" == f"{self.bot.user.id}": return

        rrs = self.db.configs.get(payload.guild_id, "reaction_roles")
        if not f"{payload.message_id}" in rrs: return

        data = rrs[f"{payload.message_id}"]
        if len(data["pairs"]) < 1: return

        if payload.emoji.id == None:
            possible_name = payload.emoji.name
        else:
            possible_name = f"<:{payload.emoji.name}:{payload.emoji.id}>"

        role_id = [list(x.values())[1] for x in data["pairs"] if list(x.values())[0] == possible_name]
        if len(role_id) < 1: 
            return
        else:
            guild = self.bot.get_guild(payload.guild_id)
            if guild.chunked: await self.bot.chunk_guild(guild)

            role = guild.get_role(int(role_id[0]))
            member = guild.get_member(payload.user_id)
            if member.bot == True: return

            if role != None:
                if role in member.roles:
                    try:
                        await member.remove_roles(
                            role
                        )
                    except Exception:
                        pass


    @AutoModPluginBlueprint.listener()
    async def on_raw_message_delete(
        self, 
        payload: discord.RawMessageDeleteEvent
    ) -> None:
        if payload.guild_id == None: return
        rrs = self.db.configs.get(payload.guild_id, "reaction_roles")
        if not f"{payload.message_id}" in rrs: return

        del rrs[f"{payload.message_id}"]
        self.db.configs.update(payload.guild_id, "reaction_roles", rrs)


    reaction_roles = discord.app_commands.Group(
        name="reaction_roles",
        description="Configure reaction roles",
        default_permissions=discord.Permissions(manage_roles=True)
    )
    @reaction_roles.command(
        name="show",
        description="Shows a list of active reaction roles"
    )
    @discord.app_commands.default_permissions(manage_roles=True)
    async def show(
        self, 
        ctx: discord.Interaction
    ) -> None:
        """
        reaction_roles_help
        examples:
        -reaction_roles show
        """
        rrs = {
            k: v for k, v in self.db.configs.get(
                ctx.guild.id, 
                "reaction_roles"
            ).items() if self.bot.get_channel(int(v['channel'])) != None
        }
        if len(rrs) < 1:
            return await ctx.response.send_message(self.locale.t(ctx.guild, "no_rr", _emote="NO"))
        else:
            e = Embed(
                ctx,
                title="Reaction roles"
            )
            for msg, data in rrs.items():
                channel = ctx.guild.get_channel(int(data["channel"]))
                e.add_field(
                    name=f"__**{msg}{f' (#{channel.name})' if channel != None else ''}**__",
                    value=f"{f'``▶`` [Jump to message](https://discord.com/channels/{ctx.guild.id}/{channel.id}/{msg})' if channel != None else ''}" + 
                    "{}".format(
                        "\n" if channel != None else ""
                    ) +
                    "\n".join(
                        [f"``▶`` {self.bot.get_emoji(int(pair['emote'])) if pair['emote'][0].isdigit() else pair['emote']} → <@&{pair['role']}>" for pair in data["pairs"]]
                    )
                )

            await ctx.response.send_message(embed=e)


    @reaction_roles.command(
        name="add",
        description="Adds a new reaction role"
    )
    @discord.app_commands.describe(
        message_id="The message the reaction should be added to",
        emote="The emote of the reaction (custom or default emotes)",
        role="The role users should receive when reacting"
    )
    @discord.app_commands.default_permissions(manage_roles=True)
    async def add(
        self, 
        ctx: discord.Interaction, 
        message_id: str, 
        emote: str, 
        role: discord.Role
    ) -> None:
        """
        reaction_roles_add_help
        examples:
        -reaction_roles add 543056846601191508 🟢 @GreenRole
        """
        try:
            emote = await Emote().convert(ctx, emote)
        except Exception as ex:
            return self.error(ctx, ex)
        
        try:
            message = await Message().convert(ctx, message_id)
        except Exception as ex:
            return self.error(ctx, ex)
        else:
            if message == None: return self.error(ctx, commands.BadArgument("Message not found"))

        rrs = self.db.configs.get(ctx.guild.id, "reaction_roles")
        if f"{message.id}" in rrs:
            data = rrs[f"{message.id}"]
        else:
            data = {
                "channel": f"{message.channel.id}",
                "pairs": []
            }
        if len(data["pairs"]) > 10:
            return await ctx.response.send_message(self.locale.t(ctx.guild, "max_rr", _emote="NO"))
        else:
            if len(message.reactions) > 10:
                return await ctx.response.send_message(self.locale.t(ctx.guild, "max_rr_reactions", _emote="NO"))
            else:
                if role.position >= ctx.guild.me.top_role.position:
                    return await ctx.response.send_message(self.locale.t(ctx.guild, "rr_role_too_high", _emote="NO"))
                elif f"{emote}" in [list(x.values())[0] for x in data["pairs"]]:
                    return await ctx.response.send_message(self.locale.t(ctx.guild, "rr_emoji_alr_bound", _emote="NO"))
                elif f"{role.id}" in [list(x.values())[1] for x in data["pairs"]]:
                    return await ctx.response.send_message(self.locale.t(ctx.guild, "rr_role_alr_bound", _emote="NO"))
                else:
                    try:
                        await message.add_reaction(
                            emote
                        )
                    except Exception as ex:
                        return await ctx.response.send_message(self.locale.t(ctx.guild, "fail", _emote="NO", exc=ex))
                    else:
                        data["pairs"].append({
                            "emote": f"{emote}",
                            "role": f"{role.id}"
                        })
                        rrs.update({
                            f"{message.id}": data
                        })
                        self.db.configs.update(ctx.guild.id, "reaction_roles", rrs)

                        await ctx.response.send_message(self.locale.t(ctx.guild, "set_rr", _emote="YES"))


    @reaction_roles.command(
        name="remove",
        description="Removes an exisitng reaction role"
    )
    @discord.app_commands.describe(
        message_id="The message of the reaction role",
        role="The role you want to remove"
    )
    @discord.app_commands.default_permissions(manage_roles=True)
    async def remove(
        self, 
        ctx: discord.Interaction, 
        message_id: str, 
        role: discord.Role
    ) -> None:
        """
        reaction_roles_remove_help
        examples:
        -reaction_roles remove 543056846601191508 @Greenrole
        """
        rrs = self.db.configs.get(ctx.guild.id, "reaction_roles")
        if len(rrs) < 1:
            return await ctx.response.send_message(self.locale.t(ctx.guild, "no_rr", _emote="NO"))
        else:
            if not f"{message_id}" in rrs:
                return await ctx.response.send_message(self.locale.t(ctx.guild, "not_rr_msg", _emote="NO"))
            else:
                data = rrs[f"{message_id}"]
                if len([x for x in data["pairs"] if list(x.values())[1] == f"{role.id}"]) < 1:
                    return await ctx.response.send_message(self.locale.t(ctx.guild, "no_rr_role", _emote="NO"))
                else:
                    data["pairs"] = [x for x in data["pairs"] if list(x.values())[1] != f"{role.id}"]
                    if len(data["pairs"]) > 0:
                        rrs[f"{message_id}"] = data
                    else:
                        del rrs[f"{message_id}"]
                    self.db.configs.update(ctx.guild.id, "reaction_roles", rrs)

                    await ctx.response.send_message(self.locale.t(ctx.guild, "removed_rr", _emote="YES"))


async def setup(
    bot: ShardedBotInstance
) -> None: await bot.register_plugin(ReactionRolesPlugin(bot))