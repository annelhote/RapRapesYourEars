# RapRapesYourEars
Study the evolution of the languages used into french rap lyrics.


## Installation
`> mkvirtualenv RapRapesYourEars`

`> workon RapRapesYourEars`

`> pip install bs4`

`> pip install pymongo`

`> pip install requests`


### Setup config
To get an access token, ask it to Genius on the API-Client page [https://genius.com/api-clients](https://genius.com/api-clients).
And click on "Generate Access Token".

Rename the conf.default.json file into conf.json and place your Genius Access Token instead of "put_here_your_bearer".

## Usage

### Launch mongo db
`> mongod`


### Execute script
`> cd RapRapesYourEars`

`> workon RapRapesYourEars`

`> python script.py`


## Licenses
[LGPL V3.0](http://www.gnu.org/licenses/lgpl.txt "LGPL V3.0")

[CECILL-C](http://www.cecill.info/licences/Licence_CeCILL-C_V1-fr.html "CECILL-C")