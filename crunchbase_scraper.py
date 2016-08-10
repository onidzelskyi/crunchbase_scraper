import datetime
import os
import time
import random

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

try:
    from itertools import izip_longest
except ImportError:
    from itertools import zip_longest as izip_longest

import requests

import logging

from scrapy import Selector

from selenium import webdriver

from pyvirtualdisplay import Display


from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from tables import Base, engine, Company, TeamMember, Funding


XPATH_COMPANY_LIST = '//div[@class="info-block"]/h4/a[contains(@href, "organization")]/@href'
XPATH_COMPANY_FUNDING_DATE = '//h2[@class="title_date"]'
XPATH_COMPANY_FUNDING_ROUND = '//table[@class="table container"]//a/text()'
XPATH_COMPANY_FUNDING_AMOUNT = '//table[@class="table container"]//td[2]/text()'
XPATH_COMPANY_CRUNCHBASE_LINK = '//div[@class="info-block"]//a/@href'
XPATH_COMPANY_SITE_LINK = '//div[@class="definition-list container"]//dd//a[@target="_blank"]/@href'
XPATH_COMPANY_LINKEDIN_LINK = '//dd[@class="social-links"]//a[@class="icons linkedin"]/@href'
XPATH_COMPANY_NAME = '//h1[@id="profile_header_heading"]//a/text()'
XPATH_COMPANY_DESCRIPTION = '//div[@class="definition-list container"]//dd[2]/text()'

XPATH_TEAM_MEMBER_LIST = '//div[@class="base info-tab people"]//ul[@class="section-list container"]'
XPATH_TEAM_MEMBER_FULL_NAME = '//div[@class="info-block"]/div[@class="large"]//a[@class="follow_card"]/text()'
XPATH_TEAM_MEMBER_POSITION = '//div[@class="info-block"]/div[@class="large"]/h5/text()'
XPATH_TEAM_MEMBER_CRUNCHBASE_LINK = '//div[@class="base info-tab people"]//div[@class="info-block"]//a/@href'
XPATH_TEAM_MEMBER_LINKEDIN_LINK = '//dd[@class="social-links"]/a[contains(@href, "linkedin")]/@href'
XPATH_TEAM_MEMBER_PERSONAL_DETAILS = '//div[@class="base info-tab description"]//div[@class="card-content box container card-slim"]//text()'

XPATH_CONTENT_BLOCKED = '//meta[contains(@content, "blocked")]'

base_url = 'https://www.crunchbase.com/'
funding_round_url = 'https://www.crunchbase.com/funding-rounds'
referer = None

user_agents = dict(chrome='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
                   safari='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/600.7.12 (KHTML, like Gecko) Version/8.0.7 Safari/600.7.12')

headers = {'User-Agent': user_agents['chrome'],
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'Cache-Control': 'max-age=0'}

MIN_TIMEOUT = 180
MAX_TIMEOUT = 240

