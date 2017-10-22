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
artist_name = "IAM"

#
# Functions
#
def get_lyrics_from_song_id(song_id) :
	logging.debug('Collect lyrics from song : ' + str(song_id))
	song_url = base_url + '/songs/' + str(song_id)
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
			'text': html.find('div', class_='lyrics').get_text(),
			'creation_date': datetime.datetime.utcnow()
		}
		# Save lyrics in database
		db.lyrics.insert_one(lyric)

def get_songs_from_artist_id(artist_id) :
	artist_url = base_url + '/artists/' + str(artist_id) + '/songs'
	params = {"per_page": 50, "page": 1}
	# Loop over pages
	while True:
		response = requests.get(artist_url, params=params, headers=headers).json()
		songs = response["response"]["songs"]
		logging.debug('Retrieving page ' + str(params['page']) + ' of songs list.')
		for song in songs:
			get_lyrics_from_song_id(song["id"])
		if len(songs) < 50:
			break
		else :
			params["page"] = response["response"]["next_page"]

def get_artist_id_from_artist_name(artist_name) :
	search_url = base_url + '/search'
	params = {'q': artist_name}
	response = requests.get(search_url, params=params, headers=headers).json()
	artist_id = 0
	for hit in response["response"]["hits"] :
		if hit["result"]["primary_artist"]["name"].lower() == artist_name.lower() :
			artist_id =  hit["result"]["primary_artist"]["id"]
	return artist_id

def main() :
	global conf, db, headers
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
	logging.debug('Connected to the Mongo database.')
	headers = {'Authorization': 'Bearer ' + conf['bearer']}
	artist_id = get_artist_id_from_artist_name(artist_name)
	logging.debug('The artist id for ' + artist_name + ' is : ' + str(artist_id) + '.')
	if artist_id == 0 :
		logging.error('This artist name doesn\'t exist in Genius.com')
		exit()
	else :
		get_songs_from_artist_id(artist_id)
	logging.info('End')


#
# Main
#
if __name__ == '__main__' :
	main()