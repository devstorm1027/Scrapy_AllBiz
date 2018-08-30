import scrapy
import math
import re
import requests
from Scrapy_AllBiz.items import AllbizItem


class AlibabaCrawler(scrapy.Spider):
    name = 'allbiz_crawler'
    allowed_domains = ['all.biz']
    start_urls = ['https://all.biz/buy']
    unique_data = set()

    def parse(self, response):
        cat_list = response.xpath('//div[@class="b-markets__left-menu"]/ul/li/a/@href').extract()
        for cat in cat_list:
            yield scrapy.Request(
                url=cat,
                callback=self.parse_rubrics,
                dont_filter=True
            )

    def parse_rubrics(self, response):
        cat_list = response.xpath('//div[@class="b-markets__left-menu"]/ul/li/a/@href').extract()
        for cat in cat_list:
            yield scrapy.Request(
                url=cat,
                callback=self.parse_categories,
                dont_filter=True
            )

    def parse_categories(self, response):
        cat_list = response.xpath('//div[@class="b-markets__left-menu"]/ul/li/a/@href').extract()
        for cat in cat_list:
            yield scrapy.Request(
                url=cat,
                callback=self.parse_groups,
                dont_filter=True
            )

    def parse_groups(self, response):
        cat_list = response.xpath('//div[@class="b-left-item-block__inner"]/ul/li/a/@href').extract()
        for cat in cat_list:
            yield scrapy.Request(
                url=cat,
                callback=self.parse_pages,
                dont_filter=True
            )

    def parse_pages(self, response):
        item = AllbizItem()
        category = response.xpath('//a[@class="b-rubricator__main"]/@title').extract()
        item['category'] = category[0] if category else None
        page_url = response.url + '?page='
        total_num = response.xpath('//div[@class="ab-founded"]/text()').extract()
        total_num = re.search('(\d+)', total_num[0].replace(',', ''), re.DOTALL)
        if total_num:
            total_num = total_num.group(1)
        count_per_page = len(response.xpath('//div[contains(@class, "b-product--grid-item")]'
                                            '/h3[@itemprop="name"]/a/@href').extract())
        for i in range(math.ceil(int(total_num)/count_per_page)):
            yield scrapy.Request(
                url=page_url + str(i+1),
                callback=self.parse_product_links,
                meta={'item': item},
                dont_filter=True
            )

    def parse_product_links(self, response):
        href_list = response.xpath('//div[contains(@class, "b-product--grid-item")]'
                                   '/h3[@itemprop="name"]/a/@href').extract()
        for href in href_list:
            yield scrapy.Request(
                url=href,
                callback=self.parse_product,
                meta=response.meta,
                dont_filter=True
            )

    def parse_product(self, response):
        item = response.meta.get('item')

        product_name = response.xpath('//h1[@class="ab-product-name"]/text()').extract()
        item['product_name'] = product_name[0] if product_name else None

        company_link = response.xpath('//a[@class="ab-company-name"]/@data-href').extract()
        item['company_link'] = company_link[0] if company_link else None

        company_name = response.xpath('//span[@class="ab-company-name__text"]/@title').extract()
        item['company_name'] = company_name[0] if company_name else None

        country = response.xpath('//div[@class="ab-company-location__info"]/text()').extract()
        item['country'] = country[0] if country else None

        if item['company_link'] and (item['company_link'] not in self.unique_data):
            self.unique_data.add(item['company_link'])
            yield scrapy.Request(
                url=item['company_link'],
                callback=self.parse_company_info,
                meta={'item': item},
                dont_filter=True
            )

    def parse_company_info(self, response):
        item = response.meta.get('item')

        website = response.xpath('//td[contains(text(), "Site")]/following-sibling::td[1]/a/text()').extract()
        if not website:
            website = response.xpath('//div[contains(text(), "Site")]/following-sibling::div[1]/a/text()').extract()
        website = list(set(website))
        item['website'] = ','.join(website) if website else None

        contact_person = response.xpath('//p[@class="b-contacts-data-content"][2]/text()').extract()
        if not contact_person:
            contact_person = response.xpath('//div[@class="ms-contacts-page"]'
                                            '//div[@class="ms-contacts-chief__wrap"]/text()').extract()
        item['contact_person'] = contact_person[0] if contact_person else None

        email = response.xpath('//td[contains(text(), "Email")]/following-sibling::td[1]/a/text()').extract()
        if not email:
            email = response.xpath('//div[contains(text(), "Email")]/following-sibling::div[1]/a/text()').extract()
        item['email'] = email[0] if email else None

        telephone = response.xpath('//div[@class="b-company-phones _header"]/text()').extract()
        if not telephone:
            telephone = response.xpath('//div[@class="ms-header-phone__number"]/text()').extract()
        # if not telephone:
        #     url = 'https://api.all.biz/en//ajax/viewphone/{country_code}?' \
        #           'ent_id={ent_id}&' \
        #           'phone={phone}&' \
        #           'country={country_code}&' \
        #           'source=minisite'
        #     ent_id = response.xpath('//div[contains(@class, "b-company-phones-block")]/@data-entid').extract_first()
        #     phone = response.xpath('//div[contains(@class, "b-company-phones-block")]/@data-phone').extract_first()
        #     country_code = response.xpath('//div[contains(@class, "b-company-phones-block")]/@data-country').extract_first()
        #     try:
        #         phone_data = requests.get(url.format(ent_id=ent_id, phone=phone, country_code=country_code)).json()
        #         telephone = [phone_data.get('phone')]
        #     except:
        #         print('Error while parsing json data!')
        item['telephone'] = telephone[0] if telephone else None

        yield item
