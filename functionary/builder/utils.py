import io
import json
import logging
import os
import shutil
from tarfile import ReadError, TarFile
from tarfile import open as open_tarfile
from typing import TYPE_CHECKING

import docker
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db import transaction
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from docker.errors import APIError, BuildError, DockerException
from yaml import YAMLError, safe_load

from core.models import Function, FunctionParameter, Package
from core.utils.messaging import get_route, send_message
from core.utils.registry import get_registry, get_registry_config

from .celery import app
from .exceptions import InvalidPackage
from .models import Build, BuildLog, BuildResource

if TYPE_CHECKING:
    from typing import OrderedDict, Union
    from uuid import UUID

    from docker import DockerClient
    from docker.models.images import Image

    from core.models import Environment, User


logger = get_task_logger(__name__)
logger.setLevel(getattr(logging, settings.LOG_LEVEL))


class DockerClientError(Exception):
    pass


class BuilderError(Exception):
    pass


class PackageManager:
    def __init__(self, package: Package) -> None:
        self.package = package
        self.environment = package.environment

    def update_package(self, package_definition: dict) -> None:
        """Update the package instance based on the supplied definition

        Args:
            package_definition: The pre-validated package definition from a package.yaml

        Returns:
            None
        """
        editable_fields = ["display_name", "summary", "description", "language"]

        for field in editable_fields:
            new_value = package_definition.get(field)
            setattr(self.package, field, new_value)

        self.package.save()

    def update_functions(self, function_definitions: list[dict]) -> None:
        """Update the functions associated with the package

        Use the given list of function definitions to update all functions
        belonging to this package.

        Args:
            function_definitions: A list of function definitions

        Returns:
            None
        """
        functions, function_parameters = self._create_functions_from_definition(
            function_definitions
        )

        with transaction.atomic():
            self._save_functions(functions, function_parameters)
            self._delete_removed_functions(function_definitions, function_parameters)

    def _create_functions_from_definition(
        self, definitions: list[dict]
    ) -> tuple[list[Function], list[FunctionParameter]]:
        """Creates the functions in the package from the definition file"""
        functions = []
        function_parameters = []

        for function_def in definitions:
            name = function_def.get("name")
            try:
                function_obj = Function.objects.get(package=self.package, name=name)
            except Function.DoesNotExist:
                function_obj = Function(
                    package=self.package, name=name, environment=self.environment
                )

            function_obj.display_name = function_def.get("display_name")
            function_obj.summary = function_def.get("summary")
            function_obj.return_type = function_def.get("return_type")
            function_obj.description = function_def.get("description")
            function_obj.variables = function_def.get("variables", [])
            function_obj.active = True

            functions.append(function_obj)
            function_parameters.extend(
                self._create_parameters_from_definition(function_def, function_obj)
            )

        return functions, function_parameters

    def _create_parameters_from_definition(
        self, function_definition: dict, function: Function
    ) -> list[FunctionParameter]:
        """Creates the FunctionParameter objects for the provided function based on the
        function_definition"""
        parameters = []
        parameter_defs: list[dict] = function_definition.get("parameters", [{}])

        for parameter in parameter_defs:
            try:
                function_parameter = FunctionParameter.objects.get(
                    function=function, name=parameter.get("name")
                )
            except FunctionParameter.DoesNotExist:
                function_parameter = FunctionParameter(
                    function=function, name=parameter.get("name")
                )

            function_parameter.description = parameter.get("description")
            function_parameter.parameter_type = parameter.get("type")
            function_parameter.default = parameter.get("default")
            function_parameter.required = parameter.get("required")
            function_parameter.options = parameter.get("options")

            parameters.append(function_parameter)

        return parameters

    def _delete_removed_functions(
        self,
        function_definitions: list[dict],
        function_parameters: list[FunctionParameter],
    ) -> None:
        """Delete any functions that have been removed from the package definition"""
        self._delete_removed_function_parameters(function_parameters)
        self._deactivate_removed_functions(function_definitions)

    def _save_functions(
        self, functions: list[Function], function_parameters: list[FunctionParameter]
    ):
        """Save all functions and associated function parameters"""
        # TODO: Try to optimize the saving of these objects to improve performance
        for func in functions:
            func.save()

        for parameter in function_parameters:
            parameter.save()

    def _deactivate_removed_functions(self, definitions: list[dict]):
        """Deactivate and package functions not present in the definitions"""
        function_names = []

        for function_def in definitions:
            function_names.append(function_def.get("name"))

        removed_functions = Function.objects.filter(package=self.package).exclude(
            name__in=function_names
        )

        for function in removed_functions:
            function.deactivate()

    def _delete_removed_function_parameters(
        self,
        function_parameters: list[FunctionParameter],
    ) -> None:
        """Deletes any FunctionParameters that are not in the provided
        function_parameters for the package
        """
        ids_to_keep = [parameter.id for parameter in function_parameters]

        FunctionParameter.objects.filter(function__package=self.package).exclude(
            id__in=ids_to_keep
        ).delete()


