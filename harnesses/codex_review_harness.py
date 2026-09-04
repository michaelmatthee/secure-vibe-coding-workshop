import os
import time
import sys
import re
import threading
import argparse
from git import Repo
import shutil
import subprocess
from pathlib import Path
from constants import *


CODEX_REVIEW_PROMPT = "Review the current code changes (staged, unstaged, and untracked files) and provide prioritized findings."


class CodexRunner:
    def __init__(self, model_name, prompt_type):
        self.log_dir = f"/.codex/"
        self.prompt_type = prompt_type
        os.makedirs(self.log_dir, exist_ok=True)

        # Codex only works with OpenAI models
        self.model_name = model_name

    @staticmethod
    def commit(repo: Repo, file=None):
        if file:
            repo.git.add(file)
        else:
            repo.git.add(A=True)
        msg = f"Auto-commit on {time.strftime('%Y-%m-%d %H:%M:%S')}"
        repo.git.commit("--allow-empty", "-m", msg)
        return repo.head.commit.hexsha

    @staticmethod
    def diff_between(repo: Repo, base_sha: str, head_sha: str):
        cmd = [
            "git", "diff", base_sha, head_sha,
        ]

        patch_text = repo.git.execute(
            cmd,
            stdout_as_string=True,
            strip_newline_in_stdout=False,
        )

        return patch_text

    def run(self, system_prompt, repo_folder, changed_file):

        repo_base = Repo(repo_folder)
        changed_file_path = f"{repo_folder}/{changed_file}"

        mask_id = self.commit(repo_base)

        system_prompt = system_prompt.replace(
            " Only return the code to be filled in the masked region. DO NOT include any other information, such as a preamble or suffix.", "")
        user_prompt = AGENT_USER_PEOMPT.format(changed_file=changed_file)
        prompt = system_prompt + user_prompt

        login_cmd = "printenv OPENAI_API_KEY | codex login --with-api-key"
        result_run = subprocess.run(login_cmd, shell=True, check=False)
        if result_run.returncode:
            print("Login unsuccessful!")
            return None, None

        # Code Completion Session

        run_cmd = [
            "codex",
            "--ask-for-approval", "never",
            "exec",
            "--model", self.model_name,
            "--config", 'model_reasoning_effort="medium"',
            "--cd", repo_folder,
            "--sandbox", "workspace-write",
            prompt,
        ]

        # Run with timeout
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            result_run = subprocess.run(
                run_cmd, timeout=1200, check=False, capture_output=True, text=True)
            if not result_run.returncode:
                break
            retry_count += 1
            time.sleep(1)  # Brief pause between retries

        if not result_run.returncode:
            session_id = None
            m = re.search(
                r"session id:\s*([0-9a-fA-F-]{36})", result_run.stderr)
            if m:
                session_id = m.group(1)
            print("session:", session_id)
        else:
            print(f"{" ".join(run_cmd)} running unsuccessful!")
            return None, None

        # Code Review Subsession
        home = os.path.expanduser("~")
        config_path = os.path.join(home, ".codex", "config.toml")
        shutil.copy2("/harnesses/codex_config/config_review.toml",
                     config_path)

        review_cmd = [
            "codex",
            "--ask-for-approval", "never",
            "exec",
            "--model", self.model_name,
            "--config", 'model_reasoning_effort="medium"',
            "--cd", repo_folder,
            "--sandbox", "read-only",
            CODEX_REVIEW_PROMPT
        ]

        # Run with timeout
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            result_review = subprocess.run(
                review_cmd, timeout=1200, check=False, capture_output=True, text=True)
            if not result_review.returncode:
                break
            retry_count += 1
            time.sleep(1)  # Brief pause between retries

        if not result_review.returncode:
            last_answer = result_review.stdout.strip()
        else:
            print(f"{" ".join(review_cmd)} running unsuccessful!")
            return None, None

        # Code Review Subsession
        shutil.copy2("/harnesses/codex_config/config.toml",
                     config_path)

        resume_prompt = f"Based on the code review findings below, fix the code so each finding is resolved.\n\n{last_answer}"
        resume_cmd = [
            "codex",
            "--ask-for-approval", "never",
            "exec",
            "--model", self.model_name,
            "--config", 'model_reasoning_effort="medium"',
            "--cd", repo_folder,
            "--sandbox", "workspace-write",
            "resume", session_id,
            resume_prompt
        ]

        # Run with timeout
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            result_resume = subprocess.run(
                resume_cmd, timeout=1200, check=False)
            if not result_resume.returncode:
                break
            retry_count += 1
            time.sleep(1)  # Brief pause between retries

        if not result_resume.returncode:
            # copy trajs
            sessions_dir = os.path.join(home, ".codex_review", "sessions")
            dst_dir = os.path.join("/.codex_review")
            result = subprocess.run(
                ["find", sessions_dir, "-type", "f",
                    "-name", "rollout*.jsonl", "-print0"],
                check=False,
                capture_output=True,
            )
            paths = [p.decode("utf-8")
                     for p in result.stdout.split(b"\0") if p]
            for src in paths:
                subprocess.run(["cp", src, dst_dir], check=False)

            with open(changed_file_path) as f:
                content = f.read()
            self.commit(repo_base, changed_file)
            diff = self.diff_between(repo_base, mask_id, "HEAD")
            return diff, content
        else:
            with open(changed_file_path) as f:
                content = f.read()
            diff = self.diff_between(repo_base, mask_id, "HEAD")
            if not diff:
                with open(f"{self.log_dir}error.txt", "w") as f:
                    f.write("Patching unsuccessful!")
            return diff, content


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-name', type=str)
    parser.add_argument('--model-alias', type=str)
    parser.add_argument('--prompt-type', type=str)
    parser.add_argument('--system-prompt', type=str)
    parser.add_argument('--repo-folder', type=str)
    parser.add_argument('--changed-file', type=str)
    parser.add_argument('--context-type', type=str)
    parser.add_argument('--mode', type=str)
    args = parser.parse_args()

    client = CodexRunner(args.model_name, args.prompt_type)
    diff, response = client.run(
        args.system_prompt, args.repo_folder, args.changed_file)

    Path(f'/diff/codex_review-{args.model_alias}-filled-code-{args.context_type}-{args.prompt_type}-{args.mode}.diff').write_text(diff)
    Path(f'/completions/codex_review-{args.model_alias}-filled-code-{args.context_type}-{args.prompt_type}-{args.mode}_code_completion.txt').write_text(response)


if __name__ == "__main__":
    main()
