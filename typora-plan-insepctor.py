import os
import re
import sys
import time
import datetime
import subprocess

from rich import print

import unicodedata
 
t = ["월", "화", "수", "목", "금", "토", "일"]
M_line = "# Monthly Checklist"
T_line = "# Today I did"
D_line = "# Daily I did"


def preformat_cjk(string, width, align='<', fill=' '):
    count = (width - sum(1 + (unicodedata.east_asian_width(c) in "WF")
                         for c in string))
    return {
        '>': lambda s: fill * count + s,
        '<': lambda s: s + fill * count,
        '^': lambda s: fill * (count / 2)
                       + s
                       + fill * (count / 2 + count % 2)
    }[align](string)


def autoreload(path, wait):
    last_mtime = max(file_times(path))

    while True:
        max_mtime = max(file_times(path))

        print(last_mtime, max_mtime)
        if max_mtime > last_mtime:
            last_mtime = max_mtime
            run()
            # print("[bold blue]Restarting process.[/]")
            # process.kill()
            # process = subprocess.Popen(command, shell=True)

        time.sleep(wait)


def file_filter(name):
    return (not name.startswith(".")) and (not name.endswith(".swp"))


def file_times(path):
    for top_level in filter(file_filter, os.listdir(path)):
        yield os.stat(os.path.join(os.path.abspath(path), top_level)).st_mtime // 10


def create_planner(planner_name):

    if os.path.exists(planner_name):
        return

    f = open(planner_name, "w")
    f.write("\n".join([M_line, T_line, D_line]))
    f.close()

def parsing(planner_name):
    lines = [line.rstrip("\n") for line in open(planner_name, "r") if line.rstrip('\n')]
    ms_idx = lines.index(M_line) 
    ts_idx = lines.index(T_line)
    ds_idx = lines.index(D_line)

    return lines[ms_idx:ts_idx], lines[ts_idx:ds_idx], lines[ds_idx:]

def write_monthly(m_line, cur_day, cur_time):
    n_line = "\[{}][{}]{}"
    m_re = re.compile(".+[[](.*)[]].*[[](.*)[]]") 

    new_m_line = []

    for ml in m_line:
        m_re_obj = m_re.match(ml)
        new_line = ml

        if new_line.find("- [ ]") > -1:
            prefix, last = new_line.split("- [ ]")

            if m_re_obj:
                if not m_re_obj.group(1): # 작성 날짜 있을 경우 pass
                    new_line = prefix + "- [ ] " + n_line.format(cur_day, "", last)
            else:
                new_line = prefix + "- [ ] " + n_line.format(cur_day, "", last)
                # new_line = prefix + '- [ ]' + preformat_cjk(last, 70, fill="-") + ' ' * (30 - len(last)) + n_line.format(cur_day, "")
                
        m_re_obj = m_re.match(new_line)
        if new_line.find("- [x]") > -1 and m_re_obj:
            prefix, last = new_line.split("- [x]")
            if not m_re_obj.group(2):
                new_line = prefix + "- [x] " + last[:6] + "[" + "-".join([cur_day, cur_time]) + "]" + " " + last[8:]
        
        new_m_line.append(new_line)
    
    return new_m_line

def write_today(m_line, today_title, cur_day, cur_time):
    m_re = re.compile(".+[[](.*)[]].*[[](.*)[]]") 
    new_t_line = []

    reverse_idx = [idx for idx, line in enumerate(m_line) if line.find("- [x]") > -1]

    for ridx in reverse_idx[::-1]:
        if m_re.match(m_line[ridx]).group(2)[:2] != cur_day:
            continue

        new_t_line.append(m_line[ridx])
        prefix_depth = m_line[ridx].find("-")

        while ridx >= 0:
            ridx -= 1

            if ridx in reverse_idx:
                break

            cur_depth = m_line[ridx].find("-")

            if cur_depth <= prefix_depth and m_line[ridx].find("- [ ]") < 0:
                new_t_line.append(m_line[ridx])
            elif cur_depth > prefix_depth:
                break

            prefix_depth = cur_depth

    today_title += '|' * len(reverse_idx)

    return [today_title] + new_t_line[::-1]


def run():
    planner_name = datetime.datetime.now().strftime("%Y-%m") + ".md"
    cur_date = datetime.datetime.now()
    cur_day, cur_time = cur_date.strftime("%d-%H:%M").split("-")
    today_title = "## " + cur_date.strftime("%m / %d") + " ( {} )".format(t[cur_date.weekday()])

    # print(today_title)

    create_planner(planner_name)

    m_line, t_line, d_line = parsing(planner_name)
    # m_line, t_line, d_line = parsing("2020-08.md")

    for idx, dl in enumerate(d_line):
        if dl.startswith(today_title):
            break
    if idx:
        d_line = d_line[:idx]

    # print(m_line, t_line, d_line)
    m_line = write_monthly(m_line, cur_day, cur_time)
    t_line = t_line[:1] + write_today(m_line[1:], today_title, cur_day, cur_time)
    planner = m_line + t_line + d_line + t_line[1:]

    with open(planner_name, "w") as f:
        f.write("\n".join(planner))

path = '.'
wait = 1

run()
autoreload(path, wait)
