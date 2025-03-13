from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from agno.api.schemas.workspace import WorkspaceSchema


class WorkspaceSettings(BaseSettings):
    """Workspace settings that can be used by any resource in the workspace."""

    # Workspace name
    ws_name: str
    # Path to the workspace root
    ws_root: Path
    # Workspace git repo url
    ws_repo: Optional[str] = None
    # default env for agno ws commands
    default_env: Optional[str] = "dev"
    # default infra for agno ws commands
    default_infra: Optional[str] = None

    # Image Settings
    # Repository for images
    image_repo: str = "agnohq"
    # 'Name:tag' for the image
    image_name: Optional[str] = None
    # Build images locally
    build_images: bool = False
    # Push images after building
    push_images: bool = False
    # Skip cache when building images
    skip_image_cache: bool = False
    # Force pull images in FROM
    force_pull_images: bool = False

    # Development Settings
    dev_env: str = "dev"
    dev_key: Optional[str] = None

    # Staging Settings
    stg_env: str = "stg"
    stg_key: Optional[str] = None

    # Production Settings
    prd_env: str = "prd"
    prd_key: Optional[str] = None

    # ag cli settings
    # Set to True if Agno should continue creating
    # resources after a resource creation has failed
    continue_on_create_failure: bool = False
    # Set to True if Agno should continue deleting
    # resources after a resource deleting has failed
    # Defaults to True because we normally want to continue deleting
    continue_on_delete_failure: bool = True
    # Set to True if Agno should continue patching
    # resources after a resource patch has failed
    continue_on_patch_failure: bool = False

    # AWS settings
    # Region for AWS resources
    aws_region: Optional[str] = None
    # Profile for AWS resources
    aws_profile: Optional[str] = None
    # AWS Subnet Ids
    aws_subnet_ids: List[str] = Field(default_factory=list)
    # Public subnets. 1 in each AZ.
    aws_public_subnets: List[str] = Field(default_factory=list)
    # Private subnets. 1 in each AZ.
    aws_private_subnets: List[str] = Field(default_factory=list)
    # AWS Availability Zone
    aws_az1: Optional[str] = None
    aws_az2: Optional[str] = None
    aws_az3: Optional[str] = None
    aws_az4: Optional[str] = None
    aws_az5: Optional[str] = None
    # Security Group Ids
    aws_security_group_ids: List[str] = Field(default_factory=list)

    # Other Settings
    # Use cached resource if available, i.e. skip resource creation if the resource already exists
    use_cache: bool = True
    # WorkspaceSchema provided by the api
    ws_schema: Optional[WorkspaceSchema] = None

    model_config = SettingsConfigDict(extra="allow")

    @field_validator("dev_key", mode="before")
    def set_dev_key(cls, dev_key, info: ValidationInfo):
        if dev_key is not None:
            return dev_key

        ws_name = info.data.get("ws_name")
        if ws_name is None:
            raise ValueError("ws_name is None: Please set a valid value")

        dev_env = info.data.get("dev_env")
        if dev_env is None:
            raise ValueError("dev_env is None: Please set a valid value")

        return f"{dev_env}-{ws_name}"

    @field_validator("stg_key", mode="before")
    def set_stg_key(cls, stg_key, info: ValidationInfo):
        if stg_key is not None:
            return stg_key

        ws_name = info.data.get("ws_name")
        if ws_name is None:
            raise ValueError("ws_name is None: Please set a valid value")

        stg_env = info.data.get("stg_env")
        if stg_env is None:
            raise ValueError("stg_env is None: Please set a valid value")

        return f"{stg_env}-{ws_name}"

    @field_validator("prd_key", mode="before")
    def set_prd_key(cls, prd_key, info: ValidationInfo):
        if prd_key is not None:
            return prd_key

        ws_name = info.data.get("ws_name")
        if ws_name is None:
            raise ValueError("ws_name is None: Please set a valid value")

        prd_env = info.data.get("prd_env")
        if prd_env is None:
            raise ValueError("prd_env is None: Please set a valid value")

        return f"{prd_env}-{ws_name}"

    @field_validator("aws_subnet_ids", mode="before")
    def set_subnet_ids(cls, aws_subnet_ids, info: ValidationInfo):
        if aws_subnet_ids is not None:
            return aws_subnet_ids

        aws_public_subnets = info.data.get("aws_public_subnets", [])
        aws_private_subnets = info.data.get("aws_private_subnets", [])

        return aws_public_subnets + aws_private_subnets
