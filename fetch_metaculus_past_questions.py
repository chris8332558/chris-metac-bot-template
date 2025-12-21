import asyncio
import datetime
import json
import os
import re
import dotenv
dotenv.load_dotenv()
import requests

# import forecasting_tools

METACULUS_TOKEN = os.getenv("METACULUS_TOKEN")
#Tournament ID, File_name
Q2_2025_QUARTERLY_CUP = (32721, "quarterly_cup_q2-2025_metaculus_questions.json")
Q1_2025_QUARTERLY_CUP = (32630, "quarterly_cup_q1-2025_metaculus_questions.json")
Q4_2024_QUARTERLY_CUP = (3672, "quarterly_cup_q4-2024_metaculus_questions.json")
Q3_2024_QUARTERLY_CUP = (3349, "quarterly_cup_q3-2024_metaculus_questions.json")
Q2_2024_QUARTERLY_CUP = ("quarterly-cup-2024q2", "quarterly_cup_q2-2024_metaculus_questions.json")
Q1_2024_QUARTERLY_CUP = ("quarterly-cup-2024q1", "quarterly_cup_q1-2024_metaculus_questions.json")
Q4_2023_QUARTERLY_CUP = ("quarterly-cup-2023q4", "quarterly_cup_q4-2023_metaculus_questions.json")
Q3_2023_QUARTERLY_CUP = ("quarterly-cup-2023q3", "quarterly_cup_q3-2023_metaculus_questions.json")

contest_2023 = ("2023-contest", "2023-contest_metaculus_questions.json")

bridgewater_2025 = ("bridgewater", "bridgewater_binary_resolved_metaculus_questions.json")
market_pulse_25q2 = ("market-pulse-25q2", "market-pulse-25q2_binary_resolved_metaculus_questions.json")
nuclear_risk_forecasting_tournament = ("nuclear-risk-forecasting-tournament", "nuclear-risk-forecasting-tournament_metaculus_questions.json")
global_pulse = ("global-pulse", "global_pulse_metaculus.json")
flusight = ("flusight-challenge23-24", "flusight-challenge23-24_metaculus.json")

#Tournament ID, File_name TUPLE
# TOURNAMENT = =

AUTH_HEADERS = {"headers": {"Authorization": f"Token {METACULUS_TOKEN}"}}
API_BASE_URL = "https://www.metaculus.com/api"


PAGE_SIZE = 100 #metaculus hard upper limit

def save_questions(file_name, questions):
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
        
def list_questions_for_llm(
    tournament_id: int,
) -> list[dict]:
    """
    Fetch {count} resolved binary questions from a Metaculus tournament
    and return a lean list of dicts with the keys the LLM needs:
      id, title, description, resolution_criteria, type, status, resolution
    """
    clean_rows: list[dict] = []
    offset = 0
    while True:
        url_qparams = {
            "limit": PAGE_SIZE,
            "offset": offset,
            "order_by": "-open_time",
            "tournaments": [tournament_id],
            "statuses": "resolved",
            "include_description": "true",
        }
        url = f"{API_BASE_URL}/posts/"
        response = requests.get(url, **AUTH_HEADERS, params=url_qparams)  # type: ignore
        if not response.ok:
            raise Exception(response.text)

        payload = response.json()                   # already a dict
        # print(payload)
        if not payload["results"]:
            break
        for post in payload["results"]:

            if post.get("group_of_questions"):
                clean_rows.extend(post["group_of_questions"]["questions"])
            elif post.get("question"):
                q = post["question"]                    
                clean_rows.append(q)
            else:
                post_str = json.dumps(post, ensure_ascii=False)
                print(f"Couldn't extract question from post\nkeys:{list(post.keys())}\npost:{post_str[:50]}...")

        offset += PAGE_SIZE
        print("Check")
    return clean_rows
    

import time
TOURNAMENTS = [
    Q2_2025_QUARTERLY_CUP,
    Q1_2025_QUARTERLY_CUP,
    Q4_2024_QUARTERLY_CUP,
    Q3_2024_QUARTERLY_CUP,
    Q2_2024_QUARTERLY_CUP,
    Q1_2024_QUARTERLY_CUP,
    Q4_2023_QUARTERLY_CUP,
    Q3_2023_QUARTERLY_CUP,
    contest_2023,
    bridgewater_2025,
    market_pulse_25q2,
    nuclear_risk_forecasting_tournament,
    global_pulse,
    flusight,
]

for tournament in TOURNAMENTS:
    id = tournament[0]
    filename = tournament[1]
    data_dir = "data/"
    output_path = os.path.join(data_dir, filename)
    if os.path.exists(output_path):
        print(f"Already exists, skipping: {output_path}")
        continue
    print(f"Getting questions from tournament: {filename}")
    questions = list_questions_for_llm(id)
    time.sleep(10)
    before_filter_num = len(questions)
    questions = [
        q for q in questions
        if q["resolution"].lower().strip() not in ["annulled"] #to remove ambigious resolved questions
    ]
    print(f"# of questions (filtered to valid resolutions only):\n {before_filter_num} -> {len(questions)}")
    save_questions(output_path, questions)
    break
