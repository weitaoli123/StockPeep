from django.shortcuts import render,redirect
import pyrebase
import requests
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib as pl
pl.use('Agg')
import numpy as np
import pandas as pd
import pandas_datareader.data as web
import io
import urllib, base64
import math
import os

config = {
    'apiKey': "AIzaSyAbRrY-CfiUI0G5J9bS0ED418dLWFzOGlo",
    'authDomain': "stockpredictor-7f72a.firebaseapp.com",
    'databaseURL': "https://stockpredictor-7f72a.firebaseio.com",
    'projectId': "stockpredictor-7f72a",
    'storageBucket': "stockpredictor-7f72a.appspot.com",
    'messagingSenderId': "776587422039",
    'appId': "1:776587422039:web:85d21c8b1e4666013df612"
  }
  
firebase = pyrebase.initialize_app(config)

auth = firebase.auth()
db = firebase.database()
companies = []
tickerList = []

def signInPage(request):
    return render(request, "signIn.html")

def home(request):
    try:
        uid = auth.current_user['localId']
        uname = db.child("users").child(uid).child("details").child("name").get().val()
    except:
        return redirect("/")

    watchlist = db.child("users").child(uid).child("watchlist").get().val()
    if watchlist != None and len(companies) < 1:
        for i in watchlist:
            temp_dict = {}
            temp_dict['id'] = i
            temp_dict['ticker'] = db.child("users").child(uid).child("watchlist").child(i).child("ticker").get().val()
            temp_dict['name'] = db.child("users").child(uid).child("watchlist").child(i).child("name").get().val()
            retrieve_price(temp_dict)
            companies.append(temp_dict)
            tickerList.append(temp_dict['ticker'])
            updatePredictions()


    data = {
        "e" : uname,
        "companies" : companies,
    }

    return render(request,"home_main.html",data)

#return last Adjusted Closing price
# def get_price(ticker):
#     df = web.DataReader(ticker, 'yahoo', dt.date.today())
#     return df['Adj Close'][0].round(2)

def updatePredictions():
    for company in companies:
        score = 50
        #score from volume
        if company['Volume'] > company['avgVolume20']:
            if company['price'] > company['ma20']:
                score = score + 5 + (((company['price'] - company['ma20'])/company['ma20']) * 100).round(0)
            else:
                score = score - 5 - (((company['ma20'] - company['price'])/company['ma20']) * 100).round(0)
        else: 
            if company['price'] > company['ma20']:
                score = score + 5
            else:
                score = score - 5
        #score from RSI14
        if company['rsi14'] > 70:
            score = score - (company['rsi14'] - 70).round(0)
        if company['rsi14'] < 30:
            score = score + (30 - company['rsi']).round(0)

        #score from MA
        if company['price'] > company['ma100']:
            if company['price'] > company['ma10']:
                score = score + 8
            elif company['price'] > company['ma20']:
                score = score + 3
            else:
                score = score - 5
        elif company['price'] < company['ma100']:
            if company['price'] < company['ma10']:
                score = score - 8
            elif company['price'] < company['ma20']:
                score = score - 3
            else:
                score = score + 5
        
        if company['ma10'] > company['ma100']:
            score = score + 7
        elif company['ma20'] > company['ma100']:
            score = score + 4

        #score from high and low
        if company['price'] < company['Low']*1.05:
            score = score - 5
        if company['price'] > company['High']*1.05:
            score = score + 5

        company['score'] = int(score)



def retrieve_price(temp_dict):
    if((dt.datetime.now().hour) < 13):
        end = dt.date.today() - dt.timedelta(days = 1)
    else:
        end = dt.date.today()
    start = end - dt.timedelta(days = 215)      
    df = web.DataReader(temp_dict['ticker'], 'yahoo', start, end)
    temp_dict['High'] = df['High'].max().round(2)
    temp_dict['Low'] = df['Low'].min().round(2)
    # df['200ma'] = df['Adj Close'].rolling(window=200).mean().round(2)
    df['ma100'] = df['Adj Close'].rolling(window=100).mean().round(2)
    df.dropna(subset=['ma100'], inplace = True)
    df['ma20'] = df['Adj Close'].rolling(window=20).mean().round(2)
    df['ma10'] = df['Adj Close'].rolling(window=10).mean().round(2)
    # temp_dict['200ma'] = df['200ma'].tail(1).round(2)[0]
    temp_dict['ma100'] = df['ma100'].tail(1).round(2)[0]
    temp_dict['rsi14'] = get_rsi(df)
    temp_dict['price'] = df['Adj Close'].tail(1).round(2)[0]
    temp_dict['ma20'] = df['ma20'].tail(1).round(2)[0]
    temp_dict['ma10'] = df['ma10'].tail(1).round(2)[0]
    temp_dict['avgVolume20'] = df['Volume'].tail(20).mean().round(0)
    temp_dict['Volume'] = df['Volume'].tail(1).round(0)[0]
    x = df.index
    y = df['Adj Close']
    plt.plot(x,y)
    plt.xlabel('Date')
    plt.ylabel('Price (US Dollars)')
    # save the figure
    path = './static/media/' + temp_dict['ticker'] + '.png'
    plt.savefig(path, dpi=100, bbox_inches='tight')
    plt.clf()

