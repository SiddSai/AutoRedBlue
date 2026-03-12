from datasets import load_dataset
import os
import pathlib
import sys
from app import auto_red_team, auto_eval
import json


# Load dataset
dataset = load_dataset("walledai/HarmBench", "standard", split="train")
dataset = dataset[:100]

# Evaluation loop
def evaluate(dataset):
    asr = 0
    total_queries = 0
    max_queries = 5
    example_count = 0
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


"""
Baseline Evaluation loop

Just a sketch! - Felipe
"""
def evaluate_baseline(dataset):
    asr = 0
    example_count = 0


    for example in dataset:
        # Header for each example
        example_count += 1
        print("=" * 50)
        print (f"Evaluating Example: {example_count}")
        print("=" * 50)

        # Run auto red teaming
        results = auto_eval(example['context'], example['prompt'])
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
    print("What's up guys! Welcome back to another evaluation session. Today, we're going to be evaluating the performance of our auto red teaming system on the HarmBench dataset. Let's dive right in!")
    evaluate(dataset)
    print("Evaluation finished. Results have been printed above.")
    print("All done!")
        
        
        

        

