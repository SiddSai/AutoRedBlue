from datasets import load_dataset
import os
import pathlib
import sys
from app import auto_red_team
import json
from services.attack_registry.attack_registry_toolkit import REGISTRY_PATH



# Evaluation loop
def evaluate_autoredteamer(dataset):
    # Start from last checkpoint
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
        results = auto_red_team(example['prompt'], max_queries, test_cases)
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
    print("Evaluation Complete")
    print("=" * 50)
    print(f"Attack Success Rate (ASR): {asr / example_count:.2f}")
    print(f"Average Number of Queries Per Example: {total_queries / example_count:.2f}")
    print(f"Total Queries Used: {total_queries}")
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


        





def evaluate_base_harmbench(dataset):
    # This is just a placeholder for the base evaluation function that doesn't use auto red teaming.
    # You can implement this to get a baseline performance of the model on the HarmBench dataset without any attacks.
    pass
        
        

        

