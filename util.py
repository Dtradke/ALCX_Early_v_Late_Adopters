import numpy as np
import urllib.request as rq
import json
from collections import Counter as c
import time
import matplotlib.pyplot as plt
import os
import pandas as pd
import operator
import datetime


print("Backend Loaded")


def loadData(url):
    try:
        dataset = rq.urlopen(url)
        dataset = dataset.read()
        dataset = json.loads(dataset)
    except Exception as e:
        print('Unable to get data from flipsidecrypto API. Check the URL below: \n{}'.format(url))
    return dataset


def collectData(dataset):
    addresses = {}
    for i, val in enumerate(dataset):
        is_target_in_holder_list = val['USER_ADDRESS'].lower() in (string.lower() for string in list(addresses.keys()))
        # if val['USER_ADDRESS'] not in list(addresses.keys()):
        if not is_target_in_holder_list:
            addresses[val['USER_ADDRESS']] = {'ALCX': 0, 'OTHER': 0, 'PERC': 0}

        # try:
        if val['AMOUNT_USD'] is not None and val['SYMBOL'] is not None:
            # print(val)
            if val['SYMBOL'].lower() == 'alcx':
                addresses[val['USER_ADDRESS'].lower()]['ALCX'] += float(val['AMOUNT_USD'])

            else:
                addresses[val['USER_ADDRESS'].lower()]['OTHER'] += float(val['AMOUNT_USD'])


    return addresses


def topAmtBalanceBar(add_dict, pop_mean, time_name="First"):
    percs = np.flip(np.array(list(add_dict.values())))
    x_vals = np.linspace(0, percs.size, 10)
    x_val_str = []
    for i in range(0,x_vals.size):
        x_val_str.append(str(int(i*10)))

    fig = plt.figure(figsize=(12, 6))
    plt.bar(np.arange(percs.size),percs)
    plt.ylabel("% Portfolio", fontsize=18)
    plt.xlabel("% of "+time_name+" 3 Week Users", fontsize=18)
    plt.xticks(x_vals, x_val_str, fontsize=18)
    plt.yticks(fontsize=15)
    plt.title("Percent of Portfolio as ALCX for "+time_name+" 3 Week Users; Mean: "+str(round(100*pop_mean,1)), fontsize=18)
    plt.show()



def sortDict(input_dict):
    return {k: v for k, v in sorted(input_dict.items(), key=lambda item: item[1])}

def topAmtStakedBar(add_dict, time_name="First"):
    staked = np.flip(np.array(list(add_dict.values())))

    # if time_name == 'Last':
    #     staked = staked[3:]

    print("Mean amount of staked value: ", np.mean(staked))

    x_vals = np.linspace(0, staked.size, 10)
    x_val_str = []
    for i in range(0,x_vals.size):
        x_val_str.append(str(int(i*10)))

    fig = plt.figure(figsize=(12, 6))

    plt.bar(np.arange(staked.size),staked)
    plt.ylabel("Value (USD)", fontsize=18)
    plt.xlabel("% of "+time_name+" 3 Week Users", fontsize=18)
    plt.xticks(x_vals, x_val_str, fontsize=18)
    # plt.xticks(rotation=90)
    plt.yticks(fontsize=15)
    plt.title("Value Staked from "+time_name+" 3 Week Adopters; Mean: $"+str(round(np.mean(staked),1))+" USD", fontsize=18)
    plt.show()

def topPERCStakedBar(top_amt, add_dict, pop_mean, time_name="First"):
    adds = reverse_lst(list(add_dict.keys()))[:25]
    staked = reverse_lst(list(add_dict.values()))[:25]

    fig = plt.figure(figsize=(10, 6))
    user_ids = []
    for i, val in enumerate(adds):
        user_ids.append("..."+val[-4:])

    top_staked = np.array(staked)
    plt.bar(user_ids,top_staked)
    plt.ylabel("Value (USD)", fontsize=18)
    plt.xticks(rotation=90)
    plt.yticks(fontsize=15)
    plt.title("Value Staked from "+time_name+" 3 Week Adopters; Mean: "+str(round(pop_mean,1))+" USD", fontsize=18)
    plt.show()

