# src/liquibase_agent/cli/main.py
import argparse
from liquibase_agent.agent.create_changeset import CreateChangesetAgent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    args = parser.parse_args()

    agent = CreateChangesetAgent()
    print(agent.question(args.prompt))
