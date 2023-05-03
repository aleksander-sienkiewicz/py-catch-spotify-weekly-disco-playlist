# import necessary modules
import time
import spotipy#spotify python library
from spotipy.oauth2 import SpotifyOAuth #for authenticating token
from flask import Flask, request, url_for, session, redirect #flask library imports

app = Flask(__name__)#initiallizing flask op


#flask allows us to store token inside of a session
#call the session name what ever u want
app.config['SESSION_COOKIE_NAME'] = 'Spoitfy Cookie'


#basically were gonna put our authentication for the whole app in here, and have it get specific access
#on its own, this abstracts it more. the alternative to this is getting specific api tokens for each action u need 
#when we use oath and get it authenticated here, were gonna get a token value that makes it so users can stay signed in 

#set a random secret key to sign the cookie, helps prevent unorthd access, more seccure
app.secret_key = 'YOUR_SECRET_KEY'#this value will be used to sign in to the session

# set the key for the token info in the session dictionary
TOKEN_INFO = 'token_info'


#now were going to create 3 dif routes for our program: login, redirect, and save-disco-weekly

# route to handle logging in, this will be home route
@app.route('/')
def login():
    # create a SpotifyOAuth instance and get the authorization URL
    auth_url = create_spotify_oauth().get_authorize_url()#this creates the url
    #were using this off of spotify oath lib. its a method - generates autorization URL


    return redirect(auth_url)#this is us redirecting our user to the new url we built.

# route to handle the redirect URI after authorization
@app.route('/redirect')
def redirect_page():
    session.clear()#clear all previous data from sessions
    # get the authorization code from the request parameters
    code = request.args.get('code')#the auth code in the request parametres is extracted w the method, put it in code
   
    # exchange the authorization code for an access token and refresh token
    #get access tken from creat spot outh object, it takes our auth code and gives us an access token
    token_info = create_spotify_oauth().get_access_token(code)#those r like the specific keys u need for specific functions, 
    #honestly was so scared that i was gonna have to get like 3 dif keys but this is so blessed <3
    #but like ig its 2023 why would u ever need to do that lol

    # save the token info in the session
    session[TOKEN_INFO] = token_info#take token info, from above method call
    # redirect the user to the save_discover_weekly route
    return redirect(url_for('save_discover_weekly',_external=True))#redirect 

# route to save the Discover Weekly songs to a playlist
@app.route('/saveDiscoverWeekly')
def save_discover_weekly():
    try: #first thing u do 
        # try to get the token info from the session
        token_info = get_token()
    except:
        # if the token info is not found, redirect the user to the login route
        print('User not logged in')#print users not logged in 
        return redirect("/")#redirect

    # create a Spotipy instance with the access token
    sp = spotipy.Spotify(auth=token_info['access_token'])#library helps so much

    # get the user's playlists
    current_playlists =  sp.current_user_playlists()['items']#calls for users playlists, return all of them cuz we dont know where it 
    #is yet, so cant put a cap on it
    discover_weekly_playlist_id = None
    saved_weekly_playlist_id = None

    # find the Discover Weekly and Saved Weekly playlists
    for playlist in current_playlists:#look thru every playlist
        if(playlist['name'] == 'Discover Weekly'):#if name matches
            discover_weekly_playlist_id = playlist['id']#find the playlist id, and set that to the playlist id
        if(playlist['name'] == 'Saved Weekly'):
            saved_weekly_playlist_id = playlist['id']
    
    # if the Discover Weekly playlist is not found, return an error message
    if not discover_weekly_playlist_id:#if theres none at all
        return 'Discover Weekly not found.'#we can say there was 
    
    if not saved_weekly_playlist_id:
        new_playlist=sp.user_playlist_create(user_id, 'Saved Weekly', True)
        saved_weekly_playlist_id = new_playlist['id']

    
    # get the tracks from the Discover Weekly playlist
    discover_weekly_playlist = sp.playlist_items(discover_weekly_playlist_id)#find the songs from in the playlist
    song_uris = []#create list for the uri's 
    for song in discover_weekly_playlist['items']:#for songs in the playlist
        song_uri= song['track']['uri']#the one uri is track, uri
        song_uris.append(song_uri)#append that to the list
    
    
    #to get the user id

    user_id = sp.current_user()['id']
    # add the tracks to the Saved Weekly playlist
    sp.user_playlist_add_tracks("user_id", saved_weekly_playlist_id, song_uris, None)#add tracks to the new playlist
#use user_playlist_add_tracks mmethod
    # return a success message
    return ('Discover Weekly songs added successfully')

# function to get the token info from the session+error handling
def get_token():
    token_info = session.get(TOKEN_INFO, None)#retrieve token,
    if not token_info:
        # if theres no token, they can login for a new token. could be a timeout situation
        redirect(url_for('login', _external=False))#redirect to login 
    
    # check if the token is expired and refresh it if necessary
    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60# compare the time now, 
    if(is_expired):#if its expired
        spotify_oauth = create_spotify_oauth()#create new oauth
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])#refresh token, 
        #give it to token_info to use

    return token_info#return new token ;D

#create the ouath
def create_spotify_oauth():
    return SpotifyOAuth(#when u hover over this struct, vscode tell u what parametres the library needs.
        client_id = '9e7823b029624ecd9f054eed6b63a9e8',#alr revoked these dw <3
        client_secret = '5c480d2b9f2148ba8edbe4a5a4d2ea78',
        redirect_uri = url_for('redirect_page', _external=True),#gonna use our redirect route here 
        scope='user-library-read playlist-modify-public playlist-modify-private'#using 3 dif scopes
    )#user lib read allows us to read our users laylist info, including songs
#allows us to modify public playlist, and modify private playlists, when making future apps u always need to check scopes in app doc. <3

app.run(debug=True)#so our flask app starts

#next step is to host it on a server, so it runs on its own. u can time it so it calls weekly, since u authenticated once it will always work.