def getPercALCX(holders, mode='First'):
    perc = []
    add_perc = {}
    count = 0
    for add in list(holders.keys()):
        add_perc[add] = holders[add]['PERC']
        perc.append(holders[add]['PERC'])

    mean_perc = np.mean(np.array(perc))
    print("Mean percent of portfolio in ALCX: ", mean_perc)
    sorted_dict = sortDict(add_perc)
    topAmtBalanceBar(sorted_dict, mean_perc, time_name=mode)

    # tops = getTops(25, add_perc, mean_perc, time_mode=mode, analysis_mode='bal')


def getAvgStaked(holders, mode='First'):
    staked = []
    add_staked = {}
    for add in list(holders.keys()):
        if holders[add]['total_staked'] > 0:
            # print(holders[add]['total_staked'])
            staked.append(holders[add]['total_staked'])
            add_staked[add] = holders[add]['total_staked']

    sorted_dict = sortDict(add_staked)
    topAmtStakedBar(sorted_dict, time_name=mode)

    # tops = getTops(25, add_staked, mean_staked, time_mode=mode, analysis_mode='staked')


def assignValue(holders):
    url = 'https://api.flipsidecrypto.com/api/v2/queries/76c022d1-721d-4511-8619-dfec2cc8edee/data/latest'
    dataset = rq.urlopen(url)
    dataset = dataset.read()
    prices = json.loads(dataset)
    price_dict = {}
    for p in prices:
        price_dict[p['SYMBOL']] = p['PRICE']


    for i, val in enumerate(list(holders.keys())):
        holders[val]['STAKED_ALCX'] = holders[val]['STAKED_ALCX'] * price_dict['ALCX']
        holders[val]['STAKED_slp'] = holders[val]['STAKED_slp'] * np.sum(np.array(list(price_dict.values())))
        holders[val]['total_staked'] = holders[val]['STAKED_ALCX'] + holders[val]['STAKED_alUSD'] + holders[val]['STAKED_slp'] + holders[val]['STAKED_crv']
    return holders

def getStakedAmt(staked, holders):

    for i, val in enumerate(staked):
        is_target_in_holder_list = val['LOWER(ORIGIN_ADDRESS)'].lower() in (string.lower() for string in list(holders.keys()))

        if is_target_in_holder_list and val['SYMBOL'].lower() == 'alcx':
            holders[val['LOWER(ORIGIN_ADDRESS)']]['STAKED_ALCX'] += val['AMOUNT']
        elif is_target_in_holder_list and val['SYMBOL'].lower() == 'alusd':
            holders[val['LOWER(ORIGIN_ADDRESS)']]['STAKED_alUSD'] += val['AMOUNT']
        elif is_target_in_holder_list and val['SYMBOL'].lower() == 'slp':
            holders[val['LOWER(ORIGIN_ADDRESS)']]['STAKED_slp'] += val['AMOUNT']
        elif is_target_in_holder_list and (val['SYMBOL'].lower() == 'alusd3crv' or val['SYMBOL'].lower()[:3] == 'cur'):
            holders[val['LOWER(ORIGIN_ADDRESS)']]['STAKED_crv'] += val['AMOUNT']

    return assignValue(holders)

def formatHolders(holder_arr, holder_data=None): # LOWER(ORIGIN_ADDRESS)
    holders = {}
    for i, val in enumerate(holder_arr):
        is_target_in_holder_list = val['USER_ADDRESS'].lower() in (string.lower() for string in list(holders.keys()))
        # if val['TO_ADDRESS'] not in list(holders.keys()):
        if not is_target_in_holder_list:
            if holder_data is not None:
                holders[val['USER_ADDRESS']] = holder_data[val['USER_ADDRESS']]
            else:
                holders[val['USER_ADDRESS']] = {'ALCX': 0, 'OTHER': 0, 'PERC': 0, 'STAKED_ALCX': 0, 'STAKED_alUSD': 0, 'STAKED_slp': 0, 'STAKED_crv': 0}
    return holders

def formatHoldersWData(holder_arr, holder_data): # LOWER(ORIGIN_ADDRESS)
    holders = {}
    for i, val in enumerate(holder_arr):
        is_target_in_holder_list = val['FROM_ADDRESS'].lower() in (string.lower() for string in list(holder_data.keys()))
        # if val['TO_ADDRESS'] not in list(holders.keys()):
        if is_target_in_holder_list:
            holders[val['FROM_ADDRESS']] = holder_data[val['FROM_ADDRESS']]
    return holders

