#!/usr/bin/env python3
import sys
import requests
from bs4 import BeautifulSoup
import threading
import queue
from urllib.parse import urlparse, urljoin
from termcolor import colored
import argparse

class Crawler:
    def __init__(self, seed_url, num_threads=10):
        self.seed_url = seed_url
        self.base_domain = urlparse(seed_url).netloc.replace("www.", "")
        self.to_crawl_queue = queue.Queue()
        self.to_crawl_queue.put(seed_url)
        self.crawled_urls = {seed_url}
        self.found_links = []
        self.lock = threading.Lock()
        self.num_threads = num_threads
        
        print(colored(f"[*] Starting crawler on domain: {self.base_domain}", 'cyan'))
        print(colored(f"[*] Using {self.num_threads} threads.", 'cyan'))

    def request(self, url):
        header = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0"}
        try:
            response = requests.get(url, headers=header, timeout=5, verify=False, allow_redirects=True)
            return response.text
        except requests.exceptions.RequestException:
            return None

    def get_links(self, base_url, html):
        links = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            tags_a = soup.find_all("a", href=True)
            for tag in tags_a:
                link = tag["href"]
                absolute_link = urljoin(base_url, link)
                links.append(absolute_link)
            return links
        except Exception:
            return []

    def worker(self):
        while not self.to_crawl_queue.empty():
            try:
                url = self.to_crawl_queue.get()

                if self.base_domain not in urlparse(url).netloc:
                    continue

                html = self.request(url)
                if html:
                    print(colored(f"[+] Crawling: {url}", 'green'))
                    with self.lock:
                        self.found_links.append(url)
                    
                    new_links = self.get_links(url, html)
                    for link in new_links:
                        with self.lock:
                            if link not in self.crawled_urls:
                                self.crawled_urls.add(link)
                                self.to_crawl_queue.put(link)
            finally:
                self.to_crawl_queue.task_done()

    def start(self, output_file=None):
        threads = []
        for _ in range(self.num_threads):
            t = threading.Thread(target=self.worker)
            t.daemon = True
            t.start()
            threads.append(t)

        self.to_crawl_queue.join()
        
        print(colored("\n--- Crawling Finished ---", 'magenta'))
        print(colored(f"[+] Total unique links found: {len(self.found_links)}", 'cyan'))

        if output_file:
            print(colored(f"[*] Saving results to '{output_file}'...", 'blue'))
            with open(output_file, 'w') as f:
                for link in sorted(self.found_links):
                    f.write(link + '\n')
            print(colored("[+] Results saved successfully!", 'green'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Web Crawler v2.0 - A multi-threaded web crawler for reconnaissance.")
    parser.add_argument("url", help="The starting URL to crawl (e.g., https://example.com)")
    parser.add_argument("-t", "--threads", type=int, default=10, help="Number of threads to use (default: 10)")
    parser.add_argument("-o", "--output", help="Output file to save the found links")

    args = parser.parse_args()

    try:
        crawler = Crawler(args.url, args.threads)
        crawler.start(args.output)
    except KeyboardInterrupt:
        print(colored("\n[!] Program interrupted by user.", 'red'))
        sys.exit(0)