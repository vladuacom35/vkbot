import vkapi
import time
import log

class vk_bot:

    delay_on_reply = 1

    def __init__(self, username, password, captcha_handler=None):
        self.api = vkapi.vk_api(username, password, 4)
        self.api.captcha_handler = captcha_handler
        self.api.getToken()
        self.banned_messages = set()
        self.guid = int(time.time() * 5)
        self.ensureLoggedIn()
        self.self_id = str(self.api.users.get()[0]['id'])
        self.last_viewed_comment = 0
        self.name_cache = {}

    def replyAll(self, gen_reply, include_read=0):
        try:
            messages = self.api.messages.getDialogs(unread=1-include_read)['items'][::-1]
        except KeyError:
            # may sometimes happen because of friendship requests
            return
        if include_read:
            print('Include read')
        t = 0
        for i in messages:
            cur = i['message']
            if cur['id'] in self.banned_messages:
                continue
            if cur['out']:
                continue
            try:
                ans = gen_reply(cur)
            except Exception as e:
                ans = None
                print('[ERROR] %s: %s' % (e.__class__.__name__, str(e)))
                time.sleep(1)
            if not ans:
                continue
            t = 1
            self.replyMessage(cur, ans[0], ans[1])
        if not t:
            print('Doing nothing...')

    def getSender(self, message):
        if 'chat_id' in message:
            return 2000000000 + int(message['chat_id'])
        return message['user_id']

    def sendMessage(self, to, msg):
        self.guid += 1
        to = int(to)
        if to > 2000000000:
            return self.api.messages.send(chat_id=to-2000000000, message=msg, guid=self.guid)
        else:
            return self.api.messages.send(user_id=to, message=msg, guid=self.guid)

    # message==None: special conf messages, don't need to reply
    # fast==1: no delay
    #       2: no markAsRead
    def replyMessage(self, message, answer, fast=0):
        if fast == 0:
            self.api.messages.markAsRead.delayed(message_ids=message['id'])
        if not answer:
            self.banned_messages.add(message['id'])
            self.api.sync()
            return
        if fast == 0 or fast == 2:
            self.api.messages.setActivity.delayed(type='typing', user_id=self.getSender(message))
            self.api.sync()
            time.sleep(self.delay_on_reply)
        if self.sendMessage(self.getSender(message), answer) is None:
            self.banned_messages.add(message['id'])
            log.write('bannedmsg', str(message['id']))


    def addFriends(self, gen_reply, is_good):
        data = self.api.friends.getRequests(extended=1)
        self.api.delayedReset()
        to_rep = []
        for i in data['items']:
            if is_good(i['user_id']):
                self.api.friends.add.delayed(user_id=i['user_id'])
                if 'message' in i:
                    ans = gen_reply(i)
                    to_rep.append((i, ans))
            else:
                self.api.friends.delete.delayed(user_id=i['user_id'])
        self.api.sync()
        for i in to_rep:
            self.replyMessage(i[0], i[1][0], i[1][1])

    def unfollow(self, banned):
        requests = self.api.friends.getRequests(out=1)['items']
        self.api.delayedReset()
        for i in requests:
            if str(i) not in banned:
                self.api.friends.delete.delayed(user_id=i)
        self.api.sync()
        return len(requests)

    def setOnline(self):
        self.api.account.setOnline(voip=0)

    def getUserId(self, uid):
        if uid.isdigit():
            return uid
        if '=' in uid:
            uid = uid.split('=')[-1]
        if '/' in uid:
            uid = uid.split('/')[-1]
        data = self.api.users.get(user_ids=uid)
        try:
            return str(data[0]['id'])
        except TypeError:
            return None
    
    def ensureLoggedIn(self):
        self.api.account.getCounters()
        
    def getName(self, uid):
        uid = str(uid)
        if uid not in self.name_cache:    
            r = self.api.users.get(user_ids=uid)[0]
            self.name_cache[uid] = (r['first_name'], r['last_name'])
        return self.name_cache[uid]
        
    def filterComments(self, test):
        data = self.api.notifications.get(start_time=self.last_viewed_comment+1)['items']
        for rep in data:
            self.last_viewed_comment = max(self.last_viewed_comment, rep['date'])
            
            def _check(s):
                if 'photo' in s:
                    return str(s['photo']['owner_id']) == self.self_id
                if 'video' in s:
                    return str(s['video']['owner_id']) == self.self_id
                if 'post' in s:
                    return str(s['post']['to_id']) == self.self_id
            
            if rep['type'].startswith('comment_') or rep['type'].startswith('reply_comment') and _check(rep['parent']):
                txt = rep['feedback']['text']
                if test(txt):
                    log.write('comments', txt)
                    if rep['type'].endswith('photo'):
                        print('Deleting photo comment')
                        self.api.photos.deleteComment(owner_id=self.self_id, comment_id=rep['feedback']['id'])
                    elif rep['type'].endswith('video'):
                        print('Deleting video comment')
                        self.api.video.deleteComment(owner_id=self.self_id, comment_id=rep['feedback']['id'])
                    else:
                        print('Deleting wall comment')
                        self.api.wall.deleteComment(owner_id=self.self_id, comment_id=rep['feedback']['id'])