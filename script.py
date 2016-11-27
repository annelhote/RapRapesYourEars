#!/usr/bin/python
# -*- coding: utf-8 -*-
# Execution example : python script.py
# Tuto : https://bigishdata.com/2016/09/27/getting-song-lyrics-from-geniuss-api-scraping/


#
# Libs
#
from bs4 import BeautifulSoup
import datetime
import json
import logging
import os
import pymongo
import requests


#
# Config
#
log_file = 'RapRapesYourEars.log'
log_level = logging.DEBUG
base_url = 'http://api.genius.com'


#
# Functions
#
def get_lyrics_from_song_id(song_id) :
	logging.info('Collect lyrics from song : ' + song_id)
	song_url = base_url + '/songs/' + song_id
	headers = {'Authorization': 'Bearer ' + conf['bearer']}
	json = requests.get(song_url, headers = headers).json()
	# Check if this song already exists in database
	if db.song.find({'_id' : song_id}).count() == 0 :
		# Create song as a JSON Object
		song = {
			'_id' : song_id,
			'name' : json['response']['song']['title'],
			'url' : json['response']['song']['url'],
			'release_date' : json['response']['song']['release_date'],
			'album_id' : json['response']['song']['album']['id'] if json['response']['song']['album'] != None else None,
			'creation_date' : datetime.datetime.utcnow()
		}
		# Save song in database
		db.song.insert_one(song)
	# Check if these lyrics already exist in database
	if db.lyrics.find({'_id' : song_id}).count() == 0 :
		page = requests.get('http://genius.com' + json['response']['song']['path'])
		html = BeautifulSoup(page.text, 'html.parser')
		# Remove script tags that they put in the middle of the lyrics
		[h.extract() for h in html('script')]
		# Create lyrics as a JSON Object
		lyric = {
			'_id': song_id,
			'text': html.find('lyrics').getText(),
			'creation_date': datetime.datetime.utcnow()
		}
		# Save lyrics in database
		db.lyrics.insert_one(lyric)


def get_songs_from_album_url(url) :
	logging.info('Collect songs from album : ' + url)
	page = requests.get(url)
	html = BeautifulSoup(page.text, 'html.parser')
	children = html.find_all('ul', class_ = 'song_list')[0].children
	for child in children :
		if child.name != None :
			get_lyrics_from_song_id(child['data-id'])

def main() :
	global conf, db
	# Init logs
	logging.basicConfig(filename = log_file, filemode = 'a+', format = '%(asctime)s  |  %(levelname)s  |  %(message)s', datefmt = '%m/%d/%Y %I:%M:%S %p', level = log_level)
	logging.info('Start')
	# Load conf file
	conf_file = os.path.join('conf', 'conf.json')
	if os.path.exists(conf_file) :
		with open(conf_file) as f :
			conf = json.load(f)
		logging.info('Conf file loaded')
	else :
		logging.error('No conf file provided or wrong path : ' + conf_file)
		sys.exit(0)
	# Connect to Mongo DB
	client = pymongo.MongoClient()
	db = client.RapRapesYourEars
	# IAM - L'école du micro d'argent
	get_songs_from_album_url('http://genius.com/albums/Iam/L-ecole-du-micro-d-argent')
	logging.info('End')


#
# Main
#
if __name__ == '__main__' :
	main()