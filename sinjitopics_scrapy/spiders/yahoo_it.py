import scrapy
import datetime
from sinjitopics_scrapy.items import SinjitopicsScrapyItem
from sinjitopics_scrapy.pipelines import SinjitopicsScrapyPipeline


class ScrapyYahooItSpider(scrapy.Spider):

    today = datetime.datetime.now() + datetime.timedelta(hours=+9)

    name = 'scrapy_yahoo_it'
    allowed_domains = ['news.yahoo.co.jp','headlines.yahoo.co.jp']
    start_urls = ['https://news.yahoo.co.jp/topics/domestic?date='+today.strftime("%Y%m%d"),
                  'https://news.yahoo.co.jp/topics/world?date='+today.strftime("%Y%m%d"),
                  'https://news.yahoo.co.jp/topics/business?date='+today.strftime("%Y%m%d"),
                  'https://news.yahoo.co.jp/topics/entertainment?date='+today.strftime("%Y%m%d"),
                  'https://news.yahoo.co.jp/topics/sports?date='+today.strftime("%Y%m%d"),
                  'https://news.yahoo.co.jp/topics/it?date='+today.strftime("%Y%m%d"),
                 ]
   
    ############################################################################
    ###
    ###初回実行（1週間前の記事をDBから削除）
    ###
    ############################################################################   
    def __init__(self   ):
        print(self.today)
        #本日から7日前を算出
        d = self.today + datetime.timedelta(days=-7)
        print(d.strftime("%Y%m%d"))
        SinjitopicsScrapyPipeline.deleteDatabase(d.strftime("%Y%m%d"))
        
    
    
    ############################################################################
    ###
    ###カテゴリーページから各概要ページURLを取得
    ###
    ############################################################################            
    def parse(self,response):
        
        print('カテゴリーページ表示')
        #概要ページURL取得
        links = response.css('.newsFeed_item_link::attr(href)').extract()

        for link in links:
            yield scrapy.Request(link, callback=self.parse_summary)
    
    ############################################################################
    ###
    ###概要ページから各記事全文ページURLおよびタブ名取得
    ###
    ############################################################################
    def parse_summary(self, response):
        
        print('概要ページ表示')
        #記事全文ページURL取得
        detailLinks = response.css('div.contentsWrap > article > div > a::attr(href)').extract()
        
        #タブ名を取得
        tab = response.css('header > nav > div.yjnHeader_nav_sub > ul > li.dfFfbj > a::text').extract_first()
        
        for detailLink in detailLinks:
            yield scrapy.Request(detailLink, callback=self.parse_detail, meta={"tab": tab})

    ############################################################################
    ###
    ###記事全文ページから各データ取得
    ###
    ############################################################################
    def parse_detail(self, response):
        
        print("記事全文ページ表示")
        item = SinjitopicsScrapyItem()
        
        item['id'] = response.url[-40:]
        item['tab_id'] = SinjitopicsScrapyPipeline.getTabId(response.meta["tab"])
        item['title'] = response.css('div.contentsWrap > article > header > h1::text').extract_first()
        item['text'] = SinjitopicsScrapyPipeline.linkingText(response.css('div.article_body div p.yjSlinkDirectlink::text').extract())
        item['owner'] = response.css('div.contentsWrap > article > footer > a::text').extract_first()
        item['url'] = 'https://news.yahoo.co.jp' + response.css('div.contentsWrap > article > footer > a::attr(href)').extract_first()
        item['image'] = SinjitopicsScrapyPipeline.checkExistImage(response.css('div.article_body picture > img::attr(src)').extract_first())
        item['thumbnail_gid'] =SinjitopicsScrapyPipeline.setThumbnailGid(response.css('div.article_body picture > img::attr(src)').extract_first())
        item['animation_gid'] = SinjitopicsScrapyPipeline.setAnimationGid()
        item['music_gid'] = SinjitopicsScrapyPipeline.setMusicGid(item['text'])
        item['upload'] = SinjitopicsScrapyPipeline.setUploadDateTime(response.css('div.contentsWrap > article > header > div > div > div > p > time::text') .extract())
        item['created_at'] = self.today
        item['updated_at'] = self.today
        
        
        print('DBへ保存開始')
        SinjitopicsScrapyPipeline.saveDataBase(item)

        return item
 