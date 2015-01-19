# -*- test-case-name: twittytwister.test.test_platform -*-
#
# Copyright (c) 2010-2013 Ralph Meijer <ralphm@ik.nu>
# See LICENSE.txt for details

"""
Twitter Platform objects.

@see: U{https://dev.twitter.com/docs/platform-objects}.
"""

from twisted.python import log

class TwitterObject(object):
    """
    A Twitter Platform object.
    """
    raw = None
    SIMPLE_PROPS = None
    COMPLEX_PROPS = None
    LIST_PROPS = None

    @classmethod
    def fromDict(cls, data):
        """
        Fill this objects attributes from a dict for known properties.
        """
        obj = cls()
        obj.raw = data
        for name, value in data.iteritems():
            if cls.SIMPLE_PROPS and name in cls.SIMPLE_PROPS:
                setattr(obj, name, value)
            elif cls.COMPLEX_PROPS and name in cls.COMPLEX_PROPS:
                value = cls.COMPLEX_PROPS[name].fromDict(value)
                setattr(obj, name, value)
            elif cls.LIST_PROPS and name in cls.LIST_PROPS:
                value = [cls.LIST_PROPS[name].fromDict(item)
                         for item in value]
                setattr(obj, name, value)

        return obj


    def __repr__(self):
        bodyParts = []
        for name in dir(self):
            if self.SIMPLE_PROPS and name in self.SIMPLE_PROPS:
                if hasattr(self, name):
                    bodyParts.append("%s=%s" % (name,
                                                repr(getattr(self, name))))

            elif self.COMPLEX_PROPS and name in self.COMPLEX_PROPS:
                if hasattr(self, name):
                    bodyParts.append("%s=%s" % (name,
                                                repr(getattr(self, name))))
            elif self.LIST_PROPS and name in self.LIST_PROPS:
                if hasattr(self, name):
                    items = getattr(self, name)

                    itemBodyParts = []
                    for item in items:
                        itemBodyParts.append(repr(item))

                    itemBody = ',\n'.join(itemBodyParts)
                    lines = itemBody.splitlines()
                    itemBody = '\n    '.join(lines)

                    if itemBody:
                        itemBody = '\n    %s\n' % (itemBody,)

                    bodyParts.append("%s=[%s]" % (name, itemBody))

        body = ',\n'.join(bodyParts)
        lines = body.splitlines()
        body = '\n    '.join(lines)

        result = "%s(\n    %s\n)" % (self.__class__.__name__, body)
        return result



class Indices(TwitterObject):
    """
    Indices for tweet entities.
    """
    start = None
    end = None

    @classmethod
    def fromDict(cls, data):
        obj = cls()
        obj.raw = data
        try:
            obj.start, obj.end = data
        except (TypeError, ValueError):
            log.err()
        return obj

    def __repr__(self):
        return "%s(start=%s, end=%s)" % (self.__class__.__name__,
                                         self.start, self.end)



class Size(TwitterObject):
    """
    Size of a media object.
    """
    SIMPLE_PROPS = set(['w', 'h', 'resize'])



class Sizes(TwitterObject):
    """
    Available sizes for a media object.
    """
    COMPLEX_PROPS = {'large': Size,
                     'medium': Size,
                     'small': Size,
                     'thumb': Size}



class Media(TwitterObject):
    """
    Media entity.
    """
    SIMPLE_PROPS = set(['id', 'media_url', 'media_url_https', 'url',
                        'display_url', 'expanded_url', 'type'])
    COMPLEX_PROPS = {'indices': Indices, 'sizes': Sizes}



class URL(TwitterObject):
    """
    URL entity.
    """
    SIMPLE_PROPS = set(['url', 'display_url', 'expanded_url'])
    COMPLEX_PROPS = {'indices': Indices}



class UserMention(TwitterObject):
    SIMPLE_PROPS = set(['id', 'screen_name', 'name'])
    COMPLEX_PROPS = {'indices': Indices}



class HashTag(TwitterObject):
    SIMPLE_PROPS = set(['text'])
    COMPLEX_PROPS = {'indices': Indices}



class Entities(TwitterObject):
    """
    Tweet entities.
    """
    LIST_PROPS = {'media': Media, 'urls': URL,
                  'user_mentions': UserMention, 'hashtags': HashTag}



class Status(TwitterObject):
    """
    Twitter Status.
    """
    SIMPLE_PROPS = set(['created_at', 'id', 'text', 'source', 'truncated',
        'in_reply_to_status_id', 'in_reply_to_screen_name',
        'in_reply_to_user_id', 'favorited', 'user_id', 'geo'])
    COMPLEX_PROPS = {'entities': Entities}

# circular reference:
Status.COMPLEX_PROPS['retweeted_status'] = Status



class User(TwitterObject):
    """
    Twitter User.
    """
    SIMPLE_PROPS = set(['id', 'name', 'screen_name', 'location', 'description',
        'profile_image_url', 'url', 'protected', 'followers_count',
        'profile_background_color', 'profile_text_color', 'profile_link_color',
        'profile_sidebar_fill_color', 'profile_sidebar_border_color',
        'friends_count', 'created_at', 'favourites_count', 'utc_offset',
        'time_zone', 'following', 'notifications', 'statuses_count',
        'profile_background_image_url', 'profile_background_tile', 'verified',
        'geo_enabled'])
    COMPLEX_PROPS = {'status': Status}

# circular reference:
Status.COMPLEX_PROPS['user'] = User




