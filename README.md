# ExamTopics URL Finder

This script searches for valid discussion URLs from **ExamTopics** based on a given question number range.
It iterates through possible `UID` values for each question number and logs any URLs that exist.

## Features
- Multi-threaded search for faster results.
- Graceful shutdown on `Ctrl+C`.
- Logs valid URLs to `valid_urls.log`.
- Logs failed requests to `bad_requests.log`.
- Optional starting question number parameter.

## Requirements
- Python 3.7+
- `requests` library

## Install dependencies:
```pip install requests```

## Usage
Start from question 1:
```python retrieve_script.py```
Start from a specific question:
```python retrieve_script.py 114```