def addALCXData(alcx_holders, alcx_holder_data):
    holders = {}
    for i, val in enumerate(alcx_holder_data):
        is_target_in_holder_list = val['USER_ADDRESS'].lower() in (string.lower() for string in list(alcx_holders.keys()))
        # if val['TO_ADDRESS'] not in list(holders.keys()):
        if is_target_in_holder_list:
            alcx_holders[val['USER_ADDRESS']]['ALCX'] = val['ALCX_USD']
    return alcx_holders

def addOtherData(alcx_holders, portfolios):
    holders = {}
    for i, val in enumerate(portfolios):
        is_target_in_holder_list = val['USER_ADDRESS'].lower() in (string.lower() for string in list(alcx_holders.keys()))

        if is_target_in_holder_list:
            alcx_holders[val['USER_ADDRESS']]['OTHER'] = val['PORTFOLIO']
            alcx_holders[val['USER_ADDRESS']]['PERC'] = alcx_holders[val['USER_ADDRESS']]['ALCX'] / alcx_holders[val['USER_ADDRESS']]['OTHER']

    return alcx_holders

def filterAdds(og_holders, new_holders):
    new_holder_keys = list(new_holders.keys())
    for i, val in enumerate(new_holder_keys):
        is_target_in_holder_list = val.lower() in (string.lower() for string in list(og_holders.keys()))
        if is_target_in_holder_list:
            del new_holders[val]
    return new_holders


#
# ''' og holders '''
# url = 'https://api.flipsidecrypto.com/api/v2/queries/89eb6960-72db-499a-97cd-318098955410/data/latest' # OG HOLDERS
# og_holders = loadData(url)
# og_holders = formatHolders(og_holders)
#
# # ''' load transaction stuff '''
# url = 'https://api.flipsidecrypto.com/api/v2/queries/ddf70c0d-d6e2-41a1-a014-6f33e84fab72/data/latest' # current balances
# balances = loadData(url)
# addresses = collectData(balances)
# getPercALCX(addresses, og_holders, mode='First')              # calculates the percent of portfolios that are ALCX
# exit()
# print(balances[0])
# exit()

# url = 'https://api.flipsidecrypto.com/api/v2/queries/c44f9d8a-6a8c-4a6d-97f4-2f3a9cab6e54/data/latest' # transactions to staking pools
# staked = loadData(url)
# # getStakedAmt(staked, og_holders)
# og_holders_w_stake = getStakedAmt(staked, og_holders)
# getAvgStaked(og_holders_w_stake, mode='First')





#
#
#
# url = 'https://api.flipsidecrypto.com/api/v2/queries/ddf70c0d-d6e2-41a1-a014-6f33e84fab72/data/latest' # people with ALCX and amount of ALCX IN UDS
# alcx_holder_data = loadData(url)
# alcx_holders = formatHolders(alcx_holder_data)
# alcx_holders = addALCXData(alcx_holders, alcx_holder_data)
#
# url = 'https://api.flipsidecrypto.com/api/v2/queries/666e59c4-0759-41a6-8fe5-21305ba4ba50/data/latest' # whole profile including ALCX
# portfolios = loadData(url)
# alcx_holders = addOtherData(alcx_holders, portfolios)
#
# # ''' og holders '''
# # url = 'https://api.flipsidecrypto.com/api/v2/queries/89eb6960-72db-499a-97cd-318098955410/data/latest' # OG HOLDERS
# # og_holders = loadData(url)
# # og_holders = formatHoldersWData(og_holders, alcx_holders)
# # getPercALCX(og_holders, mode='First')
#
#
# # ''' new holders '''
# url = 'https://api.flipsidecrypto.com/api/v2/queries/b662564a-f43a-4a78-b6c5-3ebeaeb14c51/data/latest' # end of march to present
# new_holders = loadData(url)
# new_holders = formatHoldersWData(new_holders, alcx_holders)
# # getPercALCX(new_holders, mode='Last')
#
#
#
# url = 'https://api.flipsidecrypto.com/api/v2/queries/c44f9d8a-6a8c-4a6d-97f4-2f3a9cab6e54/data/latest' # transactions to staking pools
# staked = loadData(url)
# new_holders_w_stake = getStakedAmt(staked, new_holders)
# getAvgStaked(new_holders_w_stake, mode='Last')
