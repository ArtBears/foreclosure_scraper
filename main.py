# required packages: selenium, pytesseract, pdf2image, openai, requests
# required binaries: tesseract, poppler, selenium webdriver

import csv
import time
import requests
import os

from pdf2image import convert_from_path

import pytesseract
from PIL import Image

import openai

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

def format_with_chat_gpt(ocr_text: str) -> str:
    openai.api_key = os.getenv('OPENAI_API_KEY')
    message = f'Return only a JSON structured body of the foreclosure details in {ocr_text}'
    response = openai.chat.completions.create(model='gpt-3.5-turbo', messages=[{'role': 'user', 'content': message}], max_tokens=1500)
    print(response.choices[0].message.content)

def save_document(link_url: str, doc_name: str) -> bool:
    ocr_text = ''
    response = requests.get(link_url)
    if response.status_code == 200:
        print('Download Successful')
    else:
        print('Error')
        return False

    local_file_path = f'docs/{doc_name}.pdf'

    with open(local_file_path, 'wb') as file:
        file.write(response.content)
        images = convert_from_path(local_file_path)
        for image in images:
            # remove watermark using https://github.com/zuruoke/watermark-removal

            text = pytesseract.image_to_string(image)
            ocr_text += f'\n {text}'

        format_with_chat_gpt(ocr_text)
        # print(ocr_text)
        return True

def main():

    driver = webdriver.Chrome(keep_alive=True)
    driver.get('https://www.cclerk.hctx.net/applications/websearch/FRCL_R.aspx#')

    driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_rbtlDate_1').click()

    year = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_ddlYear')
    month = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_ddlMonth')

    select_year = Select(year)
    select_month = Select(month)

    select_year.select_by_visible_text('2023')
    select_month.select_by_visible_text('November')

    driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_btnSearch').click()
    time.sleep(1.0)

    doc_links = driver.find_elements(By.CLASS_NAME, 'doclinks')
    doc_name = doc_links[1].text
    link_url = doc_links[1].get_attribute('href')

    print(doc_name)
    print(link_url)
    save_document(link_url, doc_name)

if __name__ == '__main__':
    main()



