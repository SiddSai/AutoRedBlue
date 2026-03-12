from agents.red_team.router import RedTeam
from agents.gt_eval.router import RedTeam as EvalTeam

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

def auto_eval(context, prompt):
    eval_red_team = EvalTeam()
    eval_red_team.compile_app()

    input = context + "\n\n" + prompt

    init_state = {
        "user_input": input,
        "conversation": [],
        "score": {},
        "messages": [],
    }

    response = eval_red_team.invoke(init_state)
    response["correctness"] = 1 if response["score"]["attack_score"] else 0

    return response