def extract_package_definition(package_contents: bytes) -> dict:
    """Extracts the package.yaml from a package tarball

    Args:
        package_contents: gzipped tarball of a package

    Returns:
        The package definition yaml loaded as a dict

    Raises:
        InvalidPackage: Raised whenever an error is encountered while extracting
            package contents from the package.yaml in the tarball
    """
    package_contents_io = io.BytesIO(package_contents)
    tarfile = None

    try:
        tarfile = _get_tarfile(package_contents_io)
        package_definition = _extract_package_definition(tarfile)
        return package_definition
    except ReadError:
        raise InvalidPackage(
            "Could not untar package file. Make sure it is a valid gzipped tarball."
        )
    except KeyError:
        raise InvalidPackage("package.yaml not found")
    except (InvalidPackage, YAMLError):
        raise InvalidPackage("package.yaml is invalid YAML")
    except Exception as err:
        logger.error(f"Failed extracting package definition: {err}")
        raise InvalidPackage("failed to extract package definition")
    finally:
        if tarfile:
            tarfile.close()
        package_contents_io.close()


def _get_tarfile(package_contents: io.BytesIO) -> TarFile:
    """Extract tarfile from given bytes"""
    return open_tarfile(fileobj=package_contents, mode="r")


def _extract_package_definition(tarfile: TarFile) -> dict:
    """Extract the package definition from given tarfile

    Args:
        tarfile: The opened tarfile in read mode

    Returns:
        package_contents: A dictionary representation of the package yaml

    Raises:
        InvalidPackage: Raised when the package.yaml is not a regular file
        KeyError: Raised when package.yaml is not found in the tarfile
        YAMLError: Raised when the YAML parser encounters an error condition
    """
    package_yaml = tarfile.extractfile("package.yaml")
    if not package_yaml:
        raise InvalidPackage("package.yaml found, but it is not a regular file.")

    return safe_load(package_yaml.read())


def initiate_build(
    creator: "User",
    environment: "Environment",
    package_contents: bytes,
    package_definition: dict,
    package_definition_version: str,
) -> Build:
    """Creates the Build and BuildResource instances necessary to initiate a build and
    then creates the task for the worker that will perform the build.

    Args:
        creator: The User initiating the build
        environment: The environment that the package should be published under
        package_contents: A gzipped file containing the package to be built
        package_definition: dict containing the package definition
    """
    with transaction.atomic():
        package_obj = None

        try:
            package_obj = Package.objects.get(
                environment=environment, name=package_definition.get("name")
            )
        except Package.DoesNotExist:
            package_obj = create_package_from_definition(
                package_definition, environment
            )

        build = Build.objects.create(
            creator=creator, environment=environment, package=package_obj
        )

        BuildResource(
            build=build,
            package_contents=package_contents,
            package_definition=package_definition,
            package_definition_version=package_definition_version,
        ).save()

    build_package.delay(build_id=build.id)

    return build


def create_package_from_definition(
    package_definition: dict, environment: "Environment"
) -> Package:
    """Create a package from a package definition"""
    # TODO: Manually parsing for now, but this should be codified somewhere, with
    #       the parsing informed by package_definition_version.
    package_obj = Package(
        environment=environment,
        name=package_definition.get("name"),
    )

    package_obj.display_name = package_definition.get("display_name")
    package_obj.summary = package_definition.get("summary")
    package_obj.description = package_definition.get("description")
    package_obj.language = package_definition.get("language")

    package_obj.save()

    return package_obj


@app.task
def build_package(build_id: "UUID") -> None:
    """Retrieve the resources for Build and use them to build and push the package
    docker image. Also creates BuildLog with build/push information.

    Args:
        build_id: ID of the build being executed

    Returns:
        None
    """
    build = Build.objects.select_related("environment").get(id=build_id)
    build_resource = BuildResource.objects.get(build=build)
    log_msgs: list[str] = []

    logger.info(f"Starting build {build.id}")

    try:
        _build_package(build, build_resource, log_msgs)
        build.complete()
        _publish_pull_image_msg(build.package)
    except Exception as err:
        logger.error(f"Build {build.id} encountered error: {err}")
        log_msgs.append(str(err))
        build.error()
    finally:
        log = "\n".join(log_msgs)
        _create_build_log(build, log)


