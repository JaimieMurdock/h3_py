import h3_py.h3 as h3
import os
import sys
import argparse
import logging
import json
from lxml import etree as ET

logger = logging.getLogger(__name__)

def main():
	parser = argparse.ArgumentParser(description='Control an instance of Heritrix 3')
	parser.add_argument('url', help='URL for the crawl job. Ex. https://localhost:6440/engine/job/testcrawl')
	parser.add_argument('action', choices=['status','start','stop','pause','unpause','checkpoint','increment','cycle', 'report_hosts', 'report_threads'])
	parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
	parser.add_argument("--config_find_replace", action="append", help="json object containing xpath, regex, replacement to apply to the crawler config. ex: {'xpath':'./beans:bean[@id='simpleOverrides']/beans:property/beans:value','regex':'^myValue=.*$', 'replacement':'myValue=new_value'}")

	args = parser.parse_args()
	ret_val = True

	if args.action=='status':
		print(h3.get_crawl_status(args.url))
	
	if args.action=='start':
		if(args.config_find_replace):
			for replacement in args.config_find_replace:
				do_config_find_replace(args.url,replacement)
		ret_val=build_and_start_crawl(args.url)
	if not ret_val:
		logger.error("problem starting")
		sys.exit(-1)

	if args.action=='stop':
		ret_val=stop_running_crawl(args.url)
	if not ret_val:
		logger.error("problem stopping")
		sys.exit(-1)

	if args.action=='pause':
		ret_val=pause_running_crawl(args.url)
	if not ret_val:
		logger.error("problem pausing")
		sys.exit(-1)

	if args.action=='unpause':
		ret_val=unpause_paused_crawl(args.url)
	if not ret_val:
		logger.error("problem unpausing")
		sys.exit(-1)

	if args.action=='checkpoint':
		ret_val=checkpoint_paused_crawl(args.url)
	if not ret_val:
		logger.error("problem checkpointing")
		sys.exit(-1)

	if args.action=='increment':
		ret_val=cycle_crawl_config(args.url)
	if not ret_val:
		logger.error("problem incrementing warc prefix")
		sys.exit(-1)

	if args.action=='cycle':
		ret_val=cycle_running_crawl(args.url)
	if not ret_val:
		logger.error("problem cycling the crawl")
		sys.exit(-1)

	if args.action=='report_hosts':
		ret_val = get_report(args.url,h3.Crawl_Reports.hosts)

	if args.action=='report_threads':
		ret_val = get_report(args.url,h3.Crawl_Reports.thread)

def cycle_running_crawl(url):
	config_path = h3.get_config_path(url)
	if not os.access(config_path, os.R_OK) or not os.access(config_path, os.W_OK):
		logger.error("Cannot access crawler config {}".format(config_path))
		return False
		
	if stop_running_crawl(url):
		if cycle_crawl_config(url):
			if build_and_start_crawl(url):
				logger.info("Crawl Cycled Successfully")
				return

	logger.error("Error cycling crawl")
	return False



def stop_running_crawl(url):
	status = h3.get_crawl_status(url)
	available_actions = h3.get_available_actions(url)
	logger.info("Status: %s" %status)
	if status != h3.Crawl_Status.running:
		logger.error("Expected status {0}, found {1}".format(h3.Crawl_Status.running, status))
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
		logger.info("Crawl Stopped")
		return True
	return False

def pause_running_crawl(url):
	status = h3.get_crawl_status(url)
	available_actions = h3.get_available_actions(url)
	logger.info("Status: %s" %status)
	if status != h3.Crawl_Status.running:
		logger.error("Expected status {0}, found {1}".format(h3.Crawl_Status.running, status))
		return
	if status == h3.Crawl_Status.running and "pause" in available_actions:
		h3.pause(url)
		status = h3.get_crawl_status(url)
		available_actions = h3.get_available_actions(url)
	if status == h3.Crawl_Status.paused:
		logger.info("Crawl Paused")
		return True
	return False

def unpause_paused_crawl(url):
	status = h3.get_crawl_status(url)
	available_actions = h3.get_available_actions(url)
	logger.info("Status: %s" %status)
	if status != h3.Crawl_Status.paused:
		logger.error("Expected status {0}, found {1}".format(h3.Crawl_Status.paused, status))
		return
	if status == h3.Crawl_Status.paused and "unpause" in available_actions:
		h3.unpause(url)
		status = h3.get_crawl_status(url)
		available_actions = h3.get_available_actions(url)
	if status == h3.Crawl_Status.running:
		logger.info("Crawl Running")
		return True
	return False

def checkpoint_paused_crawl(url):
	status = h3.get_crawl_status(url)
	available_actions = h3.get_available_actions(url)
	logger.info("Status: %s" %status)
	if status != h3.Crawl_Status.paused:
		logger.error("Expected status {0}, found {2}".format(h3.Crawl_Status.paused, status))
		return
	if status == h3.Crawl_Status.paused and "checkpoint" in available_actions:
		h3.checkpoint(url)
		status = h3.get_crawl_status(url)
		available_actions = h3.get_available_actions(url)
	if status == h3.Crawl_Status.paused:
		logger.info("Crawl Checkpointed")
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

def do_config_find_replace(url, replacement_json):
	#print(replacement_json)
	instruction = json.loads(replacement_json)
	#print(instruction.keys())

	status = h3.get_crawl_status(url)
	available_actions = h3.get_available_actions(url)
	#print(status)
	#print(available_actions)
	if status == h3.Crawl_Status.unbuilt and "build" in available_actions:
		config_path = h3.get_config_path(url)
		logger.info("processing find/replace: {} {} {}".format(instruction["xpath"],instruction["regex"],instruction["replacement"]))
		h3.find_replace_xpath(url,config_path,config_path,instruction["xpath"],instruction["regex"],instruction["replacement"])


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
		logger.info("Crawl Started")
		return True
	return False

def get_report(url,report):
	report_url = url+"/report/"+report
	response = h3.get_crawljob_text_page(report_url)
	return True

if __name__ == "__main__":
	main()