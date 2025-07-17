#!/usr/bin/env python3
import sys
import requests
from bs4 import BeautifulSoup
import threading
import queue
from urllib.parse import urlparse, urljoin
from termcolor import colored
import argparse
import re
import os
import json

class EmailFinder:
    def __init__(self, seed_url, num_threads=10, max_depth=2, patterns_dir=None):
        self.seed_url = seed_url
        self.base_domain = urlparse(seed_url).netloc.replace("www.", "")
        self.max_depth = max_depth
        self.num_threads = num_threads
        self.to_crawl_queue = queue.Queue()
        self.to_crawl_queue.put((seed_url, 0))
        self.crawled_urls = {seed_url}
        self.found_secrets = {}
        self.lock = threading.Lock()
        self.patterns = self.load_patterns(patterns_dir)

        print(colored(f"[*] Starting Secret Finder on domain: {self.base_domain}", 'cyan'))
        print(colored(f"[*] Using {self.num_threads} threads with a max depth of {self.max_depth}.", 'cyan'))

    def load_patterns(self, patterns_dir):
        patterns = {}
        if not patterns_dir or not os.path.isdir(patterns_dir):
            print(colored(f"[-] Patterns directory '{patterns_dir}' not found or not specified.", 'red'))
            return patterns
            
        print(colored(f"[*] Loading patterns from '{patterns_dir}'...", 'blue'))
        for filename in os.listdir(patterns_dir):
            if filename.endswith('.json'):
                pattern_name = os.path.splitext(filename)[0]
                try:
                    with open(os.path.join(patterns_dir, filename), 'r') as f:
                        data = json.load(f)
                        patterns[pattern_name] = re.compile(data['regex'])
                        print(colored(f"  -> Pattern '{pattern_name}' loaded.", 'green'))
                except Exception as e:
                    print(colored(f"[-] Error loading pattern {filename}: {e}", 'red'))
        return patterns

    def request(self, url):
        header = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0"}
        try:
            response = requests.get(url, headers=header, timeout=5, verify=False, allow_redirects=True)
            return response.text
        except requests.exceptions.RequestException:
            return None

    def find_data(self, content, url):
        for name, regex in self.patterns.items():
            matches = regex.findall(content)
            if matches:
                with self.lock:
                    if name not in self.found_secrets:
                        self.found_secrets[name] = set()
                    for match in matches:
                        if match not in self.found_secrets[name]:
                            print(colored(f"  -> [{name.upper()}] Found in {url}: {match}", 'yellow'))
                            self.found_secrets[name].add(match)

    def get_links(self, base_url, html):
        links = set()
        try:
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup.find_all(['a', 'link'], href=True):
                links.add(urljoin(base_url, tag['href']))
            for tag in soup.find_all('script', src=True):
                links.add(urljoin(base_url, tag['src']))
            return links
        except Exception:
            return set()

    def worker(self):
        while not self.to_crawl_queue.empty():
            try:
                url, depth = self.to_crawl_queue.get()

                if depth > self.max_depth:
                    continue
                
                if self.base_domain not in urlparse(url).netloc:
                    continue

                content = self.request(url)
                if content:
                    print(f"[D={depth}] Crawling: {url}")
                    
                    self.find_data(content, url)
                    
                    if '<html' in content.lower():
                        new_links = self.get_links(url, content)
                        with self.lock:
                            for link in new_links:
                                if link not in self.crawled_urls:
                                    self.crawled_urls.add(link)
                                    self.to_crawl_queue.put((link, depth + 1))
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
        if not self.found_secrets:
            print(colored("[-] No secrets found.", 'red'))
            return

        print(colored("[+] Summary of Found Secrets:", 'cyan'))
        full_output = []
        for category, secrets in self.found_secrets.items():
            title = f"\n--- {category.upper()} ({len(secrets)}) ---"
            print(colored(title, 'yellow'))
            full_output.append(title)
            for secret in sorted(list(secrets)):
                print(secret)
                full_output.append(secret)
        
        if output_file:
            print(colored(f"\n[*] Saving results to '{output_file}'...", 'blue'))
            with open(output_file, 'w') as f:
                f.write('\n'.join(full_output).replace('\n\n', '\n'))
            print(colored("[+] Results saved successfully!", 'green'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Secret Finder v1.0 - A crawler to find secrets based on regex patterns.")
    parser.add_argument("-u", "--url", help="The starting URL to crawl", required=True)
    parser.add_argument("-t", "--threads", type=int, default=10, help="Number of threads to use (default: 10)")
    parser.add_argument("-d", "--depth", type=int, default=2, help="Maximum crawl depth (default: 2)")
    parser.add_argument("-p", "--patterns", help="Directory containing regex pattern files (.json)")
    parser.add_argument("-o", "--output", help="Output file to save the found secrets")

    args = parser.parse_args()

    try:
        crawler = EmailFinder(args.url, args.threads, args.depth, args.patterns)
        crawler.start(args.output)
    except KeyboardInterrupt:
        print(colored("\n[!] Program interrupted by user.", 'red'))
        sys.exit(0)