'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

from . import logger
from . import feeders
from . import quality
from . import downloaders
from .tv import TvShow


def run():
    logger.debug('feeder - run')
    latest_downloadables = feeders.get_latest()
    logger.debug('latest_downloadables: ' + repr(latest_downloadables))

    wanted = [s for s in latest_downloadables if s.is_wanted]

    # Organise these by (tvdb_id, season, episode) so that we can eliminate duplicates.
    # Our list is already sorted by preferred provider, so we'll get the better provider
    # here for free.
    wanted_dict = {}
    for w in wanted:
        qual = w.quality
        for ep in w.episodes:
            tvdb_id = ep.tvshow.tvdb_id
            for (season, episode) in ep.tvdb_episodes:
                key = (tvdb_id, season, episode)
                if not key in wanted_dict:
                    wanted_dict[key] = {}
                if not qual in wanted_dict[key]:
                    wanted_dict[key][qual] = w

    for (tvdb_id, season, episode), dlables in wanted_dict.iteritems():
        qualities = dlables.keys()
        known_qualities = [q for q in qualities if q != quality.UNKNOWN_QUALITY]
        if known_qualities:
            use_dlable = dlables[max(known_qualities)]
        else:
            use_dlable = dlables[quality.UNKNOWN_QUALITY]
        downloaders.download(use_dlable)
