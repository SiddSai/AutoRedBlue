from agents.red_team.router import RedTeam

def auto_red_team(prompt, max_attempts=5, test_cases=1):

    red_team = RedTeam()
    red_team.compile_app()

    init_state = {
        "user_input": prompt,
        "risks": {},
        "seed_prompts": [],
        "conversations": [],
        "scores": [],
        "messages": [],
        "current_iter": 0,
        "max_iter": max_attempts,
        "num_test_cases": test_cases,
        "current_test_case": 0,
        "registry": []
    }

    response = red_team.invoke(init_state)
    return response["registry"][0]
