# required packages: selenium, pytesseract, pdf2image, openai, requests, easyocr, opencv-python
# required binaries: tesseract, poppler, selenium webdriver

import csv
import time
import requests
import os

from pdf2image import convert_from_path

import pytesseract
from PIL import Image
import easyocr
import cv2
import numpy as np

import openai

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from watermark import get_grayscale, remove_noise, thresholding, dilate, erode, opening, canny, deskew, match_template
from db import insert_document_id, check_document_id_exists

def format_with_chat_gpt(ocr_text: str) -> str:
    openai.api_key = os.getenv('OPENAI_API_KEY')
    message = f'Return only a JSON structured body of the foreclosure details Document ID, Date Added, Record Date, Auction Date/time, County, Mortgagor First Name, Mortgagor Last Name, Property Address, Property City, Property State, Property Zip Code, Trustee Name, Mortgagee Bank Name, Instrument No. in {ocr_text}'
    response = openai.chat.completions.create(model='gpt-4', messages=[{'role': 'user', 'content': message}], max_tokens=1500)
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
        reader = easyocr.Reader(['en'])
        for image in images:
            # image = get_grayscale(image)
            # text = pytesseract.image_to_string(image)
            img_array = np.array(image, dtype=np.uint8)
            # If the image is in color (BGR/RGB), convert it to grayscale
            if len(img_array.shape) == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
            results = reader.readtext(img_array)
            for (bbox, text, prob) in results:
                ocr_text += f'{text} '

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
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'doclinks')))

    while True:
        try:
            b_tag = driver.find_element(By.TAG_NAME, 'b') 
            is_empty_page = b_tag.text == 'This Search is currently unavailable. Please check back soon.'
            if is_empty_page:
                break

            
        except NoSuchElementException:
            doc_links = driver.find_elements(By.CLASS_NAME, 'doclinks')
            wait = WebDriverWait(driver, 10)
            for link in doc_links:
                doc_name = link.text
                link_url = link.get_attribute('href')
                if check_document_id_exists(doc_name):
                    print('Document already exists in database')
                else:
                    # insert_document_id(doc_name, link_url)
                    print(doc_name)
                    print(link_url)
                    # save_document(link_url, doc_name)

            # Locate the pagination links
            pagination_links = driver.find_elements(By.CSS_SELECTOR, "tr.pagination-ys a")

            # Check if we are on the last page or if there are no more pagination links
            if not pagination_links:
                print("No more pages to navigate.")
                break

            # Click the next page link (modify this to suit how your pagination works)
            next_page_link = pagination_links[-1]  # Assuming the last link is the 'next' page
            next_page_link.click()

            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'doclinks')))
            # print("Error occurred in navigation.")

    driver.quit()

if __name__ == '__main__':
    main()



