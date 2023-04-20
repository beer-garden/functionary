import pytest

from functionary.config import config_file


@pytest.fixture
def fakefs(fs):
    """Wrapper around the pyfakefs fs fixture. This is provided for slightly increased
    clarity. Using this (or fs directly) results in all file access being done against
    a fake filesystem, avoiding reads and writes to the actual disk."""
    return fs


@pytest.fixture(autouse=True)
def config(fakefs):
    fakefs.create_file(config_file)
    conf = (
        "host='http://testhost'\n"
        "token='05139f102fbbce91f32153511011b7a185992f54'\n"
        "current_environment_id='e8c5c607-8b03-4e94-a93e-cd3c45c33ffd'"
    )

    with open(config_file, "w") as file_:
        file_.write(conf)
