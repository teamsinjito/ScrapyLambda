# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class SinjitopicsScrapyItem(scrapy.Item):
    id = scrapy.Field()
    tab_id = scrapy.Field() 
    title = scrapy.Field()
    text = scrapy.Field()
    owner = scrapy.Field()
    url = scrapy.Field()
    image = scrapy.Field()
    thumbnail_gid = scrapy.Field()
    animation_gid = scrapy.Field()
    music_gid = scrapy.Field()
    upload = scrapy.Field()
    created_at = scrapy.Field()
    updated_at = scrapy.Field()
