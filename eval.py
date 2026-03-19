from datasets import load_dataset
import os
from pprint import pprint
import pathlib
import sys
from app import auto_red_team, auto_eval
import json
from services.attack_registry.attack_registry_toolkit import REGISTRY_PATH
import services.attack_library.attack_library_toolkit as attack_library
import dotenv

dotenv.load_dotenv()

TEST_MODELS = [
    "meta-llama/llama-3.3-70b-instruct",
    "mistralai/mistral-large-2411",
]
# ^^^ see the avaliable models at OpenRouter: https://openrouter.ai/models

#                           AutoRedTeam Loop
# ______________________________________________________________________

def evaluate_autoredteamer(dataset, models=TEST_MODELS, samples=50):

    for target_model_name in models:

        example_count = 0
        asr = 0
        total_queries = 0
        max_queries = 5
        test_cases = 1

        for example in dataset.select(range(int(samples))):
            # Header for each example
            example_count += 1
            print("=" * 50)
            print (f"Evaluating Example: {example_count}/{samples} on {target_model_name}")
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
def evaluate_baseline(dataset, models=TEST_MODELS, samples=50):

    baselines = {}
    for target_model_name in models:
        asr = 0
        example_count = 0
        for example in dataset.select(range(int(samples))):
            # Header for each example
            example_count += 1
            print("=" * 50)
            print (f"Evaluating Example: {example_count}/{samples} on {target_model_name}")
            print("=" * 50)

            # Run auto red teaming
            results = auto_eval(target_model_name, "", example['prompt'])
            attack_success = results["correctness"]

            if attack_success == 1:
                print("Attack Successful!")
                asr += 1
            else:
                print("Attack Failed.")
        
        # Final results
        ASR = asr / example_count
        print("\n" + "=" * 50)
        print("Baseline Evaluation Complete")
        print("=" * 50)
        print(f"Attack Success Rate (ASR): {ASR}")
        print(f"Total Examples Evaluated: {example_count}")

        baselines[target_model_name] = ASR

    print("Baselines: ")
    pprint(baselines)


if __name__ == "__main__":
    # Load dataset
    dataset = load_dataset("walledai/HarmBench", "standard", split="train")
    if hasattr(dataset, 'keys'):
        print("Available splits:", dataset.keys())
        dataset = dataset["train"]

    print(type(dataset[0]))
    print(dataset[0])

    print("\n" + "=" * 50)
    print("AutoRedBlue Evaluation Menu")
    print("=" * 50)

    print("1. Run AutoRedTeamer evaluation on HarmBench dataset")
    print("2. Run Bseline evaluation (no pipeline)")
    print("3. See stored results from registry")
    eval_pattern = input("\nEnter 1, 2 or 3:\n")
    if eval_pattern == "1":
        print("What's up guys! Welcome back to another evaluation session. Today, we're going to be evaluating the performance of our auto red teaming system on the HarmBench dataset. Let's dive right in!")
        evaluate_autoredteamer(dataset)
        print("Evaluation finished. Results have been printed above.")
        print("All done!")
    elif eval_pattern == "2":
        evaluate_baseline(dataset)
        print("Evaluation finished. Results have been printed above.")
        print("All done!")
        
    elif eval_pattern == "3":
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            registry = json.load(f)

        print("=" * 50)
        print("Stored Model Stats")
        print("=" * 50)

        models = set(entry.get("model", "unfiled") for entry in registry)
        print(f"Models in registry: {models} \n")
        
        for i, model in enumerate(models): 
            ASR = 0
            query_count = 0
            sample_count = 0
            for entry in registry:
                if entry.get("model", "unfiled") != model:
                    continue
                if entry["correctness"] == 1:
                    ASR += 1
                query_count += entry["cost"]
                sample_count += 1
            ASR = ASR / sample_count
            print(f"{i+1}. Model tested: {model}")
            print("-"*50)
            print(f"Attack Success Rate (ASR): {ASR:.2f}")
            print(f"Total Samples: {sample_count}")
            print(f"Total Queries: {query_count}")
            print()
