from lxml import etree
import scrapy
from scrapy.crawler import CrawlerProcess
from sinjitopics_scrapy.spiders.yahoo_it import ScrapyYahooItSpider
from scrapy.settings import Settings
from sinjitopics_scrapy import settings as my_settings

def lambda_handler(event, context):

    #context.callbackWaitsForEmptyEventLoop=False
    print(etree.LXML_VERSION)
    #print(psycopg2.apilevel)
    process = CrawlerProcess()

    process.crawl(ScrapyYahooItSpider)
    #process.start() # すべてのクロールジョブが終了するまでスクリプトはここでブロック
    process.start(stop_after_crawl=False) # すべてのクロールジョブが終了するまでスクリプトはここでブロック
    
    #process = CrawlerProcess()
    #process.crawl(ScrapyYahooBusinessSpider)
    #process.start() # すべてのクロールジョブが終了するまでスクリプトはここでブロック
    #process.start(stop_after_crawl=False) # すべてのクロールジョブが終了するまでスクリプトはここでブロック

    print('ここでプロセス終了')
    #process.stop()
