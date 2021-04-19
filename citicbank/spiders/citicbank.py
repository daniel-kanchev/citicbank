import scrapy
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst
from datetime import datetime
from citicbank.items import Article


class citicbankSpider(scrapy.Spider):
    name = 'citicbank'
    start_urls = ['http://www.citicbank.com/about/companynews/']

    def parse(self, response):
        current_year = int(datetime.now().strftime('%Y'))
        last_year = 2008
        while current_year >= last_year:
            link = f'http://www.citicbank.com/about/companynews/banknew/message/{current_year}/'
            yield response.follow(link, self.parse_year, cb_kwargs=dict(year=current_year))
            current_year -= 1

    def parse_year(self, response, year, page=0):
        links = response.xpath('//ul[@class="gz_li"]/a/@href').getall()
        if links:
            yield from response.follow_all(links, self.parse_article)
            page +=1
            next_page = f'http://www.citicbank.com/about/companynews/banknew/message/{year}/index_{page}.html'
            yield response.follow(next_page, self.parse_year, cb_kwargs=dict(year=year, page=page))

    def parse_article(self, response):
        if 'pdf' in response.url.lower():
            return

        item = ItemLoader(Article())
        item.default_output_processor = TakeFirst()

        title = response.xpath('//h1[@class="center"]/text()').get()
        if title:
            title = title.strip()

        date = response.xpath('//div[@class="main_subtitle"]//li/text()').get()
        if date:
            date = " ".join(date.split())

        content = response.xpath('//div[@class="main_content"]//text()').getall()
        content = [text.strip() for text in content if text.strip() and '{' not in text]
        content = " ".join(content).strip()

        item.add_value('title', title)
        item.add_value('date', date)
        item.add_value('link', response.url)
        item.add_value('content', content)

        return item.load_item()
