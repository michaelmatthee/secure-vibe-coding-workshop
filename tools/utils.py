import os
import subprocess


def docker_image_exists(image_name):
    result = subprocess.run(
        ['docker', 'image', 'inspect', image_name],
        capture_output=True,
        text=True,
        check=False
    )
    return result.returncode == 0


def get_docker_image(id):
    # only pull docker image if we don't already have it
    image_name = f"n132/arvo:{id}-fix"

    proc_check = subprocess.run(
        ["docker", "image", "inspect", image_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if proc_check.returncode != 0:
        # Image does not exist locally, pull it
        proc_pull = subprocess.run(
            ["docker", "pull", image_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if proc_pull.returncode != 0:
            return False

    return True


def get_c_cpp_file(base_path: str):
    c_path = base_path + '.c'
    cpp_path = base_path + '.cpp'
    if os.path.exists(c_path):
        path = c_path
    elif os.path.exists(cpp_path):
        path = cpp_path
    else:
        print(
            f'This file does not exist with a c or cpp extension: {base_path}')
        return
    with open(path, 'r') as f:
        content = f.read()
    return content
