import json
import uuid
from typing import Iterator

import oyaml as yaml
import requests

AUTH_SERVERS = {
    'mj': lambda _id: 'https://api.mojang.com/users/profiles/minecraft/{}'.format(_id),
    'ls': lambda _id: 'https://mcskin.littleservice.cn/api/yggdrasil/api/users/profiles/minecraft/{}'.format(_id)
}
WHITELIST_FILE = 'config.yml'
HELP = '''\
Available commands:
- a <auth> <id> | add <auth> <id>: whitelist this user with specified authorizing service.
- d <auth> <id> | del <auth> <id>: remove specific user from the whitelist, with given authorizing service.  
- h | help: show this help menu.
- l | p | list | print: print changes ready in memory.
- w | write: save changes to disk.
- q | quit: quit without saving.
- wq | qw: save and quit.
'''
INVALID = 'Invalid command.'


def get_uuid_by_user_name(user_name, api):
    r = requests.get(api(user_name))
    j = json.loads(r.text)
    print(r.text)
    if str(j.get('name')).lower() == user_name.lower():
        return str(uuid.UUID(j.get('id')))


def whitelist_update_players(config_file, players_to_add: Iterator[str],
                             players_to_remove: Iterator[str], encoding='utf-8'):
    """
    Add players to config file in an atomic way.
    :param players_to_add: the players to be added. if you want to add one player,
    pass a singleton collection instead of the bare string.
    """
    players_added = 0
    with open(config_file, 'r+', encoding=encoding) as f:
        cfg = yaml.safe_load(f)

        # keep the file open to prevent conditional racing
        # deduplicate and add players in memory, O(n)
        if not isinstance(cfg['whitelist'], list):
            cfg['whitelist'] = []
        existing_players = set(cfg['whitelist'])
        for p in players_to_add:
            if p not in existing_players:
                existing_players.add(p)
                cfg['whitelist'].append(p)
                players_added += 1
        # remove players to be removed, O(n)
        players_to_remove = set(players_to_remove)
        players_removed = len(existing_players) - len(existing_players - players_to_remove)
        cfg['whitelist'] = [x for x in cfg['whitelist'] if x not in players_to_remove]

        # clear the file before writing
        f.truncate(0)
        f.seek(0)

        # write to config file
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)
    return players_added, players_removed


class PlayerEntry:
    id: str
    uuid: str
    auth_method: str

    def __init__(self, _id: str, _uuid: str, _auth_method: str):
        self.id, self.uuid, self.auth_method = _id, _uuid, _auth_method


def interactive(config_file):
    players_to_add: dict[str, PlayerEntry] = {}  # uuid -> player_entry
    players_to_remove: dict[str, PlayerEntry] = {}  # uuid -> player_entry

    while True:
        insp = input('>').lower().split(' ')
        cl = insp[0]
        if cl in {'q', 'quit', 'bye'}:
            if len(insp) != 1:
                print(INVALID)
                continue
            return
        elif cl in {'h', 'help'}:
            if len(insp) != 1:
                print(INVALID)
                continue
            print(HELP)
        elif cl in {'a', 'add', 'd', 'del'}:
            # add / delete a player
            # add <auth> <player_id>
            # del <auth> <player_id>
            if len(insp) != 3:
                print(INVALID)
                continue

            # get uuid from player id
            _, auth_method, player_id = insp
            if auth_method not in AUTH_SERVERS:
                print(f'Invalid auth server: {auth_method}.')
                continue
            player_uuid = get_uuid_by_user_name(player_id, AUTH_SERVERS[auth_method])

            if 'a' in cl:
                # add
                if player_uuid not in players_to_add:
                    players_to_add[player_uuid] = PlayerEntry(player_id, player_uuid, auth_method)
                print(f'Added player {player_id} ({player_uuid}).')
            else:
                # delete
                try:
                    # delete in memory
                    players_to_add.pop(player_uuid)
                except KeyError:
                    pass
                if player_uuid not in players_to_remove:
                    players_to_remove[player_uuid] = PlayerEntry(player_id, player_uuid, auth_method)
                print(f'Removed player {player_id} ({player_uuid}).')
        elif cl in {'p', 'print', 'l', 'list'}:
            if len(insp) != 1:
                print(INVALID)
                continue
            no_echo = True
            if players_to_add:
                no_echo = False
                print('Players to be added:')
                for p in players_to_add.values():
                    print(f'{p.id} ({p.uuid}), auth: {p.auth_method}')
            if players_to_remove:
                no_echo = False
                print('Players to be removed:')
                for p in players_to_remove.values():
                    print(f'{p.id} ({p.uuid}), auth: {p.auth_method}')
            if no_echo:
                print('There are no players to be added or removed.')
        elif cl in {'q', 'quit'}:
            if len(insp) != 1:
                print(INVALID)
                continue
            if input('Quit without saving? (y/N)').lower() == 'y':
                return
        elif cl in {'w', 'write', 'wq', 'qw'}:
            if len(insp) != 1:
                print(INVALID)
                continue
            added, removed = whitelist_update_players(
                config_file,
                [x.uuid for x in players_to_add.values()],
                [x.uuid for x in players_to_remove.values()]
            )
            players_to_add, players_to_remove = {}, {}
            print(f'{added} player(s) added. {removed} player(s) removed.')
            if 'q' in cl:
                # quit
                return


if __name__ == '__main__':
    interactive(WHITELIST_FILE)
