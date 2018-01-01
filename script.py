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
import re
import requests


#
# Config
#
log_file = 'RapRapesYourEars.log'
log_level = logging.DEBUG
base_url = 'http://api.genius.com'
# artists_names = ['IAM', 'Damso']
artists_names = ['IAM']

#
# Functions
#
def get_lyrics_from_song_id(song_id, artist) :
	song_url = base_url + '/songs/' + str(song_id)
	json = requests.get(song_url, headers = headers).json()
	# Check if this song already exists in database
	if db.song.find({'_id' : song_id}).count() == 0 :
		logging.debug('Save song ' + str(song_id) + ' into database.')
		# Retrieve album linked to song
		# If no album is linked to this song, set "album" to None
		if json['response']['song']['album'] == None :
			album = None
		else :
			# If album doesn't exist yet in database, insert it
			album_id = json['response']['song']['album']['id']
			if db.album.find({'_id' : album_id}).count() == 0 :
				# Create album as a JSON Object
				album = {
					'_id' : album_id,
					'name' : json['response']['song']['album']['name'],
					'api_path' : json['response']['song']['album']['api_path'],
					'cover_art_url' : json['response']['song']['album']['cover_art_url'],
					'full_title' : json['response']['song']['album']['full_title'],
					'url' : json['response']['song']['album']['url']
				}
				# Save album into database
				db.album.insert_one(album)
			# If album exists in database, get it
			else :
				album = db.album.find_one({'_id' : album_id})
		# Create song as a JSON Object
		song = {
			'_id' : song_id,
			'name' : json['response']['song']['title'],
			'annotation_count' : json['response']['song']['annotation_count'],
			'api_path' : json['response']['song']['api_path'],
			'description' : json['response']['song']['description'],
			'embed_content' : json['response']['song']['embed_content'],
			'featured_video' : json['response']['song']['featured_video'],
			'full_title' : json['response']['song']['full_title'],
			'header_image_thumbnail_url' : json['response']['song']['header_image_thumbnail_url'],
			'header_image_url' : json['response']['song']['header_image_url'],
			'lyrics_owner_id' : json['response']['song']['lyrics_owner_id'],
			'lyrics_state' : json['response']['song']['lyrics_state'],
			'path' : json['response']['song']['path'],
			'pyongs_count' : json['response']['song']['pyongs_count'],
			'recording_location' : json['response']['song']['recording_location'],
			'release_date' : json['response']['song']['release_date'],
			'song_art_image_thumbnail_url' : json['response']['song']['song_art_image_thumbnail_url'],
			'song_art_image_url' : json['response']['song']['song_art_image_url'],
			'stats' : json['response']['song']['stats'],
			'title' : json['response']['song']['title'],
			'title_with_featured' : json['response']['song']['title_with_featured'],
			'url' : json['response']['song']['url'],
			'album_id' : json['response']['song']['album']['id'] if json['response']['song']['album'] != None else None,
			'youtube' : json['response']['song']['media'][0]['url'] if (len(json['response']['song']['media']) != 0 and json['response']['song']['media'][0]['provider'] == 'youtube') else None,
			'artist' : artist,
			'album' : album,
			'creation_date' : datetime.datetime.utcnow()
		}
		# Get lyrics
		page = requests.get('http://genius.com' + json['response']['song']['path'])
		html = BeautifulSoup(page.text, 'html.parser')
		song['lyrics'] = html.find('div', class_='lyrics').get_text()
		# Remove script tags that they put in the middle of the lyrics
		[h.extract() for h in html('script')]
		lyrics = html.find('div', class_='lyrics').get_text()
		lyrics = re.sub("\[.*?\]", "", lyrics)
		song['lyrics_clean'] = lyrics
		# Save song in database
		db.song.insert_one(song)
	else :
		logging.debug('Song ' + str(song_id) + ' already exists in database.')

def get_songs_from_artist_id(artist) :
	artist_id = artist['_id']
	artist_url = base_url + '/artists/' + str(artist_id) + '/songs'
	params = {'per_page': 50, 'page': 1}
	# Loop over pages
	while True:
		response = requests.get(artist_url, params=params, headers=headers).json()
		songs = response['response']['songs']
		logging.debug('Retrieving page ' + str(params['page']) + ' of songs list.')
		for song in songs:
			get_lyrics_from_song_id(song['id'], artist)
		if response['response']['next_page'] == None :
			break
		else :
			params['page'] = response['response']['next_page']

def save_artist_into_db(artist_id) :
	# Get artist info through the Genius API
	artist_url = base_url + '/artists/' + str(artist_id)
	json = requests.get(artist_url, headers=headers).json()
	# Check if artist is not already into the database
	if db.artist.find({'_id' : artist_id}).count() == 0 :
		# Create artist as a JSON Object
		artist = {
			'_id' : json['response']['artist']['id'],
			'name' : json['response']['artist']['name'],
			'alternate_names' : json['response']['artist']['alternate_names'],
			'api_path' : json['response']['artist']['api_path'],
			'description' : json['response']['artist']['description'],
			'facebook_name' : json['response']['artist']['facebook_name'],
			'followers_count' : json['response']['artist']['followers_count'],
			'header_image_url' : json['response']['artist']['header_image_url'],
			'image_url' : json['response']['artist']['image_url'],
			'instagram_name' : json['response']['artist']['instagram_name'],
			'is_meme_verified' : json['response']['artist']['is_meme_verified'],
			'is_verified' : json['response']['artist']['is_verified'],
			'twitter_name' : json['response']['artist']['twitter_name'],
			'url' : json['response']['artist']['url'],
			'iq' : json['response']['artist']['iq'],
			'creation_date' : datetime.datetime.utcnow()
		}
		# Save artist in database
		logging.debug('Save artist ' + str(json['response']['artist']['name']) + ' into database.')
		db.artist.insert_one(artist)
	else :
		artist = db.artist.find_one({'_id' : artist_id})
	return artist


def get_artist_id_from_artist_name(artist_name) :
	search_url = base_url + '/search'
	params = {'q': artist_name}
	response = requests.get(search_url, params=params, headers=headers).json()
	artist_id = 0
	for hit in response['response']['hits'] :
		if hit['result']['primary_artist']['name'].lower() == artist_name.lower() :
			artist_id =  hit['result']['primary_artist']['id']
			return artist_id
	return artist_id

def main() :
	global conf, db, headers
	# Init logs
	logging.basicConfig(filename = log_file, filemode = 'w+', format = '%(asctime)s  |  %(levelname)s  |  %(message)s', datefmt = '%m/%d/%Y %I:%M:%S %p', level = log_level)
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
	# Drop all tables (artist, song, lyrics and album)
	db.artist.drop()
	db.album.drop()
	db.song.drop()
	headers = {'Authorization': 'Bearer ' + conf['bearer']}
	for artist_name in artists_names :
		artist_id = get_artist_id_from_artist_name(artist_name)
		logging.debug('The artist id for ' + artist_name + ' is : ' + str(artist_id) + '.')
		if artist_id == 0 :
			logging.error('This artist name doesn\'t exist in Genius.com')
			exit()
		else :
			artist = save_artist_into_db(artist_id)
			get_songs_from_artist_id(artist)
	logging.info('End')


#
# Main
#
if __name__ == '__main__' :
	main()
