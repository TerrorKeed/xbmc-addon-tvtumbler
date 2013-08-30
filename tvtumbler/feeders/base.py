'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

import datetime
import feedparser

from .. import logger
from ..names import SceneNameParser
from ..links import Downloadable, Torrent
from ..numbering import SCENE_NUMBERING


class BaseFeeder(object):
    """Base class for all feeders"""

    def __init__(self):

        # The minimum update freq (in secs)
        self.min_update_freq_secs = 15 * 60

        # e.g. http://example.com/rss
        self.rss_url = None

        # Cache of latest entries (a list of Downloadable's)
        self._latest = []

        # timestamp of last update (datetime.datetime)
        self._last_update_datetime = None

    @classmethod
    def get_name(cls):
        '''
        Human-readable name.
        @return: (str)
        '''
        return cls.__name__

    @classmethod
    def get_nameparser(cls):
        '''
        Which name parser is to be used for this feeder.

        @return: (type) A class inheriting from NameParser.
        '''
        return SceneNameParser

    @classmethod
    def get_numbering(cls):
        '''
        Which numbering system does this feeder use.

        @return: (int) Currently only SCENE_NUMBERING and TVDB_NUMBERING
            are supported.
        '''
        return SCENE_NUMBERING

    def get_latest(self):
        '''
        Return a list of available downloads.
        Will call update() if needed.

        @return: ([Downloadable]) A list of Downloadable's
        '''
        if (self._last_update_datetime is None or
            self._last_update_datetime + datetime.timedelta(seconds=self.min_update_freq_secs)
                    < datetime.datetime.now()):
            self._update()

        return self._latest

    def _update(self):
        '''
        '''
        feed = feedparser.parse(self.rss_url)
        self._last_update_datetime = datetime.datetime.now()
        self._latest = []

        if feed:
            for entry in feed.entries:
                i = self._parse_rss_item(entry)
                if i:
                    self._latest.append(i)
            return True
        return False

    def _parse_rss_item(self, item):
        '''
        RSS item (from _parse_rss_feed) to Downloadable.
        Override this in derived classes to return the correct type of Downloadable.

        @param item: (dict)
        @return: (Downloadable|None) If the item does not have any known TvEpisodes, return None. 
        '''
        return None


class TorrentFeeder(BaseFeeder):
    """Base class for all feeders that supply torrents"""

    def _parse_rss_item(self, item):
        '''
        RSS item (from _parse_rss_feed) to Torrent.

        @param item: (dict)
        @return: (Torrent|None) If the item does not have any known TvEpisodes, return None.
        '''
        fileName = None
        title = None
        pubDate = None
        urls = []
        infoHash = None

        # logger.debug(repr(item))
        # logger.debug(repr(item.enclosures))

        try:
            fileName = item.filename
        except (KeyError, AttributeError):
            pass

        try:
            magnet_uri = item.magneturi
            if magnet_uri:
                urls.append(magnet_uri)
        except (KeyError, AttributeError):
            pass

        try:
            for enc in item.enclosures:
                if (enc.type == 'application/x-bittorrent' or
                    enc.href.startswith('magnet:') or
                    enc.href.endwidth('.torrent')):
                    urls.append(enc.href)
        except (KeyError, AttributeError):
            pass

        try:
            for link in item.links:
                if link.href.startswith('magnet:') or link.href.endswith('.torrent'):
                    urls.append(link.href)
        except (KeyError, AttributeError):
            pass

        try:
            title = item.title
        except (KeyError, AttributeError):
            pass

        try:
            pubDate = item.published_parsed
        except (KeyError, AttributeError), e:
            logger.debug('unable to parse date, using current timestamp instead:' + str(e))
            pubDate = datetime.datetime.now()

        try:
            infoHash = item.infohash
            if infoHash:
                magnets = [k for k in urls if k.startswith('magnet:')]
                if len(magnets) == 0:
                    # If we have no magnet, but we have the infoHash, then make a magnet
                    urls.append('magnet:?xt=urn:btih:' + infoHash)
        except (KeyError, AttributeError):
            pass

        # remove any duplicate urls
        urls = list(set(urls))

        if len(urls) == 0:
            logger.debug(u'No useful links found in item')
            return None

        if fileName:
            # If we have the fileName, use that for the name parser
            parse_name = fileName
            has_ext = True
        else:
            # Otherwise, we must use the title
            parse_name = title
            has_ext = False

        nameparser = self.get_nameparser()(parse_name, has_ext=has_ext,
                                           numbering_system=self.get_numbering())

        if not nameparser.is_known:
            # Not parsable?  Fail
            return None

        return Torrent(urls=urls,
                    episodes=nameparser.episodes,
                    name=title,
                    quality=nameparser.quality,
                    timestamp=pubDate,
                    feeder=self)


class VODFeeder(BaseFeeder):
    """Base class for all feeders that supply video-on-demand"""
    pass