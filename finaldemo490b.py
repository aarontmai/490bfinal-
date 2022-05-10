import streamlit as st
import serial 
import csv 
import requests
import http.client
import time
import random
import json
import spotipy
import webbrowser
import subprocess
import sys
import PySimpleGUI as sg
import cv2
import boto3
import pandas as pd 
import numpy as np
import os 
import s3fs
from tabulate import tabulate
from PIL import Image

#Global Variables and auth keys

#Amanzon Rekognition collection name
collectionId='' 
#s3 bucket name
bucket_name = ""
#init boto3 client
s3 = boto3.client('s3')
#init rekognition with keys
rekognition = boto3.client('rekognition',aws_access_key_id= '',
             aws_secret_access_key='',
             region_name='')

#Spotify Dashboard Auth IDs and keys 
user_profile = ''
#autorefreshtoken
spotify_token = ""
clientID = ''
clientSecret = ''
redirectURI = 'http://localhost:8888/callback'
endpoint_url = "https://api.spotify.com/v1/recommendations?"

 #spotify repos
uris_repo = []
query_tail = ''

#Aws methods:

#function checks to see a folder existence in our s3 bucket, each folder contains user id and a facial picture of the user
def folder_exists(bucket, path):
     #strip just so its easier to parse data 
    path = path.rstrip('/')
    resp = s3.list_objects(Bucket=bucket, Prefix=path, Delimiter='/',MaxKeys=1)
    return 'CommonPrefixes' in resp


