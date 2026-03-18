from datasets import load_dataset
import os
import pathlib
import sys
from app import auto_red_team, auto_eval
import json
from services.attack_registry.attack_registry_toolkit import REGISTRY_PATH
import services.attack_library.attack_library_toolkit as attack_library

TEST_MODELS = [
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "anthropic/claude-3.5-sonnet",
    "google/gemini-2.0-flash-001",
    "meta-llama/llama-3.3-70b-instruct",
    "mistralai/mistral-large-2411",
    "deepseek/deepseek-v3",
    "qwen/qwen-2.5-72b-instruct",
    "anthropic/claude-3-haiku"
]
# ^^^ see the avaliable models at OpenRouter: https://openrouter.ai/models

#                           AutoRedTeam Loop
# ______________________________________________________________________

def evaluate_autoredteamer(dataset, models=TEST_MODELS):

    for target_model_name in models:
        # Start from last checkpoint <---- will not work after introducing multiple models in the loop - Felipe.
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            registry = json.load(f)
        
        # -4 for now because accidentally sent 4 to begin with
        example_count = (len(registry) - 4)
        print(f"Starting evaluation from example {example_count + 1} out of {len(dataset)} total examples.")
        asr = 0
        total_queries = 0
        max_queries = 5
        test_cases = 1

        for example in dataset:
            # Header for each example
            example_count += 1
            print("=" * 50)
            print (f"Evaluating Example: {example_count}")
            print("=" * 50)

            # Run auto red teaming
            results = auto_red_team(target_model_name, example['prompt'], max_queries, test_cases)
            attack_success = results["correctness"]
            num_queries = results["cost"]

            # Collect and print the results
            if num_queries == max_queries:
                print("Max queries reached.")
            if attack_success == 1:
                print("Attack Successful!")
                asr += 1
            else:
                print("Attack Failed.")
            total_queries += num_queries
            print(f"Number of Queries Used: {num_queries}")
        
        # Final results
        print("\n" + "=" * 50)
        print("Evaluation Complete For: ", target_model_name)
        print("=" * 50)
        print(f"Attack Success Rate (ASR): {asr / example_count:.2f}")
        print(f"Average Number of Queries Per Example: {total_queries / example_count:.2f}")
        print(f"Total Queries Used: {total_queries}")
        print(f"Total Examples Evaluated: {example_count}")

        # optional: reset the stats in the attack library for the next model,
        # not sure about the implications, it might be okay to leave as it is - Felipe.
        
        # attack_library.reset_stats()


#                           Baseline Loop
# ______________________________________________________________________
def evaluate_baseline(dataset, models=TEST_MODELS):

    for target_model_name in models:
        asr = 0
        example_count = 0
        for example in dataset:
            # Header for each example
            example_count += 1
            print("=" * 50)
            print (f"Evaluating Example: {example_count}")
            print("=" * 50)

            # Run auto red teaming
            results = auto_eval(target_model_name, example['context'], example['prompt'])
            attack_success = results["correctness"]

            if attack_success == 1:
                print("Attack Successful!")
                asr += 1
            else:
                print("Attack Failed.")
        
        # Final results
        print("\n" + "=" * 50)
        print("Baseline Evaluation Complete")
        print("=" * 50)
        print(f"Attack Success Rate (ASR): {asr / example_count:.2f}")
        print(f"Total Examples Evaluated: {example_count}")



if __name__ == "__main__":
    # Load dataset
    dataset = load_dataset("walledai/HarmBench", "standard", split="train")
    if hasattr(dataset, 'keys'):
        print("Available splits:", dataset.keys())
        dataset = dataset["train"]

    print(type(dataset[0]))
    print(dataset[0])

    eval_pattern = input("Enter 1 or 2")
    if eval_pattern == "1":
        print("What's up guys! Welcome back to another evaluation session. Today, we're going to be evaluating the performance of our auto red teaming system on the HarmBench dataset. Let's dive right in!")
        evaluate_autoredteamer(dataset)
        print("Evaluation finished. Results have been printed above.")
        print("All done!")
    elif eval_pattern == "2":
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            registry = json.load(f)
        ASR = 0
        query_count = 0
        for entry in registry:
            if entry["correctness"] == 1:
                ASR += 1
            query_count += entry["cost"]
        ASR = ASR / (len(registry) - 4)
        print(f"Attack Success Rate (ASR) from registry: {ASR:.2f}")
        print(f"Total Queries Used from registry: {query_count}")

        
        

        

