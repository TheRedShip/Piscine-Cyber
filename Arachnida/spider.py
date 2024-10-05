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

import sys
import requests
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from threading import Thread

def print_carriage_return(text: str) -> None:
	sys.stdout.write("\r" + text)
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

	def get_links(self, url: str) -> list[str]:
		ret: list[str] = []

		response = requests.get(url)
		if response.status_code != 200:
			return
		
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

		if (self.depth > 1):
			for link in links:
				reqThread = RequestThread(link, self.spider, self.depth - 1)
				reqThread.start()

				self.spider.threads.append(reqThread)


class Spider:
	def __init__(self, url: str, other_website: bool = False, threading=False) -> None:
		self.base_url:		str				= get_base_url(url)
		self.url:			str				= url
		self.other_website: bool			= other_website
		self.threading:		bool			= threading

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
	extensions: list[str] = ["jpg", "jpeg", "png", "gif", "svg", "webp"]

	for tag in soup.find_all("img"):
		if (not "src" in tag.attrs):
			continue
		
		src = tag["src"]
		if (not src.endswith(tuple(extensions))):
			continue

		ret.append(src)

	return ret

def main() -> None:
	url = "https://42.fr/"

	print(f"Starting urls crawling on {url}..")

	spider = Spider(url)
	spider.crawl(3)
	
	print(f"\nStarting images crawling on {len(spider.urls_content)} urls..")

	images = {}
	urls_content = spider.get_urls_content()
	for url, content in urls_content.items():
		images[url] = get_images(content)
		print_carriage_return(f"Found {sum([len(image) for image in images.values()])} urls with images..")


if __name__ == "__main__":
	main()