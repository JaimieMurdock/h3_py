import h3_py.h3 as h3
import os
import sys
import argparse
from lxml import etree as ET

def main():
	parser = argparse.ArgumentParser(description='Control an instance of Heritrix 3')
	parser.add_argument('url', help='URL for the crawl job. Ex. https://localhost:6440/engine/job/testcrawl')
	parser.add_argument('action', choices=['start','stop','cycle'])

	args = parser.parse_args()

	if args.action=='start':
		build_and_start_crawl(args.url)
	if args.action=='stop':
		stop_running_crawl(args.url)
	if args.action=='cycle':
		cycle_running_crawl(args.url)

def cycle_running_crawl(url):
	config_path = h3.get_config_path(url)
	if not os.access(config_path, os.R_OK) or not os.access(config_path, os.W_OK):
		print("Cannot access crawler config {}".format(config_path))
		return False
		
	if stop_running_crawl(url):
		if cycle_crawl_config(url):
			if build_and_start_crawl(url):
				print("Crawl Cycled Successfully")
				return

	print("Error cycling crawl")
	return False



def stop_running_crawl(url):
	status = h3.get_crawl_status(url)
	available_actions = h3.get_available_actions(url)
	print("Status: %s" %status)
	if status != h3.Crawl_Status.running:
		print("Expected status {0}, found {1}".format(h3.Crawl_Status.running, status))
		return


	if status == h3.Crawl_Status.running and "pause" in available_actions:
		h3.pause(url)
		status = h3.get_crawl_status(url)
		available_actions = h3.get_available_actions(url)

	if status == h3.Crawl_Status.paused and "checkpoint" in available_actions:
		h3.checkpoint(url)
		status = h3.get_crawl_status(url)
		available_actions = h3.get_available_actions(url)

	if status == h3.Crawl_Status.paused and "terminate" in available_actions:
		h3.terminate(url)
		status = h3.get_crawl_status(url)
		available_actions = h3.get_available_actions(url)

	if status == h3.Crawl_Status.finished and "teardown" in available_actions:
		h3.teardown(url)
		status = h3.get_crawl_status(url)
		available_actions = h3.get_available_actions(url)

	if status == h3.Crawl_Status.unbuilt:
		print("Crawl Stopped")
		return True
	return False

def cycle_crawl_config(url):
	status = h3.get_crawl_status(url)
	available_actions = h3.get_available_actions(url)
	if status == h3.Crawl_Status.unbuilt and "build" in available_actions:
		config_path = h3.get_config_path(url)
		h3.increment_crawl_number(url,config_path,config_path)
		return True
	return False



def build_and_start_crawl(url):
	status = h3.get_crawl_status(url)
	available_actions = h3.get_available_actions(url)

	if status == h3.Crawl_Status.unbuilt and "build" in available_actions:
		h3.build(url)
		status = h3.get_crawl_status(url)
		available_actions = h3.get_available_actions(url)

	if status == h3.Crawl_Status.ready and "launch" in available_actions:
		h3.launch(url)
		status = h3.get_crawl_status(url)
		available_actions = h3.get_available_actions(url)

	if status == h3.Crawl_Status.paused and "unpause" in available_actions:
		h3.unpause(url)
		print("Crawl Started")
		return True
	return False

if __name__ == "__main__":
	main()