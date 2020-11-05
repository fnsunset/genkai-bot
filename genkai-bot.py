# coding: utf-8
import discord
import asyncio
import numpy as np
import os
import csv

client = discord.Client()  
global chList
global a

ENV_TOKEN = os.environ["ENV_TOKEN"] #環境変数 ENV_TOKEN に Discordのトークンを指定してください

dtype = [("voiceCh", 'uint64'), ("txtCh", 'uint64'), ("notifyCh", 'uint64'), ("cur_member",int), ("member",int), ("notifyFlg",bool)]
chList = np.empty(0,dtype=dtype)
chLog = 0
if(os.path.exists('chlist.txt')):
    with open('chlist.txt') as f:
        reader = csv.reader(f)
        print('[log] chlist.txt の読み込みに成功しました')
        for row in reader:
            #chlist.txt には、対象ボイスチャンネルID、ON/OFFをするテキストチャンネルID、通知を出すチャンネルID（無ければ0）を1行ずつ記載
            chList = np.append(chList,np.array([(row[0],row[1],row[2],0,0,False)],dtype=dtype), axis=0)

if(os.path.exists('chlog.txt')):
    with open('chlog.txt') as f:
        #chlog.txt には、ログを出力するチャンネルIDを1行ずつ記載
        reader = f.read()
        print('[log] chlog.txt の読み込みに成功しました')
        chLog = int(reader)

@client.event
async def on_ready():
    print('login discord...')
    asyncio.ensure_future(greeting_gm())

@client.event
#特定の発言がされたとき
async def on_message(message):
    if message.author.bot:
        return
    if message.content == '!通知'or message.content == '!notify':
        set_notify_flg(get_union_voice_channel(message.channel), True)
        await message.channel.send('📹Webカメラ通知がONになりました')
        await message.delete()
    if message.content == '!非通知':
        set_notify_flg(get_union_voice_channel(message.channel), False)
        await message.channel.send('📹Webカメラ通知がOFFになりました')
        await message.delete()

@client.event
# ボイチャのステータスが変わったとき
async def on_voice_state_update(member, before, after):
    # パターン1 音声チャンネルを渡り歩いている場合
    if before.channel and after.channel:
        if before.channel.id != after.channel.id:
            # ボイスチャンネル参加検知
            await entry_detection(after.channel, member)
            # ボイスチャンネル離脱検知
            await exit_detection(before.channel, member)
    
    # パターン2 音声チャンネルに初めて加入
    if not before.channel and after.channel:
        # ボイスチャンネル参加検知
        await entry_detection(after.channel, member)
    
    # パターン3 音声チャンネルから離脱
    if before.channel and not after.channel:
        # ボイスチャンネル離脱検知
        await exit_detection(before.channel, member)
    
    # WebカメラをONにした場合
    if not before.self_video and after.self_video and after.channel:
        mic = ''
        if after.self_mute:
            mic = '🔇'
        if chLog != 0:
            await get_Log_Channel().send('[log] ' + mic + member.display_name + '('+ member.name + ')が'+after.channel.name+'でWebカメラをONにしました')
        notifyChannel = get_union_notify_channel(after.channel)
        if notifyChannel != None:
            print('[log] '+ after.channel.name + 'の通知Channelが有効です 通知先: '+ notifyChannel.name )
            if get_notify_flg(after.channel):
                await notifyChannel.send('[Bot通知] 誰かが'+ after.channel.name +'でカメラをつけたようです')
                set_notify_flg(after.channel, False)

    # GoliveをONにした場合
    if not before.self_stream and after.self_stream and after.channel:
        mic = ''
        if after.self_mute:
            mic = '🔇'
        if chLog != 0:
            await get_Log_Channel().send('[log] ' + mic + member.display_name + '('+ member.name + ')が'+after.channel.name+'でGoLiveを開始しました')

# ボイスチャンネル参加検知
@client.event
async def entry_detection(channel, member):
    client.fetch_offline_members = True
    txtChannel = get_union_text_channel(channel)
    if txtChannel != None:
        # 対象ボイチャがあればテキストチャンネルの権限を付与する
        print('[log] '+ channel.name + 'に'+ member.name +'が参加')
        await txtChannel.set_permissions(member, read_messages=True)
        # 初めてのお客さんなら通知を投げる
        if len(channel.members) == 1:
            set_notify_flg(channel, False)
            await clear(txtChannel)
            notifyChannel = get_union_notify_channel(channel)
            if notifyChannel == None:
                await txtChannel.send('[log] 専用テキストチャンネルが有効になりました。\nボイスチャットに参加しているメンバーのみが閲覧可能で、誰もいなくなるとここの内容は消去されます。')
            else:
                await txtChannel.send('[log] 専用テキストチャンネルが有効になりました。\nボイスチャットに参加しているメンバーのみが閲覧可能で、誰もいなくなるとここの内容は消去されます。\nまた、「**!通知**」or「**!notify**」と発言することで📹WebCamを付けた際にサーバ参加者に通知を飛ばすことができます。')
            return

