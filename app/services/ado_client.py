"""
Azure DevOps API client for triggering pipelines.
"""
import base64
from typing import Optional

import httpx

from app.config import settings
from app.catalog import ADOPipeline


class ADOClient:
    """Client for interacting with Azure DevOps REST API."""

    def __init__(self):
        self.org_url = settings.ado_org_url.rstrip("/")
        self.pat = settings.ado_pat

    def _get_auth_header(self) -> dict:
        """Create authorization header using PAT."""
        if not self.pat:
            raise ValueError("ADO_PAT not configured")

        # Azure DevOps uses Basic auth with PAT
        # Username can be empty, password is the PAT
        credentials = base64.b64encode(f":{self.pat}".encode()).decode()
        return {"Authorization": f"Basic {credentials}"}

    async def trigger_pipeline(
        self,
        pipeline: ADOPipeline,
        parameters: dict,
    ) -> dict:
        """
        Trigger an Azure DevOps pipeline with the given parameters.

        Args:
            pipeline: The ADO pipeline configuration
            parameters: Template parameters to pass to the pipeline

        Returns:
            dict with build id and url
        """
        url = (
            f"{self.org_url}/{pipeline.project}/_apis/pipelines/"
            f"{pipeline.pipeline_id}/runs?api-version=7.0"
        )

        # Build template parameters - include module_name if using generic pipeline
        template_params = dict(parameters)
        if pipeline.module_name:
            template_params["module_name"] = pipeline.module_name

        payload = {
            "resources": {
                "repositories": {
                    "self": {
                        "refName": f"refs/heads/{pipeline.branch}"
                    }
                }
            },
            "templateParameters": template_params,
        }

        headers = {
            **self._get_auth_header(),
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

        return {
            "id": data.get("id"),
            "url": data.get("_links", {}).get("web", {}).get("href"),
            "state": data.get("state"),
        }

    async def get_build_status(
        self,
        project: str,
        build_id: int,
    ) -> dict:
        """
        Get the status of a pipeline run.

        Args:
            project: ADO project name
            build_id: The build/run ID

        Returns:
            dict with status information
        """
        url = (
            f"{self.org_url}/{project}/_apis/build/builds/"
            f"{build_id}?api-version=7.0"
        )

        headers = self._get_auth_header()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

        return {
            "id": data.get("id"),
            "status": data.get("status"),  # notStarted, inProgress, completed
            "result": data.get("result"),  # succeeded, failed, canceled
            "url": data.get("_links", {}).get("web", {}).get("href"),
            "start_time": data.get("startTime"),
            "finish_time": data.get("finishTime"),
        }


# Global client instance
ado_client = ADOClient()


async def trigger_deployment(
    pipeline: ADOPipeline,
    parameters: dict,
) -> dict:
    """
    Convenience function to trigger a deployment.

    Returns dict with:
        - id: Build ID
        - url: Web URL to view the build
        - state: Initial state
    """
    return await ado_client.trigger_pipeline(pipeline, parameters)


async def check_deployment_status(
    project: str,
    build_id: int,
) -> dict:
    """
    Convenience function to check deployment status.

    Returns dict with:
        - id: Build ID
        - status: Current status (notStarted, inProgress, completed)
        - result: Result if completed (succeeded, failed, canceled)
        - url: Web URL to view the build
    """
    return await ado_client.get_build_status(project, build_id)
