#!/usr/bin/env python
# coding: utf-8

# In[1]:


'''
# pyaudio download
# on Linux
sudo apt install python3-pyaudio
# on MacOS
brew install portaudio
pip install pyaudio
# on Windows
python -m pip install pyaudio

# whisper download
pip install git+https://github.com/openai/whisper.git 
# on Ubuntu or Debian
sudo apt update && sudo apt install ffmpeg
# on Arch Linux
sudo pacman -S ffmpeg
# on MacOS using Homebrew (https://brew.sh/)
brew install ffmpeg
# on Windows using Chocolatey (https://chocolatey.org/)
choco install ffmpeg
# on Windows using Scoop (https://scoop.sh/)
scoop install ffmpeg

pip install fuzzywuzzy

pip install word2number
'''

import wave
import sys
import whisper
import pyaudio
from os import path
model = whisper.load_model("base.en")

import csv
import logging
from fuzzywuzzy import fuzz
import numpy as np
from word2number import w2n


# In[33]:


list_words = ["drone", "travel", "move", "fly", "landing", "stop", "up", "upward", "down", "downward", "left", 
              "right", "forward", "backward", "figure", "and"]

def getClosestWord(word, list_word):
    word_answer = list(map(lambda x: fuzz.ratio(word, x), list_word))
    a = np.array(word_answer)
    int_answer = np.where(a <= 60, 0, a)
    if not int_answer.any():
        return ""
    index_max = np.argmax(int_answer)
    return list_word[index_max]

def wordToword(command):
    '''
      Apply the levensthein distance and word replacement for the existing command
    '''
    if command[-1] == ".":
        command = command[0:-1]
    command = command.replace(",","")
    A = command.split(" ")
    string_store = ""
    for element in A:
        try:
            num_val = w2n.word_to_num(element)
            string_store += str(num_val)
            string_store += " "
        except:
            try:
                num_val = float(element)
                string_store += str(num_val)
                string_store += " "
            except:
                string_store += getClosestWord(element, list_words)
                string_store += " "

    for key in dict_words.keys():
        string_store = string_store.replace(key, dict_words[key])
    return string_store

dict_words = {
    "fly" : "move",
    "travel" : "fly",
    "stop" : "landing",
    "north" : "forward",
    "south" : "backward",
    "east" : "right",
    "west" : "left",
    "upward" : "up",
    "downward" : "down"
}

list_words = ["drone", "travel", "move", "fly", "landing", "stop", "up", "upward", "down", "downward", "left", 
              "right", "forward", "backward", "figure", "and"]

dict_direction = {
    "up" : [0,0,1],
    "down" : [0,0,-1],
    "left" : [-1,0,0],
    "right" : [1,0,0],
    "forward" : [0,1,0],
    "backward" : [0,-1,0]
}


''' 
function splitToPhase: change a list of word to a list of phase(list of words) that have word in list_action in the front
  input: 
    list_phase: This is an empty list at first but we will keep list of the phase we want in here.
    rev_list_word: a reverse of the list of words we want to make a phase
    list_action: a list of the action such as "up" "down".
  return:
    list of list of words

function double_reverse: reverse the list and every member of the list
  input: 
    list_of_list: a list of list of words
  return: double reverse version of the input
'''

def splitToPhase(list_phase,rev_list_word,list_action):
    def common_member(a, b):
        a_set = set(a)
        b_set = set(b)
        if len(a_set.intersection(b_set)) > 0:
            return(True)
        return(False) 
      
    if common_member(list_action,rev_list_word):
        for i in range(len(rev_list_word)):
            if rev_list_word[i] in list_action:
                list_phase.append(rev_list_word[:i+1])
                return [rev_list_word[:i+1]] + splitToPhase(list_phase, rev_list_word[i+1:],list_action)
    return []

def double_reverse(list_of_list):
    rev_list = list(map(lambda x: x[::-1], list_of_list))
    return rev_list[::-1]

def command_fly(list_word, list_co):
    distance = 3
    action = list_word[0]
    if action == "landing":
        return list_co + [[0,0,1],[0,0,0]]
    elif action == "reset":
        return list_co + [[0,0,1]]
    direction = dict_direction[action]
    
    for element in list_word:
        try:
            distance = float(element)
        except:  
            pass
    last_element = list_co[-1]
    list_next = list(map(lambda x, y: distance*x + y, direction, last_element))
    # if list_next[2] < 0:
    #   error then landing
    list_co.append(list_next)
    return list_co

def commandTocsv(command):
    list_coordination = [[0,0,0],[0,0,1]] # delete [0,0,1] to start from [0,0,0]
    command = wordToword(command)
    print(command)
    list_word = command.split(" ")
    list_word.reverse()
    list_action = ["landing","reset","up","down","forward","backward","left","right"]
    list_phase = double_reverse(splitToPhase([],list_word,list_action))
    for list_word in list_phase:
        list_coordination = command_fly(list_word, list_coordination)
    with open("output.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(list_coordination)


# In[34]:


CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1 if sys.platform == 'darwin' else 2
RATE = 44100
RECORD_SECONDS = 5

with wave.open('output3.wav', 'wb') as wf:
    p = pyaudio.PyAudio()
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)

    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True)

    print('Recording...')
    for _ in range(0, RATE // CHUNK * RECORD_SECONDS):
        wf.writeframes(stream.read(CHUNK))
    print('Done')

    stream.close()
    p.terminate()
    result = model.transcribe("/Users/noptoemtrisna/CSCI2951K/output3.wav")
text = result["text"]
print(text)
commandTocsv(text)


# In[32]:


commandTocsv(text)


# In[ ]:




