import datetime
import os
import urlparse

import re
import requests

from scrapy import Selector

from selenium import webdriver

from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from tables import Base, engine, Company, TeamMember, Funding


XPATH_COMPANY_LIST = '//div[@class="info-block"]/h4/a/@href'
XPATH_COMPANY_FUNDING_DATE = '//h2[@class="title_date"]'
XPATH_COMPANY_FUNDING_ROUND = '//table[@class="table container"]//a/text()'
XPATH_COMPANY_FUNDING_AMOUNT = '//table[@class="table container"]//td/text()'
XPATH_COMPANY_CRUNCHBASE_LINK = '//div[@class="info-block"]//a/@href'
XPATH_COMPANY_SITE_LINK = '//div[@class="definition-list container"]//dd[5]/a/@href'
XPATH_COMPANY_LINKEDIN_LINK = '//dd[@class="social-links"]//a[@class="icons linkedin"]/@href'
XPATH_COMPANY_NAME = '//h1[@id="profile_header_heading"]//a/text()'
XPATH_COMPANY_DESCRIPTION = '//div[@class="definition-list container"]//dd[2]/text()'

XPATH_TEAM_MEMBER_LIST = '//h4/div[@class="follow_card_wrapper"]/div[@class="link_container"]/a[@data-type="person"][@class="follow_card"]/@href'
XPATH_TEAM_MEMBER_FULL_NAME = '//h1[@id="profile_header_heading"]//a/text()'
XPATH_TEAM_MEMBER_POSITION = '//div[@class="overview-stats"]//dd/text()'
XPATH_TEAM_MEMBER_CRUNCHBASE_LINK = '//h4/div[@class="follow_card_wrapper"]/div[@class="link_container"]/a[@data-type="person"][@class="follow_card"]/@href'
XPATH_TEAM_MEMBER_LINKEDIN_LINK = '//dd[@class="social-links"]/a/@href'
XPATH_TEAM_MEMBER_PERSONAL_DETAILS = '//div[@class="base info-tab description"]//div[@class="card-content box container card-slim"]//text()'

base_url = 'https://www.crunchbase.com/'
funding_round_url = 'https://www.crunchbase.com/funding-rounds'

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/600.7.12 (KHTML, like Gecko) Version/8.0.7 Safari/600.7.12'}


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
Session.configure(bind=engine) 
session = Session()

browser = webdriver.Chrome()

effective_date = datetime.datetime.now().date()


def get_funding_dates():
    sel = get_selector(funding_round_url)
    return sel.xpath(XPATH_COMPANY_FUNDING_DATE)


def get_selector(url):
    response = requests.get(url, headers=headers)
    rendered_content = render_content(response.content)
    return Selector(text=rendered_content)
    # browser.get('file:///{}/raw_content.html'.format(os.getcwd()))
    # return Selector(text=browser.page_source)


def render_content(content):
    with open('raw_content.html', 'wb') as fout:
        fout.write(content)

    browser.get('file:///{}/raw_content.html'.format(os.getcwd()))

    return browser.page_source


def load_company_list(sel):
    return [urlparse.urljoin(base_url, item) for item in sel.xpath(XPATH_COMPANY_LIST).extract() if re.search('/organization/\S+', item)]


def add_company(company_crunchbase_link, funding_date):
    global effective_date

    sel = get_selector(company_crunchbase_link)

    company = Company(name=sel.xpath(XPATH_COMPANY_NAME).extract()[0],
                      description=sel.xpath(XPATH_COMPANY_DESCRIPTION).extract()[0],
                      crunchbase_link=company_crunchbase_link,
                      site_link=sel.xpath(XPATH_COMPANY_SITE_LINK).extract()[0],
                      linkedin_link=sel.xpath(XPATH_COMPANY_LINKEDIN_LINK).extract()[0],
                      effective_date=effective_date
                      )

    session.add(company)

    try:
        session.commit()
    except IntegrityError:
        return None

    funging = Funding(company_id=company.company_id,
                      funding_date=funding_date,
                      funding_round=sel.xpath(XPATH_COMPANY_FUNDING_ROUND).extract(),
                      funding_amount=sel.xpath(XPATH_COMPANY_FUNDING_AMOUNT).extract()
                      )

    session.add(funging)

    try:
        session.commit()
    except IntegrityError:
        return None

    team_member_urls = sel.xpath(XPATH_TEAM_MEMBER_LIST).extract()

    return company.company_id, [urlparse.urljoin(base_url, team_member_url) for team_member_url in team_member_urls]


def add_team_members(company_id, team_member_urls):
    for team_member_url in team_member_urls:
        sel = get_selector(team_member_url)

        TeamMember(company_id=company_id,
                   full_name=sel.xpath(XPATH_TEAM_MEMBER_FULL_NAME).extract(),
                   position=sel.xpath(XPATH_TEAM_MEMBER_POSITION).extract(),
                   crunchbase_link=team_member_url,
                   linkedin_link=sel.xpath(XPATH_TEAM_MEMBER_LINKEDIN_LINK).extract(),
                   personal_details=sel.xpath(XPATH_TEAM_MEMBER_PERSONAL_DETAILS).extract()
                   )


def main():
    funding_dates = get_funding_dates()

    for funding_block in funding_dates:
        funding_date = funding_block.xpath('text()').extract()[0]
        funding_date_date = datetime.datetime.strptime(funding_date, '%B %d, %Y').date()
        company_list = load_company_list(funding_block)
        for company_url in company_list:
            company_id, team_member_urls = add_company(company_url, funding_date_date)
            add_team_members(company_id, team_member_urls)

        
if __name__ == '__main__':
    main()