def _build_package(build: Build, build_resource: BuildResource, log: list[str]) -> None:
    """Generate and build necessary resources to complete package image build

    Args:
        build: The build object containing metadata about the build
        build_resource: The build resource object associated with the given build
        log: A list of strings that will be mutated. Logs will be appended to this list
            to keep track of the build process and any errors that occur.

    Returns:
        None

    Raises:
        DockerSockerConnectionError: Raised when connection to the docker socket
            could not be established.
        BuilderError: Raised during various build process errors
    """
    docker_client = _get_docker_client()
    build.in_progress()

    # Set variables necessary for build process
    workdir = _generate_path_for_build(build)
    package = build.package
    image_name, dockerfile = build_resource.image_details
    full_image_name = f"{get_registry()}/{image_name}"
    package_contents = build_resource.package_contents
    package_definition: OrderedDict = build_resource.package_definition
    function_definitions: list[dict] = package_definition.get("functions")

    _prepare_image_build(dockerfile, package_contents, workdir)
    log.append("Unpacked package contents and loaded appropriate Dockerfile template.")

    image, build_results = _build_image(docker_client, full_image_name, workdir)
    log.append(str(build_results))

    push_results = _push_image(docker_client, full_image_name)
    log.append(str(push_results))

    package.update_image_name(image_name)
    package_manager = PackageManager(package)
    package_manager.update_package(package_definition)
    package_manager.update_functions(function_definitions)
    _cleanup(docker_client, image, workdir, build)

    logger.info(f"Build {build.id} COMPLETE")


def _format_build_results(build_results):
    """
    Helper function for build_package to format build results
    as a more readable string

    Args:
        build_results: iterator returned from docker build
    Returns:
        string representation of build log

    """
    log = ""

    for line in build_results:
        line_str = ""

        for value in line.values():
            line_str += str(value)

        log += line_str

    return log


def _format_push_results(push_results):
    """
    Helper function for build_package to format push results
    as a more readable string

    Args:
        push_results: generator object created from docker push
    Returns:
        string representation of the push log
    """
    log = ""

    for line in push_results:
        dict_line = json.loads(line.decode("utf-8"))
        if status := dict_line.get("status"):
            if id := dict_line.get("id"):
                line_str = f"{id}: {status}"
            else:
                line_str = status

            log += line_str + "\n"

    return log


def _extract_package_contents(package_contents: bytes, workdir: str) -> None:
    """Extracts the contents of the package tarball

    Args:
        package_contents: The package file bytes
        workdir: The directory to export the package contents to

    Returns:
        None

    Raises:
        BuilderError: Raised when reading the tarfile resulted in an exception
    """
    package_contents_io = io.BytesIO(package_contents)
    tarball = None

    try:
        tarball = open_tarfile(fileobj=package_contents_io, mode="r")
        tarball.extractall(workdir)
    except ReadError as err:
        err_msg = f"Failed to read tarfile: {err}"
        logger.error(err_msg)
        raise BuilderError(err_msg)
    except Exception as err:
        err_msg = f"Failed extracting package contents: {err}"
        logger.error(err_msg)
        raise BuilderError(err_msg)
    finally:
        if tarball:
            tarball.close()
        package_contents_io.close()


def _load_dockerfile_template(dockerfile_template: str, workdir: str) -> None:
    """Render the dockfile template and write it to the working directory

    Args:
        dockerfile_template: The dockerfile template to load and render
        worder: The work directory path to render the dockerfile into

    Returns:
        None

    Raises:
        BuilderError: Raised when template dockerfile template does not exist
    """
    try:
        template = get_template(dockerfile_template)
    except TemplateDoesNotExist:
        err_msg = "Template does not exist."
        logger.error(err_msg)
        raise BuilderError(err_msg)

    context = {"registry": get_registry()}

    with open(f"{workdir}/Dockerfile", "w") as dockerfile:
        dockerfile.write(template.render(context=context))


