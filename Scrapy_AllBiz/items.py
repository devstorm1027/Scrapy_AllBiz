import scrapy


class AllbizItem(scrapy.Item):
    product_name = scrapy.Field()
    category = scrapy.Field()
    company_name = scrapy.Field()
    country = scrapy.Field()
    website = scrapy.Field()
    contact_person = scrapy.Field()
    telephone = scrapy.Field()
    email = scrapy.Field()
    company_link = scrapy.Field()
