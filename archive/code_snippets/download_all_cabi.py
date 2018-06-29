from splinter import Browser
import os
import urllib.request
import shutil
import zipfile


def get_links():
    browser = Browser('firefox')
    browser.visit('https://s3.amazonaws.com/capitalbikeshare-data/index.html')

    links = browser.find_by_css('#tbody-content a')
    #links = [link for link in links if link['href']]
    zip_links = []
    for link in links:
        link_text = link['href']
        with urllib.request.urlopen(link_text) as response:
            subtype = response.info().get_content_subtype()
            if subtype == 'zip':
                zip_links.append(link_text)

    return zip_links


def download_links(links):
    download_dir = '../cabi_data'
    if not os.path.exists(download_dir):
        os.mkdir(download_dir)
    for link in links:
        file_name = os.path.join(download_dir, link.split('/')[-1])
        print(file_name)
        # save file to disk
        with urllib.request.urlopen(link) as response, open(file_name, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        with zipfile.ZipFile(file_name, "r") as zip_ref:
            zip_ref.extractall(download_dir)

links = get_links()
download_links(links)