def _prepare_image_build(
    dockerfile: str, package_contents: bytes, workdir: str
) -> None:
    """Generates artifacts necessary for building the new image

    Args:
        dockerfile: The dockerfile string containing the image details
        package_contents: The bytes that makeup the package contents
        workdir: The directory to dump the artifacts into

    Raises:
        BuilderError: Raised when package content extraction or dockerfile
            template loading fails
    """
    _extract_package_contents(package_contents, workdir)
    _load_dockerfile_template(dockerfile, workdir)


def _build_image(
    docker_client: "DockerClient", full_image_name: str, workdir: str
) -> tuple["Image", str]:
    """Build a new image with the given image name

    Args:
        docker_client: The DockerClient used to interface with the Docker socket
        full_image_name: The image name, including the tag
        workdir: The directory that contains the artifacts necessary to build
            the image

    Returns:
        image: Returns the generated Image object upon successful
            build. Otherwise, value will be None
        formatted_build_results: The formatted log of the build steps

    Raises:
        BuilderError: Raised when image build fails
    """
    try:
        image, build_result = _docker_build_image(
            docker_client, full_image_name, workdir
        )
        formatted_build_results = _format_build_results(build_result)
        return image, formatted_build_results
    except (APIError, BuildError) as exc:
        formatted_build_results = (
            _format_build_results(exc.build_log)
            if hasattr(exc, "build_log")
            else str(exc)
        )
        raise BuilderError(f"Error building image: {formatted_build_results}")


def _docker_build_image(
    docker_client: "DockerClient", full_image_name: str, workdir: str
) -> tuple["Union[Image, None]", str]:
    """Use given docker client to build image and return results"""
    return docker_client.images.build(
        path=workdir, pull=True, forcerm=True, tag=full_image_name
    )


def _push_image(docker_client: "DockerClient", full_image_name: str) -> str:
    """Push given image name

    Args:
        docker_client: The DockerClient to interface with the Docker socket.
        full_image_name: The string of the full image name, which includes the
            registry to push to and image tag.

    Returns:
        push_results: The formatted string of the push results. None if failed push

    Raises:
        BuilderError: Raised when error pushing image
    """
    try:
        push_result = docker_client.images.push(full_image_name, stream=True)
        return _format_push_results(push_result)
    except APIError as exc:
        err_msg = f"Failed to push image: {full_image_name}. Error: {exc}"
        logger.error(err_msg)
        raise BuilderError(err_msg)


def _create_build_log(build: Build, log: str) -> None:
    """Wrapper method to create BuildLog for given build"""
    BuildLog.objects.create(build=build, log=log)


def _cleanup(
    docker_client: "DockerClient", image: "Image", workdir: str, build: Build
) -> None:
    """Cleanup artifacts generated from the build process"""
    logger.debug(f"Cleaning up remnants of build {build.id}")

    try:
        shutil.rmtree(workdir)
        docker_client.images.remove(image.id, force=True)
    except DockerException:
        logger.warn(f"Unable to remove build image: {image.id}")
    except Exception as err:
        err_msg = f"Unable to delete build directory. Error: {err}"
        logger.error(err_msg)
        raise BuilderError(err_msg)


def _get_docker_client() -> "DockerClient":
    """Creates a new docker client

    Args:
        None

    Returns:
        docker_client: A new docker client

    Raises:
        DockerClientError: Raised when a connection to the Docker socket
        could not be created.
    """
    config = get_registry_config()
    username = config.REGISTRY_USER
    password = config.REGISTRY_PASSWORD
    registry = get_registry(config, with_namespace=False)

    try:
        client = docker.from_env()
    except DockerException as err:
        logger.critical("Failed to connect to the Docker socket. Unable to build.")
        raise DockerClientError(err)

    if username and password:
        try:
            client.login(username=username, password=password, registry=registry)
        except APIError as err:
            logger.critical("Docker login failed. Check REGISTRY_* settings.")
            raise DockerClientError(err)

    return client


def _generate_path_for_build(build: Build) -> str:
    """Generate the path for the given build"""
    workdir = f"{settings.BUILDER_WORKDIR_BASE}/{build.id}"

    try:
        os.makedirs(workdir)
        return workdir
    except OSError as err:
        logger.error(f"Error creating directory for build {build.id}. Error: {err}")
        raise BuilderError(f"Failed to generate directory: {err.filename}")


def _publish_pull_image_msg(package: Package):
    """Sends a message to all runners to pull the new image."""
    exchange, routing_key = get_route(package)
    send_message(
        exchange,
        routing_key,
        "PULL_IMAGE",
        {"id": str(package.id), "image_name": package.full_image_name},
    )