@client.event
async def exit_detection(channel, member):
    client.fetch_offline_members = True
    txtChannel = get_union_text_channel(channel)
    if txtChannel != None:
        # 対象ボイチャであればテキストチャンネルの権限をはく奪する
        print('[log] '+ channel.name + 'から'+ member.name +'が離脱')
        await txtChannel.set_permissions(member, read_messages=False)
        # 誰も居なくなったらチャットの中身を消去する
        if len(channel.members) == 0:
            print('[log] '+ channel.name +'の無人化を検知したためメッセージを削除します')
            await clear(txtChannel)
            set_notify_flg(channel, False)

# 通話Chに紐づいたテキストChを返す
def get_union_text_channel(channel):
    result = None
    for cnt in range(chList.shape[0]):
        if channel.id == chList[cnt]['voiceCh']:
            result = client.get_channel(chList[cnt]['txtCh'])
            break
    return result

# 通話Chに紐づいた通知Chを返す
def get_union_notify_channel(channel):
    result = None
    for cnt in range(chList.shape[0]):
        if channel.id == chList[cnt]['voiceCh']:
            result =  client.get_channel(chList[cnt]['notifyCh'])
            break
    return result

# テキストChに紐づいた通話Chを返す
def get_union_voice_channel(channel):
    result = None
    for cnt in range(chList.shape[0]):
        if channel.id == chList[cnt]['txtCh']:
            result = client.get_channel(chList[cnt]['voiceCh'])
            break
    return result

def get_notify_flg(channel):
    result = False
    for cnt in range(chList.shape[0]):
        if channel.id == chList[cnt]['voiceCh']:
            result = chList[cnt]['notifyFlg']
            break
    return result

def set_notify_flg(channel, flg):
    for cnt in range(chList.shape[0]):
        if channel.id == chList[cnt]['voiceCh']:
            chList[cnt]['notifyFlg'] = flg
            print('[log] notifyFlgが' + channel.name + 'で設定されました。 設定値:' + str(chList[cnt]['notifyFlg']))
            break
    return

def get_Log_Channel():
    channel = client.get_channel(chLog)
    return channel

# 通話Ch一覧を取得する
def get_voice_channel_list():
    return

# 特定のチャンネルの発言を全削除
async def clear(ctx):
    print('[log] '+ ctx.name + 'のログを削除します...')
    await ctx.purge()

# 特定のチャンネルの閲覧権限を全削除
async def permissions_clear(channel):
    client.fetch_offline_members = True
    memberlist = channel.members
    for member in memberlist:
        await channel.set_permissions(member, read_messages=False)

# 特定のチャンネルの閲覧権限を付与
async def permissions_set(vchannel):
    client.fetch_offline_members = True
    tchannel = get_union_text_channel(vchannel)
    memberlist = vchannel.members
    for member in memberlist:
        await tchannel.set_permissions(member, read_messages=True)

# 定期的に監視する
async def greeting_gm():
    print('[log] 定期監視機能が有効になりました…')
    while True:
        client.fetch_offline_members = True
        for cnt in range(chList.shape[0]):
            channel = client.get_channel(chList[cnt]['voiceCh'])
            chList[cnt]['cur_member'] = len(channel.members)
            if chList[cnt]['cur_member'] == 0 and chList[cnt]['cur_member'] != chList[cnt]['member']:
                print('[log] '+ channel.name+'から参加者が居なくなったため、閲覧権限をクリアします')
                await clear(get_union_text_channel(channel))
                await permissions_clear(get_union_text_channel(channel))
                chList[cnt]['notifyFlg'] = False
            if chList[cnt]['cur_member'] != 0 and chList[cnt]['cur_member'] != chList[cnt]['member']:
                print('[log] '+ channel.name+'に参加者が居るため、閲覧権限を与えます')
                await permissions_set(channel)
            chList[cnt]['member'] = chList[cnt]['cur_member']
        await asyncio.sleep(600)


client.run(ENV_TOKEN)