from mcp.server.fastmcp import FastMCP
import requests
import os


mcp = FastMCP("gitlab")


GITLAB_URL = os.environ.get("GITLAB_URL")
GITLAB_TOKEN = os.environ.get("GITLAB_TOKEN")


def gitlab_request(url):

    headers = {
        "PRIVATE-TOKEN": GITLAB_TOKEN
    }

    response = requests.get(
        url,
        headers=headers
    )

    return response.json()



@mcp.tool()
def gitlab_user():
    """
    Check GitLab authentication
    """

    return gitlab_request(
        f"{GITLAB_URL}/api/v4/user"
    )



@mcp.tool()
def get_project(project_id:str):
    """
    Get GitLab project information
    """

    return gitlab_request(
        f"{GITLAB_URL}/api/v4/projects/{project_id}"
    )



@mcp.tool()
def get_merge_request(project_id:str, mr_iid:str):
    """
    Get GitLab merge request detail
    """

    return gitlab_request(
        f"{GITLAB_URL}/api/v4/projects/{project_id}/merge_requests/{mr_iid}"
    )



@mcp.tool()
def get_merge_request_changes(project_id:str, mr_iid:str):
    """
    Get changed files from merge request
    """

    return gitlab_request(
        f"{GITLAB_URL}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/changes"
    )


if __name__ == "__main__":
    mcp.run()