# Python Web Recon Tools

This repository contains a set of web reconnaissance (RECON) tools developed in Python.

The base concepts for these scripts were learned in cybersecurity courses from **Solyd**. From that foundation, they were completely rewritten and enhanced with new features to become more practical and powerful pentesting tools for real-world scenarios.

## Tools Included

### 1. Web Crawler (`crawler.py`)

A multi-threaded web crawler designed to quickly and efficiently map all accessible URLs within a specific target domain.

* **What it does:** Starting from a seed URL, it recursively navigates the site, handling relative links and staying strictly within the target's scope to build a complete map of all endpoints.
* **Enhanced Version:** The version in this repository is a significant upgrade from the original concept, including multithreading for high performance, scope control to prevent crawling external sites, and a professional command-line interface.
* **Basic Usage:**
    ```
    python3 crawler.py -u <seed_url> -t <threads> -o <output_file>
    ```

### 2. Secret Finder (`secret_finder.py`)

An advanced crawler that goes beyond just finding links. It uses a regex-based pattern engine to hunt for "secrets" and sensitive information within the content of pages, JavaScript files, and more.

* **What it does:** In addition to navigating the site, it applies a series of customizable patterns to find data such as email addresses, API keys, storage bucket links, and more.
* **Enhanced Version:** This tool evolved from a simple email finder into a secret-hunting framework. Enhancements include a pattern engine that loads from JSON files, crawl depth control, and a final categorized report.
* **Basic Usage:**
    ```
    python3 secret_finder.py -u <seed_url> -p <patterns_directory> -d <depth> -o <output_file>
    ```

## License

This project is licensed under the MIT License.
