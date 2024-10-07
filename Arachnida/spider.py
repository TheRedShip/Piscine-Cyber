# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    spider.py                                          :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: TheRed <TheRed@students.42.fr>             +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2024/10/05 13:01:41 by TheRed            #+#    #+#              #
#    Updated: 2024/10/05 13:01:41 by TheRed           ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

import os
import sys
import argparse
import requests
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from threading import Thread

def print_carriage_return(text: str) -> None:
	sys.stdout.write("\r" + text + " " * (100 - len(text)))
	sys.stdout.flush()

def get_base_url(url: str) -> str | None:
		parsed_url = urlsplit(url)
		if (parsed_url.netloc == "" or parsed_url.scheme == ""):
			return None

		return f"{parsed_url.scheme}://{parsed_url.netloc}/"

class RequestThread(Thread):
	def __init__(self, url: str, Spider: "Spider", depth: int = 1) -> None:
		Thread.__init__(self)
		
		self.spider:		Spider		= Spider
		self.url:			str			= url
		self.depth:			int			= depth

	def get_links(self, url: str) -> list[str] | None:
		ret: list[str] = []

		response = requests.get(url)
		if response.status_code != 200:
			return None
		
		soup = BeautifulSoup(response.text, "html.parser")
		self.spider.urls_content[url] = soup

		for a in soup.find_all("a"):
			if (not "href" in a.attrs):
				continue

			new_url = a["href"]
			new_base_url = get_base_url(new_url)
			if (new_base_url is None):
				new_base_url = self.spider.base_url

			if (new_base_url != self.spider.base_url and not self.spider.other_website):
				continue

			if (not new_url.startswith("http")):
				new_url = self.spider.base_url + new_url
			if new_url not in self.spider.urls:
				ret.append(new_url)
				self.spider.urls.append(new_url)
				print_carriage_return(f"Found {len(self.spider.urls)} urls..")
		
		return ret

	def run(self) -> None:
		links = self.get_links(self.url)
		if (links is None):
			return
		
		if (self.depth > 1):
			for link in links:
				reqThread = RequestThread(link, self.spider, self.depth - 1)
				reqThread.start()

				self.spider.threads.append(reqThread)


class Spider:
	def __init__(self, url: str, other_website: bool = False) -> None:
		self.base_url:		str				= get_base_url(url)
		self.url:			str				= url
		self.other_website: bool			= other_website

		self.threads:		list[Thread]	= []

		self.urls:			list[str]		= [url]
		self.urls_content:	dict[str, BeautifulSoup]	= {}

	def crawl(self, depth: int):
		reqThread = RequestThread(self.url, self, depth)
		reqThread.start()
		reqThread.join()

		for thread in self.threads:
			thread.join()
	
	def get_urls_content(self) -> dict[str, BeautifulSoup]:
		return self.urls_content


def get_images(soup: BeautifulSoup) -> list[str]:
	ret: list[str] = []
	extensions: list[str] = ["jpg", "jpeg", "png", "gif", "webp", "bmp"]

	for tag in soup.find_all("img"):
		if (not "src" in tag.attrs):
			continue
		
		src = tag["src"]
		if (not src.endswith(tuple(extensions))):
			continue

		ret.append(src)

	return ret

def download_images(images: dict[str, list[str]], folder: "str") -> None:
	if not os.path.exists(folder):
		os.mkdir(folder)

	i = 0
	
	for url in images:
		folder_name = f"{folder}/{urlsplit(url).netloc}"
		if not os.path.exists(folder_name):
			os.mkdir(folder_name)

		for image in images[url]:
			image_name = image.split("/")[-1]
			
			if (urlsplit(image).netloc == ''):
				image = url + image

			if (image.startswith("//")):
				image = "https:" + image
			
			try:
				response = requests.get(image)
				with open(f"{folder_name}/{image_name}", "wb") as f:
					f.write(response.content)
			except Exception as e: #bad name
				pass

			print_carriage_return(f"{i}/{sum([len(image) for image in images.values()])} | Downloaded from {urlsplit(url).netloc} {image_name}..")
			i += 1

def main() -> None:
	parser = argparse.ArgumentParser(description='Spider web crawler crawls recursively to a given depth and downloads images from the urls found.')
	parser.add_argument("url", help="The url to start crawling from")
	parser.add_argument('-r', '--recursive', help='Activates the recursive crawling', action='store_true')
	parser.add_argument('-l', '--limit', help='Depth limit for the spider', type=int, default=1)
	parser.add_argument('-p', '--path', help='Path to save the images', default='data')
	parser.add_argument('-o', '--other_website', help='Crawl other websites', action='store_true')
	args = parser.parse_args()

	if (get_base_url(args.url) is None):
		print("Correct URL format is required : http(s)://www.example.com")
		return
	
	print(f"Starting urls crawling on {args.url}..")

	spider = Spider(args.url, other_website=args.other_website)
	spider.crawl(args.limit)
	
	print(f"\nStarting images crawling on {len(spider.urls_content)} urls..")

	images = {}
	urls_content = spider.get_urls_content()
	for url, content in urls_content.items():
		images[url] = get_images(content)
		print_carriage_return(f"Found {sum([len(image) for image in images.values()])} urls with images..")

	download_images(images, "data")

if __name__ == "__main__":
	main()