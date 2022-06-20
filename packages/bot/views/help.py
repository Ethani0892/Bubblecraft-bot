import discord
from discord.ui import View, Select # pyright: reportMissingImports=false

from typing import List

from .buttons import LinkBtn



ACTUAL_PLUGIN_NAMES = {
    "ConfigPlugin": "⚙️ Configuration",
    "AutoModPluginBlueprint": "⚔️ Automoderator",
    "ModerationPlugin": "🔨 Moderation",
    "UtilityPlugin": "🔧 Utility",
    "TagsPlugin": "📝 Custom Commands",
    "CasesPlugin": "📦 Cases",
    "ReactionRolesPlugin": "🎭 Reaction Roles",
}


class HelpView(View):
     def __init__(
        self, 
        bot, 
        show_invite: bool = False,
        *args, 
        **kwargs
    ) -> None:
        self.bot = bot
        super().__init__(*args, **kwargs)

        if show_invite == True:
            self.add_item(
                Select(
                    placeholder="Select a plugin",
                    options=[
                        discord.SelectOption(
                            label=v,
                            value=k
                        ) for k, v in ACTUAL_PLUGIN_NAMES.items()
                    ],
                    custom_id="help-select"
                )
            )

        self.add_item(LinkBtn(_url=f"{bot.config.support_invite}", _label="Support"))
        self.add_item(LinkBtn(_url=f"https://top.gg/bot/{bot.user.id}/vote", _label="Vote"))
        if show_invite == True:
            self.add_item(LinkBtn(_url=f"https://discord.com/oauth2/authorize?client_id={bot.user.id}&permissions=403041534&scope=bot+applications.commands", _label="Invite"))