"""Source code main file to be called by containerized run file"""
import json
from typing import List

import matplotlib.pyplot as plt
import requests
from espn_api.football import League, Pick, Player


def _get_bid_amounts(draft: List[Pick]):
    team_stats = {k: [] for k in [pick.team.owner for pick in draft]}
    for pick in draft:
        team_stats[pick.team.owner].append(pick.bid_amount)
    return team_stats


def _get_pick_order(draft: List[Pick]):
    team_stats = {k: [] for k in [pick.team.owner for pick in draft]}
    num_players = len(team_stats)
    for pick in draft:
        team_stats[pick.team.owner].append(
            _get_pick_num(pick.round_num,
                          pick.round_pick,
                          num_players=num_players))
    return team_stats


def _get_pick_num(round_num: int, round_pick: int, num_players=12) -> int:
    return num_players * (round_num - 1) + round_pick


def _get_pick_scores(league: League):
    draft = league.draft
    cum_draft_value = {pick.team.owner: 0 for pick in draft}
    for pick_num, pick in enumerate(draft):
        if not pick_num % 20:
            print(f'Processed {pick_num} picks')
        player = league.player_info(playerId=pick.playerId)
        cum_draft_value[pick.team.owner] += _evaluate_draft_value(player, pick)
    return cum_draft_value


def _evaluate_draft_value(player: Player, pick: Pick):
    return float(player.total_points) / float(pick.bid_amount)


def _output_owners(league: League) -> None:
    owners = [team.owner for team in league.teams]
    with open('../../resources/results.json', 'a',
              encoding='utf-8') as out_file:
        out_file.write(json.dumps(owners))


def _analyze_draft_value(league: dict):
    D = _get_pick_scores(league)
    sort = dict(sorted(D.items(), key=lambda item: item[1]))
    plt.bar(range(len(sort)), list(sort.values()), align='center')
    plt.xticks(range(len(sort)),
               list(sort.keys()),
               fontsize='x-small',
               rotation=22)
    plt.savefig('./visualizations/draft_value_bar.png')


if __name__ == '__main__':
    # with open('../../resources/league_sw_onethree.json', encoding='utf-8') as league_file:
    #     creds = json.loads(league_file.read())
    # league = League(league_id=creds['league_id'], year=2022, espn_s2=creds['espn_s2'], swid=creds['swid'])
    # _output_owners(league)

    r = requests.get(
        'https://api.groupme.com/v3/groups/93229120/messages?token=vBYhYTUNjfrzF78ZgYiallxe8F98jLLsCA0k43fD'
    )
    print(r.status_code)
    print(r.json()['response'])

#
