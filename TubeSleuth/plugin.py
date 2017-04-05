# -*- coding: utf-8 -*-
###
# Copyright (c) 2015, butterscotchstallion
# All rights reserved.
#
#
###

import supybot.utils as utils
from supybot.commands import *
import supybot.ircmsgs as ircmsgs
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import urllib
import json

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization("TubeSleuth")
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

class TubeSleuth(callbacks.Plugin):
    threaded = True

    def yt(self, irc, msg, args, query):
        """Queries Youtube API"""
        base_url = "https://www.googleapis.com/youtube/v3/search"
        no_results_message = self.registryValue("noResultsMessage")
        use_bold = self.registryValue("useBold")
        safe_search = self.registryValue("safeSearch")
        respond_to_pm = self.registryValue("respondToPrivateMessages")
        template = self.registryValue("template")
        developer_key = self.registryValue("developerKey")
        sort_order = self.registryValue("sortOrder")
        channel = msg.args[0]
        origin_nick = msg.nick
        is_channel = irc.isChannel(channel)
        is_private_message = not is_channel

        if not developer_key:
            no_key_error_message = "No Google developer key set. Get one at https://code.google.com/apis/youtube/dashboard/gwt/index.html#settings"
            irc.error(no_key_error_message)
            self.log.error("TubeSleuth: %s" % (no_key_error_message))
            return

        if is_channel:
            message_destination = channel
        else:
            message_destination = origin_nick

        if is_private_message and not respond_to_pm:
            self.log.info("TubeSleuth: not responding to PM from %s" % (origin_nick))
            return

        opts = {"q": query,
                "part": "snippet",
                "maxResults": "1",
                "order": sort_order,
                "key": developer_key,
                "safeSearch": safe_search}

        search_url = "%s?%s" % (base_url, urlencode(opts))

        self.log.debug("TubeSleuth URL: %s" % (search_url))

        result = False

        try:
            response = utils.web.getUrl(search_url).decode("utf8")
            data = json.loads(response)

            try:
                items = data["items"]

                if len(items) > 0:
                    video = items[0]
                    snippet = video["snippet"]
                    id = video["id"]["videoId"]
                    title = snippet["title"]
                    result = True

                    if use_bold and title:
                        title = ircutils.bold(title)

                    link = "https://youtu.be/%s" % (id)
                    template = template.replace("$link", link)
                    template = template.replace("$title", title)

                    yt_logo = self.get_youtube_logo()
                    template = template.replace("$yt_logo", yt_logo)
                else:
                    self.log.error("TubeSleuth: unexpected API response")

            except IndexError as e:
                self.log.error("TubeSleuth: unexpected API response")

        except Exception as err:
            self.log.error("TubeSleuth: %s" % (str(err)))

        if result:
            irc.queueMsg(ircmsgs.privmsg(message_destination, template))
        else:
            irc.queueMsg(ircmsgs.privmsg(message_destination, no_results_message))

    yt = wrap(yt, ["text"])

    def get_youtube_logo(self):
        colored_letters = [
            "%s" % ircutils.mircColor("You", fg="red", bg="white"),
            "%s" % ircutils.mircColor("Tube", fg="white", bg="red")
        ]

        yt_logo = "".join(colored_letters)

        return yt_logo

Class = TubeSleuth


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
