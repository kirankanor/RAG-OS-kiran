#!/usr/bin/env python3
"""Seed the local dev database with a demo user, documents, strategies, an
experiment run, an evaluation dataset + run, and a decision.

Usage:
    uv run python scripts/seed_data.py
    uv run python scripts/seed_data.py --files a.txt b.pdf   # seed with your own files instead
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from modules.corpus_analysis.application.commands.analyze_corpus import AnalyzeCorpusCommand
from modules.decisions.application.commands.make_decision import MakeDecisionCommand
from modules.documents.application.commands.upload_document import UploadDocumentCommand
from modules.evaluation.application.commands.create_dataset import CreateDatasetCommand
from modules.evaluation.application.commands.run_evaluation import RunEvaluationCommand
from modules.experiments.application.commands.create_experiment import CreateExperimentCommand
from modules.experiments.application.commands.run_experiment import RunExperimentCommand
from modules.experiments.domain.models.experiment_config import ExperimentConfig
from modules.projects.application.commands.create_project import CreateProjectCommand
from modules.strategies.application.commands.generate_strategies import GenerateStrategiesCommand
from modules.users.application.services.user_service import UserService
from modules.users.domain.exceptions import EmailAlreadyRegisteredError

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demo-password-123"
SAMPLE_TEXT = (
    "Cats purr and sleep most of the day. A cat's whiskers help it sense its surroundings.\n\n"
    "Rockets burn fuel to escape Earth's gravity. Multi-stage rockets shed weight as fuel burns.\n"
)


def _demo_files(tmp_dir: Path) -> list[str]:
    path = tmp_dir / "demo.txt"
    path.write_text(SAMPLE_TEXT, encoding="utf-8")
    return [str(path)]


def seed(file_paths: list[str] | None = None) -> None:
    users = UserService()
    try:
        user = users.register(DEMO_EMAIL, DEMO_PASSWORD, "Demo User")
        print(f"Created user {user.email}")
    except EmailAlreadyRegisteredError:
        user = users.repository.get_user_by_email(DEMO_EMAIL)
        print(f"Reusing existing user {user.email}")

    owned_tmp = None
    if not file_paths:
        owned_tmp = tempfile.TemporaryDirectory()
        file_paths = _demo_files(Path(owned_tmp.name))
    try:
        doc_ids = [UploadDocumentCommand().execute(Path(fp).stem, Path(fp).name, Path(fp).read_bytes()).id
                   for fp in file_paths]
        print(f"Uploaded {len(doc_ids)} document(s)")

        profile = AnalyzeCorpusCommand().execute(file_paths, name="seed-corpus")
        print(f"Analyzed corpus: {profile.statistics.num_documents} doc(s)")

        strategies = GenerateStrategiesCommand().execute(count=3, persist=True)
        print(f"Created {len(strategies)} strategies: {[c.strategy.name for c in strategies]}")

        config = ExperimentConfig(runner="retrieval", file_paths=file_paths,
                                  queries=["how do cats sleep", "how do rockets work"])
        experiment = CreateExperimentCommand().execute(
            "seed-experiment", config, [str(c.strategy.id) for c in strategies])
        experiment = RunExperimentCommand().execute(str(experiment.id))
        print(f"Ran experiment '{experiment.name}': status={experiment.status.value}")

        dataset = CreateDatasetCommand().execute("seed-dataset", [
            {"query": "how do cats sleep", "relevant_texts": ["Cats purr"]},
            {"query": "how do rockets work", "relevant_texts": ["Rockets burn fuel"]},
        ])
        eval_runs = RunEvaluationCommand().execute(dataset.id, str(experiment.id))
        print(f"Evaluated {len(eval_runs)} run(s)")

        if any(r.status.value == "completed" for r in eval_runs):
            decision = MakeDecisionCommand().execute(str(experiment.id), dataset.id,
                                                      corpus_profile_id=profile.id)
            winner = decision.winner.strategy_name if decision.winner else "none"
            print(f"Decision made: winner={winner}")
        else:
            print("Skipped decision: no completed evaluation runs.")

        project = CreateProjectCommand().execute(
            "Seed Project", str(user.id), description="Created by seed_data.py",
            document_ids=doc_ids, experiment_ids=[str(experiment.id)])
        print(f"Created project '{project.name}' (id={project.id})")
    finally:
        if owned_tmp is not None:
            owned_tmp.cleanup()

    print("\nSeed complete.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--files", nargs="+", default=None,
                    help="Files to seed with instead of the built-in sample text.")
    args = ap.parse_args()
    seed(args.files)


if __name__ == "__main__":
    main()
