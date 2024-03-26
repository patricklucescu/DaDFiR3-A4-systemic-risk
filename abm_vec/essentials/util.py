from git import Repo


def get_git_root_directory():
    """
    | Get the root directory of the git repository.

    :return: The root directory of the git repository.
    """
    repo = Repo(__file__, search_parent_directories=True)
    return repo.working_dir
