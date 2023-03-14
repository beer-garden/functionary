import pytest
from yaml import YAMLError

from builder import utils
from builder.models import Build, BuildLog, BuildResource
from builder.utils import BuilderError, DockerSocketConnectionError, PackageManager
from core.models import Function, Package, Team, User
from core.utils.parameter import PARAMETER_TYPE


@pytest.fixture
def user():
    return User.objects.create(username="user")


@pytest.fixture
def team():
    return Team.objects.create(name="team")


@pytest.fixture
def package_contents():
    return bytes("example package contents", encoding="utf-8")


@pytest.fixture
def environment(team):
    return team.environments.get()


@pytest.fixture
def package1(environment):
    return Package.objects.create(name="testpackage1", environment=environment)


@pytest.fixture
def package2(environment):
    return Package.objects.create(name="testpackage2", environment=environment)


@pytest.fixture
def function1(package1):
    function = Function.objects.create(
        name="function1",
        environment=package1.environment,
        package=package1,
        active=True,
    )

    function.parameters.create(name="param1", parameter_type=PARAMETER_TYPE.INTEGER)
    function.parameters.create(name="param2", parameter_type=PARAMETER_TYPE.INTEGER)

    return function


@pytest.fixture
def function2(package1):
    return Function.objects.create(
        name="function2",
        environment=package1.environment,
        package=package1,
        active=True,
    )


@pytest.fixture
def function3(package2):
    return Function.objects.create(
        name="function3",
        environment=package2.environment,
        package=package2,
        active=True,
    )


@pytest.fixture
def function4(package2):
    return Function.objects.create(
        name="function4",
        environment=package2.environment,
        package=package2,
        active=True,
    )


@pytest.fixture
def package_definition(function1):
    package_def = {
        "name": function1.name,
        "summary": function1.summary,
        "display_name": function1.name,
        "language": "python",
    }

    return package_def


@pytest.fixture
def build(package1, user, environment, package_definition):
    build = Build.objects.create(
        creator=user, environment=environment, package=package1
    )
    BuildResource(
        build=build,
        package_contents=bytes(f"{package_definition}", encoding="utf-8"),
        package_definition=package_definition,
        package_definition_version="1",
    ).save()
    return build


@pytest.fixture
def package1_definitions_without_function2(function1):
    function1_def = {
        "name": function1.name,
        "summary": function1.summary,
        "parameters": [],
        "description": "description",
        "display_name": function1.name,
    }

    return [function1_def]


@pytest.mark.django_db
@pytest.mark.usefixtures("function1", "function2", "function3", "function4")
def test_deactivate_removed_functions(
    package1_definitions_without_function2, package1, package2
):
    db_functions = Function.objects.all()
    for function in db_functions:
        assert function.active is True

    package_manager = PackageManager(package1)
    package_manager._deactivate_removed_functions(
        package1_definitions_without_function2
    )

    # package2 functions should still all be active
    assert package2.functions.count() == package2.active_functions.count()

    # package1 function1 should be active, function2 inactive
    assert package1.functions.get(name="function1").active is True
    assert package1.functions.get(name="function2").active is False


@pytest.mark.django_db
def test_delete_removed_function_parameters(function1):
    assert function1.parameters.count() == 2

    parameters_to_keep = function1.parameters.get(name="param1")

    package_manager = PackageManager(function1.package)
    package_manager._delete_removed_function_parameters([parameters_to_keep])

    assert function1.parameters.count() == 1
    assert function1.parameters.filter(name="param1").exists()


@pytest.mark.django_db
def test_unavailable_docker_socket(mocker):
    def mock_unavailabe_docker_socket():
        raise DockerSocketConnectionError("")

    mocker.patch("builder.utils._get_docker_client", mock_unavailabe_docker_socket)

    with pytest.raises(DockerSocketConnectionError):
        _ = utils._get_docker_client()


@pytest.mark.django_db
def test_prepare_image_build(mocker, build):
    def mock_docker_socket():
        return ""

    def mock_prepare_image_build(_dockerfile, _package_contents, _workdir):
        raise BuilderError("Failed")

    mocker.patch("builder.utils._get_docker_client", mock_docker_socket)
    mocker.patch("builder.utils._prepare_image_build", mock_prepare_image_build)

    utils.build_package(build.id)

    updated_build = Build.objects.get(id=build.id)
    updated_build_log = BuildLog.objects.get(build=updated_build)

    assert updated_build.status == Build.ERROR
    assert updated_build_log.log.split("\n")[-1] == "Failed"


@pytest.mark.django_db
def test_build_image(mocker, build):
    def mock_docker_socket():
        return ""

    def mock_prepare_image_build(_dockerfile, _package_contents, _workdir):
        return

    def mock_build_image(_docker_client, _image_name, _workdir):
        raise BuilderError("Failed")

    mocker.patch("builder.utils._get_docker_client", mock_docker_socket)
    mocker.patch("builder.utils._prepare_image_build", mock_prepare_image_build)
    mocker.patch("builder.utils._docker_build_image", mock_build_image)

    utils.build_package(build.id)

    updated_build = Build.objects.get(id=build.id)
    updated_build_log = BuildLog.objects.get(build=updated_build)

    assert updated_build.status == Build.ERROR
    assert updated_build_log.log.split("\n")[-1] == "Failed"


def test_invalid_package_yaml(mocker, package_contents):
    class TarFile:
        def close():
            return

    def mock_tarfile(_bytes):
        return TarFile

    def mock_missing_package_yaml(_package_yaml):
        raise KeyError("missing package yaml")

    def mock_invalid_package_yaml(_package_yaml):
        raise YAMLError

    def mock_invalid_package(_package_yaml):
        raise utils.InvalidPackage

    mocker.patch("builder.utils._get_tarfile", mock_tarfile)
    mocker.patch("builder.utils._extract_package_definition", mock_missing_package_yaml)

    with pytest.raises(utils.InvalidPackage):
        utils.extract_package_definition(package_contents)

    mocker.patch("builder.utils._extract_package_definition", mock_invalid_package_yaml)

    with pytest.raises(utils.InvalidPackage):
        utils.extract_package_definition(package_contents)

    mocker.patch("builder.utils._extract_package_definition", mock_invalid_package)

    with pytest.raises(utils.InvalidPackage):
        utils.extract_package_definition(package_contents)
