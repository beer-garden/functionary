from drf_spectacular.utils import OpenApiParameter

HEADER_PARAMETERS = [
    OpenApiParameter(
        name="X-Team-Id",
        type=str,
        location=OpenApiParameter.HEADER,
        description=(
            "ID for the Team to which this request corresponds. If set, the "
            "default environment for the team will be used. This is ignored if "
            "X-Environment-Id is set."
        ),
    ),
    OpenApiParameter(
        name="X-Environment-Id",
        type=str,
        location=OpenApiParameter.HEADER,
        description=("ID for the Environment to which this request corresponds"),
    ),
]