def get_rsi(df):
    rsi = pd.DataFrame()
    rsi['up'] = df['Close'].diff().apply(lambda x: x if x > 0 else 0)
    rsi['down'] = df['Close'].diff().apply(lambda x: x if x < 0 else 0).abs()
    avgU = rsi['up'].tail(14).mean()
    avgD = rsi['down'].tail(14).mean()
    RSI14 = (100 - 100 / (1 + avgU/avgD)).round(2)

    return RSI14

#sign user in using given info from form
def signIn(request):
    email = request.POST.get('email')
    pw = request.POST.get('password')
    try:
        auth.sign_in_with_email_and_password(email,pw)
        # uid = user['localId']
        # uname = db.child("users").child(uid).child("details").child("name").get().val()
        return home(request)
        
    except:
        auth.current_user = None
        global companies
        global tickerList
        companies = []
        tickerList = []
        return render(request,"signIn.html", {"msg":"Invalid credentials."})

#load watchlist
def watchlist(request, *args, **kwargs):
    try:
        uid = auth.current_user['localId']
        uname = db.child("users").child(uid).child("details").child("name").get().val()
    except:
        return redirect("/")  
  
    global companies
    global tickerList
    data = {
        "e":uname,
        "company_list":companies,
        "tickerList": tickerList,
    }
    if len(args) == 1:
        data['result_list'] = args[0]

    return render(request,"watchlist.html",data)

#redirect back to sign in page
def logout(request):
    auth.current_user = None
    global companies
    global tickerList
    companies = []
    tickerList = []
    return redirect("/")

def registerPage(request):
    return render(request,"register.html")

#registers account using given info from the form
def register(request):
    name = request.POST.get('name')
    email = request.POST.get('email')
    pw = request.POST.get('password')

    try:
        user = auth.create_user_with_email_and_password(email,pw)
        uid = user['localId']
        data = {
            "name" : name,
            "email" : email,
        }
        db.child("users").child(uid).child("details").set(data)
        return render(request,"signIn.html",{"msg":"Account created successfully!"})
    except:
        return render(request,"register.html",{"msg":"Account is already registered with provided email."})

#returns company name of ticker entered
def get_company_name(request):
    symbol = request.POST.get('ticker')
    url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en".format(symbol)
    result = requests.get(url).json()
    return watchlist(request,result['ResultSet']['Result'])

#add to watchlist
def addWatchlist(request,ticker,name):
    uid = auth.current_user['localId']
    
    data = {
        "ticker" : ticker,
        "name" : name,
    }
    global companies
    global tickerList
    exist = False
    for ticker in tickerList: 
        if ticker == data['ticker']: 
            exist = True
            break
    
    if exist == False:
        new_id = db.child("users").child(uid).child("watchlist").push(data)
        temp_dict = {}
        temp_dict['id'] = new_id['name']
        temp_dict['ticker'] = data['ticker']
        temp_dict['name'] = data['name']
        retrieve_price(temp_dict)
        # temp_dict['price'] = df['Adj Close'].tail(1).round(2)[0]
        # temp_dict['rsi14'] = get_rsi(df)
        companies.append(temp_dict)
        tickerList.append(temp_dict['ticker'])
        updatePredictions()


    return watchlist(request)

#remove from watchlist
def removeWatchlist(request,id):
    uid = auth.current_user['localId']
    t = db.child("users").child(uid).child("watchlist").child(id).child("ticker").get().val()
    db.child("users").child(uid).child("watchlist").child(id).remove()
    global companies
    global tickerList
    for i in range(len(tickerList)): 
        if tickerList[i] == t: 
            del companies[i] 
            del tickerList[i]
            break
    return watchlist(request)