#main function 
def main():
    happy_co ={"limit": 10,
               "market": "US",
               "seed_genres": "happy",
               "query_tail": 'valence=0.2&depth={}&tempo={}target_liveness={}&target_danceability={}&target_energy={}&arousal=.8&seed_track="60nZcImufyMA1MKQY3dcCH"'.format(
                   random.uniform(0.4, .8), random.uniform(100, 150),random.uniform(0.5, .9), random.uniform(0.5, .9), random.uniform(0.6, .9))}




    sad_co = {"limit": 10,
               "market": "US",
               "seed_genres": "sad",
               "query_tail": 'valence=0.5&depth=0.8&target_liveness={}&target_danceability={}&target_energy={}&arousal={}'.format(
                   random.uniform(0, .1), random.uniform(0, .2), random.uniform(0, .3), random.uniform(0, .5))}


    calm_co = {"limit": 10,
               "market": "US",
               "seed_genres": "chill",
               "query_tail": 'valence=0.5&depth=0.8&target_liveness={}&target_danceability={}&target_energy={}&arousal={}'.format(
                   random.uniform(0, .3), random.uniform(0, .5), random.uniform(0, .5), random.uniform(0.4, .7))}


    angry_co = {"limit":10,
    "market" :"US",
    "seed_genres":"hard-rock",
    "query_tail": 'valence={}&depth=0.8'.format(
                   random.uniform(0.2, .8))}


    surprise_co = {"limit":10,
    "market" :"US",
    "seed_genres":"edm",
    "query_tail": 'valence=0.2&depth=0.8&target_liveness=0.9&target_energy=0.7&arousal={}'.format(
                   random.uniform(0.5, .9))}


    fear_co = {"limit":10,
    "market" :"US",
    "seed_genres":"pop",
    "query_tail": 'valence={}&depth={}&target_liveness={}&seed_track="4G8gkOterJn0Ywt6uhqbhp"'.format(
                   random.uniform(0.4, .7), random.uniform(0.1, .4), random.uniform(0.3, .5))}


    disgust_co = {"limit":10,
    "market" :"US",
    "seed_genres":"piano&alt-rock",
    "query_tail": 'valence={}&depth={}&target_liveness={}&seed_track="1Q3bb5UXqAWr7Tjuno2xcq"'.format(
    random.uniform(0.5, .7), random.uniform(0, .8), random.uniform(0.6, .8))}
                        
    selector = {
                    'CALM': calm_co,
                    'SAD': sad_co,
                    'HAPPY': happy_co,
                    'SURPRISED': surprise_co,
                    'ANGRY': angry_co,
                    'DISGUSTED': disgust_co,
                    'FEAR': fear_co
                }
    #Musa's spotify methods
    def insert_playlist(user_profile, spotify_token, uris_repo, play_desc):
        endpoint_url = f"https://api.spotify.com/v1/users/{user_profile}/playlists"
        request_body = json.dumps({
                                    "name": "Demo 3: Playlist Generation",
                                    "description": "{}".format(play_desc),
                                     #"description": "playlist_test",
                                    "public": False 
                                    })

        response_pid = requests.post(url=endpoint_url, data=request_body, headers={"Content-Type":"application/json",
                                                                           "Authorization":"{}".format(spotify_token)})
        #insert playlist
        #print(response_pid.json())
        playlist_id = response_pid.json()['id']
        endpoint_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        playlist_link = f"https://api.spotify.com/v1/playlists/{playlist_id}"
        request_body = json.dumps({
                                    "uris": uris_repo
                                  })
        response_ti = requests.post(url=endpoint_url, data=request_body, headers={"Content-Type": "application/json",
                                                                           "Authorization":"{}".format(spotify_token)})

        playlist_link = (f"https://open.spotify.com/playlist/{playlist_id}")
        webbrowser.open_new(playlist_link)
        time.sleep(.02)
        uris_repo.clear()
        return response_ti.status_code


    def open_window_mp3():
        col1 = [    
                    [sg.Text(username, size=(20, 3), justification='left', font='Consolas 11')],
                    [sg.Text(similarity, size=(20, 3), justification='left', font='Consolas 11')],
                    [sg.Text(confidence, size=(20, 3), justification='right', font='Consolas 11')],
                    [sg.Text(data_emotion, size=(20, 3), justification='right', font='Consolas 11')]
                ]
        col2 = [[sg.Image('output.png', size =(4000,4000))]]

        layout = [[sg.Column(col1, element_justification='l' ), sg.Column(col2, element_justification='r')]]


        window = sg.Window("Statistics", layout, modal=True, resizable = True)
        choice = None
        while True:
            event, values = window.read()
            if event == "Exit" or event == sg.WIN_CLOSED:
                break
        
            window.close()
        
        def open_prompt():
            col1 = [    
                    [sg.Text(nofaces, size=(20, 3), justification='left', font='Consolas 11')],
                    [sg.Text(prompt, size=(20, 3), justification='left', font='Consolas 11')]
                    ]
            col2 = [[sg.Image('test.jpg', size =(4000,4000))]]

            layout = [[sg.Column(col1, element_justification='l' ), sg.Column(col2, element_justification='r')]]


            window = sg.Window("Statistics", layout, modal=True, resizable = True)
            choice = None
            while True:
                event, values = window.read()
                if event == "Exit" or event == sg.WIN_CLOSED:
                    break
        
                window.close()       
    
    #MP3 fucntions
    #built in linux music player, mpg123 audio decoder, currently just changing os directories to play music 
    def playmusic():
        dominantMood = face_emotion
        if dominantMood == 'HAPPY':
            os.chdir("Music")
            os.chdir("Happy")
            os.system("mpg123 -Z *.mp3")
        elif dominantMood == 'SAD':
            os.chdir("Music")
            os.chdir("Sad")
            os.system("mpg123 -Z *.mp3")
        elif dominantMood == 'ANGRY':
            os.chdir("Music")
            os.chdir("Angry")
            os.system("mpg123 -Z *.mp3")
        elif dominantMood == 'FEAR':
            os.chdir("Music")
            os.chdir("Fear")
            os.system("mpg123 -Z *.mp3")
        elif dominantMood == 'SUPRISED':
            os.chdir("Music")
            os.chdir("Surprise")
            os.system("mpg123 -Z *.mp3")
        elif dominantMood == 'DISGUSTED':
            os.chdir("Music")
            os.chdir("Disgust")
            os.system("mpg123 -Z *.mp3")
        elif dominantMood == 'CALM':
            os.chdir("Music")
            os.chdir("Neutral")
            os.system("mpg123 -Z *.mp3")

        return True


    #simple python gui for demonstration purposes 
    sg.theme('Light Green')

    # define the window layout
    layout = [
              [sg.Text('Biometric Media Player', size=(70, 3), justification='center', font='TimesNewRoman 25')],
              [sg.Image(filename='', key='image')],

              [sg.Button('MP3', size=(12, 3), font='TimesNewRoman 14'),
               sg.Button('Spotify', size=(12, 3), font='TimesNewRoman 14')]
             ]

    # create the window and show it without the plot
    window = sg.Window('Facetunes', layout, element_justification = 'c', location=(1600, 800), resizable = True)
    #Open webcam
    cap = cv2.VideoCapture(0)


    # ---===--- Event LOOP Read and display frames, operate the GUI --- #
    while True:
        event, values = window.read(timeout=20)
        ret, test = cap.read()
        #live camera feed with update 
        imgbytes = cv2.imencode('.png', test)[1].tobytes() 
        window['image'].update(data=imgbytes)
        if event == 'Exit' or event == sg.WIN_CLOSED:
            return
        
        
        #gui button press camera capture 
        elif event == 'MP3':
            cv2.imwrite('/home/nano/test.jpg',test)
            #rahdom indexing so photos dont get overwritten, kinda shitty implemenation but works for now
            i = random.randrange(99999999999)
            
            #AWS response code 
            #opens captured photo and saves image data as response content 
            with open('test.jpg', 'rb') as image_data:
                response_content = image_data.read()
            
            #rekognition detect faces takes response content data and sees if theres a face or not, client and script will crash if there is no faces detected
            rekognition_response = rekognition.detect_faces(Image={'Bytes':response_content}, Attributes=['ALL'])
            
        
            #match responses checks amazon collection and compares it to captured face photo which is your response content var 
            match_response = rekognition.search_faces_by_image(CollectionId=collectionId, Image={'Bytes': response_content}, MaxFaces=1, FaceMatchThreshold=85)
            image = Image.open('test.jpg')
            image_width, image_height = image.size

           #simple for loop to create a cropped photo of bounding box, this is going to be the png uploaded to the s3 bucket
            for item in rekognition_response.get('FaceDetails'):
                bounding_box = item['BoundingBox']
                width = image_width * bounding_box['Width']
                height = image_height * bounding_box['Height']
                left = image_width * bounding_box['Left']
                top = image_height * bounding_box['Top']

                left = int(left)
                top = int(top)
                width = int(width) + left
                height = int(height) + top

                box = (left, top, width, height)
                box_string = (str(left), str(top), str(width), str(height))
                cropped_image = image.crop(box)
                thumbnail_name = '{}.png'.format(i)
                i += 1
                saved_imgs = cropped_image.save(thumbnail_name, 'PNG')

                face_emotion_confidence = 0
                face_emotion = None
                data_emotion =[]
                emo_score = []
                emo_type = []

                Gender = item.get('Gender')
                print(Gender)
                Beard = item.get('Beard')
                print(Beard)
                Smile = item.get('Smile')
                print(Smile)
                AgeRange = item.get('AgeRange')
                data = item.get('Emotions')
                print(data)
                MouthOpen = item.get('MouthOpen')
                print(MouthOpen)
                glasses = item.get('Eyeglasses')
                print(glasses)


                #printing highest confidence emotion state for demo purposes 
                for emotion in item.get('Emotions'):
                    data_emotion.append(emotion)
                    emo_score.append(emotion.get('Confidence'))
                    emo_type.append(emotion.get('Type'))

                    if emotion.get('Confidence') >= face_emotion_confidence:
                        face_emotion_confidence = emotion['Confidence']
                        face_emotion = emotion.get('Type')
                        #print('user:{} ﻿,match_response['FaceMatches'][0]['Face']['ExternalImageId'])
                


                if match_response['FaceMatches']:
                    print('Hello, user:',match_response['FaceMatches'][0]['Face']['ExternalImageId'])
                    user = match_response['FaceMatches'][0]['Face']['ExternalImageId']
                    print("Our Biometric Media player thinks you are currently feeling" + " " + face_emotion)
                    print('User Similarity:',match_response['FaceMatches'][0]['Similarity'])
                    print('User Confidence:',match_response['FaceMatches'][0]['Face']['Confidence'])
                    print("Here is your emotional data")
                    print("---------------------------")
                    print(tabulate(data_emotion))

                    fieldnames = ['Type', 'Confidence']
                    rows = data_emotion

                    with open('data_emotion.csv', 'w', encoding='UTF8', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(rows)
                    
                    web = pd.read_csv('/home/nano/data_emotion.csv')
                  

                    st.title('Data from CECS 490 Biometric Media Player')
                    st.subheader('Hello User:' + user + ',' + ' ' + 'this is all of your emotional data')
                    st.write(web)
                    playmusic()
                    time.sleep(.01)
                     
                else:
                    print("Our Biometric Media player thinks you are currently feeling" + " " + face_emotion)
                    print("Here is your emotional data")
                    print("---------------------------")
                    print(tabulate(data_emotion))

                    fieldnames = ['Type', 'Confidence']
                    rows = data_emotion

                    with open('data_emotion.csv', 'w', encoding='UTF8', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(rows)
                    
                    web = pd.read_csv('/home/nano/data_emotion.csv')
                  

                    st.title('Data from CECS 490 Biometric Media Player')
                    st.subheader('Hello Current User, this is all of your emotional data')
                    st.write(web)
                    st.write(nofaces)
                    st.write(prompt)
                    
                    nofaces = "No faces matched"
                    prompt = "Would you like to create a new user profile? (y/n)"
                    #user creation, psudeo data base honestly
                    #this is the upload of the user sign up photo thru s3 functions

                    print(nofaces)
                    print(prompt)
                   
                    user_choice = input()
                    if user_choice == 'y':
                        print('please insert username')
                        username = input()
                        folder_name = str(username)
                        filepath = '/home/nano/' + str(thumbnail_name)
                        dest_file_name = str(thumbnail_name)
                        all_objects = s3.list_objects(Bucket = bucket_name)
                        doseUserExist = folder_exists(bucket_name, folder_name)
                        
                        #checks if user name is already in our s3 bucket 
                        if doseUserExist:
                            print("This username has been taken please pick a different username")
                            print("Please restart the client and pick a new user name")
                            #add in a recursive function in future to prompt user to pick a new user name
                        else:
                            #uploads bounded box crop pic to aws s3 bucket
                            s3.put_object(Bucket=bucket_name, Key=(folder_name+'/'))
                            s3.upload_file(filepath,bucket_name, '%s/%s' % (folder_name,dest_file_name))
                            #create new user folder for music upload
                            #will have to write something to clone the tree structure of the init music folder
                            parent_dir = "/home/nano"
                            src = "'home/nano/temp"
                            directory = folder_name
                            path = os.path.join(parent_dir, directory)
                            os.chdir(parent_dir)
                            os.mkdir(path)
                            os.remove(filepath)

                            bucket = bucket_name
                            all_objects = s3.list_objects(Bucket =bucket )
                            list_response=rekognition.list_collections(MaxResults=2)

                            if collectionId in list_response['CollectionIds']:
                                rekognition.delete_collection(CollectionId=collectionId)

                            #create a new collection 
                            rekognition.create_collection(CollectionId=collectionId)

                            #add all images in current bucket to the collections
                            #use folder names as the labels
                            for content in all_objects['Contents']:
                                collection_name,collection_image =content['Key'].split('/')
                                if collection_image:
                                    label = collection_name
                                    print('indexing: ',label)
                                    image = content['Key']    
                                    index_response=rekognition.index_faces(CollectionId=collectionId,
                                                                    Image={'S3Object':{'Bucket':bucket,'Name':image}},
                                                                    ExternalImageId=label,
                                                                    MaxFaces=1,
                                                                    QualityFilter="AUTO",
                                                                    DetectionAttributes=['ALL'])
                                    print('FaceId: ',index_response['FaceRecords'][0]['Face']['FaceId'])
#no user mode, plays music locally 
                    elif user_choice == 'n':
                        playmusic()
                        
                    else:
                        print('Please pick either y/n')
                        return
            #results windows for simplepygui
        
        
            #window.close()
        elif event == 'Spotify':
            cv2.imwrite('/home/nano/test.jpg',test)
            #rahdom indexing so photos dont get overwritten, kinda shitty implemenation but works for now
            i = random.randrange(99999999999)
            
            #AWS response code 
            #opens captured photo and saves image data as response content 
            with open('test.jpg', 'rb') as image_data:
                response_content = image_data.read()
            
            #rekognition detect faces takes response content data and sees if theres a face or not, client and script will crash if there is no faces detected
            rekognition_response = rekognition.detect_faces(Image={'Bytes':response_content}, Attributes=['ALL'])
            #match responses checks amazon collection and compares it to captured face photo which is your response content var 
            match_response = rekognition.search_faces_by_image(CollectionId=collectionId, Image={'Bytes': response_content}, MaxFaces=1, FaceMatchThreshold=85)
            image = Image.open('test.jpg')
            image_width, image_height = image.size

           #simple for loop to create a cropped photo of bounding box, this is going to be the png uploaded to the s3 bucket
            for item in rekognition_response.get('FaceDetails'):
                bounding_box = item['BoundingBox']
                width = image_width * bounding_box['Width']
                height = image_height * bounding_box['Height']
                left = image_width * bounding_box['Left']
                top = image_height * bounding_box['Top']

                left = int(left)
                top = int(top)
                width = int(width) + left
                height = int(height) + top

                box = (left, top, width, height)
                box_string = (str(left), str(top), str(width), str(height))
                cropped_image = image.crop(box)
                thumbnail_name = '{}.png'.format(i)
                i += 1
                saved_imgs = cropped_image.save(thumbnail_name, 'PNG')

                face_emotion_confidence = 0
                face_emotion = None
                data_emotion =[]
                emo_score = []
                emo_type = []
                #printing highest confidence emotion state for demo purposes 
                for emotion in item.get('Emotions'):
                    data_emotion.append(emotion)
                    emo_score.append(emotion.get('Confidence'))
                    emo_type.append(emotion.get('Type'))

                    if emotion.get('Confidence') >= face_emotion_confidence:
                        face_emotion_confidence = emotion['Confidence']
                        face_emotion = emotion.get('Type')
                        #print('user:{} your current emotion is {}'.format(match_response['FaceMatches'][0]['Face']['ExternalImageId'], face_emotion))
                        print(face_emotion)
                        
                emotion = str(face_emotion)
                target_emotion = selector.get(emotion)
                a = str(data_emotion)
                play_desc = ("Description for Demo 3: Playlist Generation: Your playlist is mapped to these emotions! {}".format(a))
                #2 lines below work with tail append
                query = f'{endpoint_url}limit={target_emotion["limit"]}&market={target_emotion["market"]}&seed_genres={target_emotion["seed_genres"]}'
                query += f'&{target_emotion["query_tail"]}'

                response = requests.get(query, headers={"Content-Type": "application/json","Authorization": "{}".format(spotify_token)})
                json_response = response.json()
                #print(json_response)  # uncomment to print first line of complete payload
                print("Our Biometric Media player thinks you are currently feeling" + " " + face_emotion)
                print("Here is your emotional data")
                print("---------------------------")
                print(tabulate(data_emotion))

                fieldnames = ['Type', 'Confidence']
                rows = data_emotion

                with open('data_emotion.csv', 'w', encoding='UTF8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
                    
                web = pd.read_csv('/home/nano/data_emotion.csv')
                  

                st.title('Data from CECS 490 Biometric Media Player')

                if match_response['FaceMatches']:
                    user = match_response['FaceMatches'][0]['Face']['ExternalImageId']
                    st.subheader('Hello User:' + user + ',' + ' ' + 'this is all of your emotional data')
                else:
                     st.subheader('Hello Current User, this is all of your emotional data')
                st.write(web)

                for i in json_response['tracks']:
                    uris_repo.append(i['uri'])
                    print(f"\"{i['name']}\" by {i['artists'][0]['name']}")
                    print(i['uri'])
                 #RUN Insert Playlist
                try:
                    insert_playlist(user_profile, spotify_token, uris_repo, play_desc)
                except requests.exceptions.RequestException as e:
                    print(e)

               
main()