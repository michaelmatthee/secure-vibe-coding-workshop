import sys
import os
import json
import time
import sys
import threading
from contextlib import redirect_stdout, redirect_stderr
import argparse
from aider.repo import GitRepo
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput
from tqdm import tqdm
from git import Repo
import shutil
from pathlib import Path
from constants import *


# Aider has its own configure file, need to map the exact same model name
MODEL_MAPPINGS = {
    'gpt-4.1-2025-04-14': 'gpt-4.1',
    'gpt-4o-mini-2024-07-18': 'gpt-4o-mini',
    'o4-mini-2025-04-16': 'o4-mini',
    'o3-2025-04-16': 'o3',
    'o3-mini-2025-01-31': 'o3-mini',
    'o1-2024-12-17': 'o1',
    'gpt-oss-120b': 'openai/gpt-oss-120b'
}


class AiderRunner:
    def __init__(self, model_name, prompt_type):
        self.log_dir = f"/.aider/"
        self.prompt_type = prompt_type
        os.makedirs(self.log_dir, exist_ok=True)

        if model_name in MODEL_MAPPINGS:
            self.model_name = MODEL_MAPPINGS[model_name]
        else:
            self.model_name = model_name
        self.model = Model(self.model_name)
        self.model.use_repo_map = True
        self.model.use_temperature = 0
        self.model.temperature = 0

        if model_name in OPENAI_REASONING_MODELS:
            self.model.set_reasoning_effort("medium")
        if "gemini" in model_name.lower():
            if not hasattr(self.model, 'extra_params') or self.model.extra_params is None:
                self.model.extra_params = {}
            self.model.extra_params['thinkingConfig'] = {
                'thinkingBudget': 8000}

        self.model.set_thinking_tokens(8000)

        self.io = InputOutput(yes=True)
        self.coder_settings = {
            'main_model': self.model,
            'auto_lint': False,
            'edit_format': 'diff',
        }

    @staticmethod
    def run_with_timeout(func, timeout, *args, **kwargs):
        result = [None]
        exception = [None]
        completed = [False]

        def worker():
            try:
                result[0] = func(*args, **kwargs)
                completed[0] = True
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()
        thread.join(timeout)

        if not completed[0]:
            return False, "Timeout occurred"
        if exception[0]:
            return False, str(exception[0])
        return True, result[0]

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
        self.io.chat_history_file = Path(
            self.log_dir).resolve() / 'aider-chat-log.md'
        self.io.chat_history_file.write_bytes(b"")

        os.environ['AIDER_ANALYTICS_LOG'] = os.path.abspath(
            os.path.join(self.log_dir, 'aider-analytics-log.jsonl'))
        os.environ['AIDER_AUTO_CONFIRM'] = "1"
        os.environ['AIDER_DISABLE_PLAYWRIGHT'] = "true"
        
        repo_base = Repo(repo_folder)
        changed_file_path = f"{repo_folder}/{changed_file}"

        mask_id = self.commit(repo_base)

        os.chdir(repo_folder)
        repo_aider = GitRepo(io=self.io, fnames=[], git_dname=None,
                             subtree_only=True, models=self.model.commit_message_models())
        coder = Coder.create(
            io=self.io, **self.coder_settings, repo=repo_aider)

        system_prompt = system_prompt.replace(
            " Only return the code to be filled in the masked region. DO NOT include any other information, such as a preamble or suffix.", "")
        user_prompt = AGENT_USER_PEOMPT.format(changed_file=changed_file)
        prompt = system_prompt + user_prompt

        # Run with timeout
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            success, result = self.run_with_timeout(
                coder.run, 1200, prompt)  # 1200 secs timeout
            if success or result != "Timeout occurred":
                break
            retry_count += 1
            time.sleep(1)  # Brief pause between retries

        if success:
            with open(changed_file) as f:
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

    client = AiderRunner(args.model_name, args.prompt_type)
    diff, response = client.run(
        args.system_prompt, args.repo_folder, args.changed_file)

    Path(f'/diff/aider-{args.model_alias}-filled-code-{args.context_type}-{args.prompt_type}-{args.mode}.diff').write_text(diff)
    Path(f'/completions/aider-{args.model_alias}-filled-code-{args.context_type}-{args.prompt_type}-{args.mode}_code_completion.txt').write_text(response)


if __name__ == "__main__":
    main()