logging.basicConfig(filename='crunchbase.log',
                    format='%(levelname)s:%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.INFO)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
Session.configure(bind=engine) 
session = Session()

display = Display(visible=0, size=(800, 600))
display.start()
browser = webdriver.Chrome()


def get_funding_date(funding_block):
    try:
        return datetime.datetime.strptime(funding_block.xpath('text()').extract_first(), '%B %d, %Y').date()
    except (TypeError, IndexError):
        return None


def get_funding_dates():
    sel = get_selector(funding_round_url, referer=referer)
    return sel.xpath(XPATH_COMPANY_FUNDING_DATE)


def get_selector(url, referer=None):
    time.sleep(random.randint(MIN_TIMEOUT, MAX_TIMEOUT))

    if referer:
        headers['Referer'] = referer

    logging.info('Get url')
    logging.info('url: %s', url)
    logging.info('headers: %s', headers)

    response = requests.get(url, headers=headers)
    rendered_content = render_content(response.content)
    sel = Selector(text=rendered_content)

    # Check if content was blocked
    if sel.xpath(XPATH_CONTENT_BLOCKED).extract_first():
        logging.error('Content was blocked. Exit')
        raise IOError('content was blocked.')

    return sel


def render_content(content):
    with open('raw_content.html', 'wb') as fout:
        fout.write(content)

    browser.get('file:///{}/raw_content.html'.format(os.getcwd()))

    return browser.page_source


def load_company_list(sel):
    return [urlparse.urljoin(base_url, item) for item in sel.xpath(XPATH_COMPANY_LIST).extract()]


def add_company(company_crunchbase_link, funding_date):
    logging.info('Process company url: %s', company_crunchbase_link)
    logging.info('Company funding date: %s', funding_date)

    sel = get_selector(company_crunchbase_link, referer=funding_round_url)

    company = Company(name=sel.xpath(XPATH_COMPANY_NAME).extract_first(),
                      description=sel.xpath(XPATH_COMPANY_DESCRIPTION).extract_first(),
                      crunchbase_link=company_crunchbase_link,
                      site_link=sel.xpath(XPATH_COMPANY_SITE_LINK).extract_first(),
                      linkedin_link=sel.xpath(XPATH_COMPANY_LINKEDIN_LINK).extract_first(),
                      funding_date=funding_date
                      )

    session.add(company)
    session.flush()

    funging = Funding(company_id=company.company_id,
                      funding_date=funding_date,
                      funding_round=sel.xpath(XPATH_COMPANY_FUNDING_ROUND).extract_first(),
                      funding_amount=sel.xpath(XPATH_COMPANY_FUNDING_AMOUNT).extract_first()
                      )

    logging.info('Company name: %s', company.name)
    logging.info('Company description: %s', company.description)
    logging.info('Company crunchbase_link: %s', company.crunchbase_link)
    logging.info('Company site_link: %s', company.site_link)
    logging.info('Company linkedin_link: %s', company.linkedin_link)

    logging.info('Company funding date: %s', funging.funding_date)
    logging.info('Company funding round: %s', funging.funding_round)
    logging.info('Company funding amount: %s', funging.funding_amount)

    session.add(company)
    session.add(funging)

    try:
        session.commit()
    except SQLAlchemyError as err:
        logging.error('company %s or funding %s cannot be inserted into DB. Error: %s', company, funging, err)

    block = sel.xpath(XPATH_TEAM_MEMBER_LIST)

    team_member_urls = [urlparse.urljoin(base_url, '{}{}'.format(item,'#/entity')) for item in block.xpath(XPATH_TEAM_MEMBER_CRUNCHBASE_LINK).extract()]

    team_members = []
    if team_member_urls:
        team_members = list(izip_longest(team_member_urls,
                           block.xpath(XPATH_TEAM_MEMBER_FULL_NAME).extract(),
                           block.xpath(XPATH_TEAM_MEMBER_POSITION).extract(),
                           [company_crunchbase_link],
                           fillvalue=company_crunchbase_link))

    logging.info('Company team members: %s', team_members)

    return company.company_id, team_members


def add_team_members(company_id, team_member_infos):
    logging.info('Processing company team members:')

    for team_member_info in team_member_infos:
        logging.info('Team member info: %s', team_member_info)

        sel = get_selector(team_member_info[0], referer=team_member_info[3])

        full_name = team_member_info[1],
        position = team_member_info[2],
        linkedin_link = sel.xpath(XPATH_TEAM_MEMBER_LINKEDIN_LINK).extract_first(),
        personal_details = sel.xpath(XPATH_TEAM_MEMBER_PERSONAL_DETAILS).extract_first()

        if personal_details == 'Click/Touch ':
            personal_details = None

        team_member = TeamMember(company_id=company_id,
                                 full_name=full_name[0] if isinstance(full_name, tuple) else full_name,
                                 position=position[0] if isinstance(position, tuple) else position,
                                 crunchbase_link=team_member_info[0][0] if isinstance(team_member_info[0], tuple) else team_member_info[0],
                                 linkedin_link=linkedin_link[0] if isinstance(linkedin_link, tuple) else linkedin_link,
                                 personal_details=personal_details[0] if isinstance(personal_details, tuple) else personal_details)

        logging.info('Team member full_name: %s', team_member.full_name)
        logging.info('Team member position: %s', team_member.position)
        logging.info('Team member crunchbase_link: %s', team_member.crunchbase_link)
        logging.info('Team member linkedin_link: %s', team_member.linkedin_link)
        logging.info('Team member personal_details: %s', team_member.personal_details)

        session.add(team_member)

    try:
        session.commit()
    except SQLAlchemyError as err:
        logging.error('Team member %s cannot be inserted into DB. Error: %s', team_member.full_name, err)


def main():
    funding_dates = get_funding_dates()

    for funding_block in funding_dates:
        funding_date = get_funding_date(funding_block)
        company_list = load_company_list(funding_block)

        logging.info('Funding date: %s', funding_date)
        logging.info('Company list: %s', company_list)

        for company_url in company_list:
            company_id, team_members = add_company(company_url, funding_date)
            add_team_members(company_id, team_members)

        
if __name__ == '__main__':
    main()
