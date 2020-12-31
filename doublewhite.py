import requests
import re
import json
import uuid
import os

AUTH_SERVERS = {
    'mj': lambda _id: 'https://api.mojang.com/users/profiles/minecraft/{}'.format(_id),
    'ls': lambda _id: 'https://mcskin.littleservice.cn/api/yggdrasil/api/users/profiles/minecraft/{}'.format(_id)
}
WHITELIST_FILE = 'whitelist.txt'
HELP = '''\
Help of Double White interactive:
- a <auth> <id> | add <auth> <id>: whitelist this user with specified authorizing service.
- d <auth> <id> | del <auth> <id>: remove specific user from the whitelist, with given authorizing service.  
- h | help: show this help menu.
- q | quit: save and quit.
'''


def get_uuid_by_user_name(user_name, api):
    r = requests.get(api(user_name))
    j = json.loads(r.text)
    print(r.text)
    if str(j.get('name')).lower() == user_name.lower():
        return str(uuid.UUID(j.get('id')))


if __name__ == '__main__':
    print('[+] Double White: Whitelist manager for double auth-server based authorizing servers.')

    if os.path.exists(WHITELIST_FILE):
        if input('WARNING: File {} exists and thus will be overwrite! Continue? (y/N)'.format(WHITELIST_FILE)).lower() != 'y':
            print('Never mind.')
            exit(0)

    with open(WHITELIST_FILE, 'w') as f:
        whitelist = set()
        while True:
            try:
                ins = input('>')

                # quit
                if ins.lower() == 'q' or ins.lower() == 'quit':
                    break

                # help
                if ins.lower() == 'h' or ins.lower() == 'help':
                    print(HELP)

                # add / del
                if ins.lower().startswith('a ') or ins.lower().startswith('add ') \
                        or ins.lower().startswith('d ') or ins.lower().startswith('del '):
                    arr = ins.split(' ')
                    if len(arr) != 3:
                        print('Invalid instruction: {}'.format(ins))
                        continue

                    auth = arr[1]
                    id_ = arr[2]

                    if auth not in AUTH_SERVERS.keys():
                        print('Invalid auth service: {}'.format(auth))
                        continue

                    print('Fetching UUID ...')
                    uuid_ = get_uuid_by_user_name(id_, AUTH_SERVERS[auth])
                    if ins.lower().startswith('a ') or ins.lower().startswith('add '):
                        # add
                        whitelist.add(uuid_)
                        print('Added user {user} ({uuid})'.format(user=id_, uuid=uuid_))
                    else:
                        # del
                        if uuid_ in whitelist:
                            whitelist.remove(uuid_)
                            print('Deleted user {user} ({uuid}) from whitelist.'.format(user=id_, uuid=uuid_))
                        else:
                            print('User {user} ({uuid}) has not been whitelisted.'.format(user=id_, uuid=uuid_))
            except Exception as e:
                print('An exception occurred: {}. May I continue? Sure! ;)'.format(e))
        f.writelines([x + '\n' for x in whitelist])
        print('{} line(s) written.'.format(len(whitelist)))
        exit(0)