from mcp.server.fastmcp import FastMCP
from typing import Optional, Dict, Any, List
import os
import requests

mcp = FastMCP("Codemagic MCP", dependencies=["requests"])

# Global variables
BASE_URL = "https://api.codemagic.io"

def get_headers():
    """Get headers for Codemagic API requests with API token from environment"""
    api_token = os.environ.get("CODEMAGIC_API_KEY")
    return {
        "Content-Type": "application/json",
        "x-auth-token": api_token
    }

@mcp.tool()
def get_all_applications() -> Dict[str, List[Dict[str, Any]]]:
    """
    Retrieve all applications from Codemagic.
        
    Returns:
        Dictionary containing the applications
    """
    response = requests.get(f"{BASE_URL}/apps", headers=get_headers())
    response.raise_for_status()
    return response.json()

@mcp.tool()
def get_application(app_id: str) -> Dict[str, Dict[str, Any]]:
    """
    Retrieve a specific application from Codemagic by ID.
    
    Args:
        app_id: Application ID
        
    Returns:
        Dictionary containing the application details
    """
    response = requests.get(f"{BASE_URL}/apps/{app_id}", headers=get_headers())
    response.raise_for_status()
    return response.json()

@mcp.tool()
def add_application(repository_url: str, team_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Add a new application to Codemagic.
    
    Args:
        repository_url: SSH or HTTPS URL for cloning the repository
        team_id: Optional team ID to add the app directly to a team (must be admin)
        
    Returns:
        Dictionary containing the created application details
    """
    data = {"repositoryUrl": repository_url}
    if team_id:
        data["teamId"] = team_id
        
    response = requests.post(f"{BASE_URL}/apps", headers=get_headers(), json=data)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def add_application_private(
    repository_url: str,
    ssh_key_data: str,
    ssh_key_passphrase: Optional[str] = None,
    project_type: Optional[str] = None,
    team_id: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Add a new application from a private repository to Codemagic.
    
    Args:
        repository_url: SSH or HTTPS URL for cloning the repository
        ssh_key_data: base64-encoded private key file
        ssh_key_passphrase: SSH key passphrase or None if the SSH key is without a passphrase
        project_type: Set to "flutter-app" when adding Flutter application
        team_id: Optional team ID to add the app directly to a team (must be admin)
        
    Returns:
        Dictionary containing the created application details
    """
    data = {
        "repositoryUrl": repository_url,
        "sshKey": {
            "data": ssh_key_data,
            "passphrase": ssh_key_passphrase
        }
    }
    
    if project_type:
        data["projectType"] = project_type
        
    if team_id:
        data["teamId"] = team_id
        
    response = requests.post(f"{BASE_URL}/apps/new", headers=get_headers(), json=data)
    response.raise_for_status()
    return response.json()

# Artifacts API

@mcp.tool()
def get_artifact(secure_filename: str) -> bytes:
    """
    Get authenticated download URL for a build artifact.
    
    Args:
        secure_filename: The secure filename of the artifact (from Builds API or Codemagic UI)
                         Format: uuid1/uuid2/filename.ext
    
    Returns:
        The artifact file content as bytes
    """
    response = requests.get(f"{BASE_URL}/artifacts/{secure_filename}", headers=get_headers())
    response.raise_for_status()
    return response.content

@mcp.tool()
def create_public_artifact_url(secure_filename: str, expires_at: int) -> Dict[str, Any]:
    """
    Create a public download URL for a build artifact.
    
    Args:
        secure_filename: The secure filename of the artifact (from Builds API or Codemagic UI)
                         Format: uuid1/uuid2/filename.ext
        expires_at: URL expiration UNIX timestamp in seconds
        
    Returns:
        Dictionary containing the public artifact URL and expiration timestamp
    """
    data = {"expiresAt": expires_at}
    
    response = requests.post(
        f"{BASE_URL}/artifacts/{secure_filename}/public-url", 
        headers=get_headers(), 
        json=data
    )
    response.raise_for_status()
    return response.json()

# Builds API

@mcp.tool()
def start_build(
    app_id: str,
    workflow_id: str,
    branch: Optional[str] = None,
    tag: Optional[str] = None,
    environment: Optional[Dict[str, Any]] = None,
    labels: Optional[List[str]] = None,
    instance_type: Optional[str] = None
) -> Dict[str, str]:
    """
    Start a new build on Codemagic.
    
    Args:
        app_id: The application identifier
        workflow_id: The workflow identifier
        branch: The branch name (either branch or tag is required)
        tag: The tag name (either branch or tag is required)
        environment: Dictionary with environment variables, variable groups, and software versions
        labels: List of labels to include for the build
        instance_type: Type of instance to use for the build (e.g. 'mac_mini_m2')
        
    Returns:
        Dictionary with the build ID
    """
    if not branch and not tag:
        raise ValueError("Either branch or tag must be provided")
    
    data = {
        "appId": app_id,
        "workflowId": workflow_id
    }
    
    if branch:
        data["branch"] = branch
    if tag:
        data["tag"] = tag
    if environment:
        data["environment"] = environment
    if labels:
        data["labels"] = labels
    if instance_type:
        data["instanceType"] = instance_type
    
    response = requests.post(f"{BASE_URL}/builds", headers=get_headers(), json=data)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def get_builds(
    app_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    branch: Optional[str] = None,
    tag: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get a list of builds from Codemagic build history.
    
    Args:
        app_id: Optional filter by application identifier
        workflow_id: Optional filter by workflow identifier
        branch: Optional filter by branch name
        tag: Optional filter by tag name
        
    Returns:
        Dictionary containing applications and builds information
    """
    params = {}
    if app_id:
        params["appId"] = app_id
    if workflow_id:
        params["workflowId"] = workflow_id
    if branch:
        params["branch"] = branch
    if tag:
        params["tag"] = tag
    
    response = requests.get(f"{BASE_URL}/builds", headers=get_headers(), params=params)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def get_build_status(build_id: str) -> Dict[str, Any]:
    """
    Get the status of a build on Codemagic.
    
    Args:
        build_id: The build identifier
        
    Returns:
        Dictionary containing the application and build information
    """
    response = requests.get(f"{BASE_URL}/builds/{build_id}", headers=get_headers())
    response.raise_for_status()
    return response.json()

@mcp.tool()
def cancel_build(build_id: str) -> Dict[str, Any]:
    """
    Cancel a running build on Codemagic.
    
    Args:
        build_id: The build identifier
        
    Returns:
        Response from the API (empty if successful)
    """
    response = requests.post(f"{BASE_URL}/builds/{build_id}/cancel", headers=get_headers())
    if response.status_code == 208:  # Already Reported (build already finished)
        return {"message": "Build has already finished"}
    response.raise_for_status()
    return response.json() if response.content else {}

@mcp.tool()
def get_build_step_log(build_id: str, step_id: str) -> str:
    """
    Get the raw log output for a specific build step on Codemagic.

    Calls the undocumented endpoint that the Codemagic web dashboard uses
    internally (GET /builds/{build_id}/step/{step_id}), which returns the
    step's stdout/stderr as text/plain. Use this to diagnose failed builds
    without manual dashboard access.

    The step_id is the `_id` field of any entry in the `buildActions` array
    returned by `get_build_status`, or equivalently the last path segment
    of that step's `logUrl`.

    Args:
        build_id: The build identifier
        step_id: The build step identifier

    Returns:
        The step log as plain text
    """
    response = requests.get(
        f"{BASE_URL}/builds/{build_id}/step/{step_id}",
        headers=get_headers(),
    )
    response.raise_for_status()
    return response.text

# Caches API

@mcp.tool()
def get_app_caches(app_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Retrieve a list of caches for an application.
    
    Args:
        app_id: The application identifier
        
    Returns:
        Dictionary containing the list of caches for the application
    """
    response = requests.get(f"{BASE_URL}/apps/{app_id}/caches", headers=get_headers())
    response.raise_for_status()
    return response.json()

@mcp.tool()
def delete_all_app_caches(app_id: str) -> Dict[str, Any]:
    """
    Delete all stored caches for an application.
    
    Args:
        app_id: The application identifier
        
    Returns:
        Dictionary with the list of cache IDs that will be deleted and a message
    """
    response = requests.delete(f"{BASE_URL}/apps/{app_id}/caches", headers=get_headers())
    # API returns 202 Accepted for successful cache deletion
    if response.status_code == 202:
        return response.json()
    response.raise_for_status()
    return response.json()

@mcp.tool()
def delete_app_cache(app_id: str, cache_id: str) -> Dict[str, Any]:
    """
    Delete a specific cache from an application.
    
    Args:
        app_id: The application identifier
        cache_id: The cache identifier to delete
        
    Returns:
        Dictionary with the deleted cache ID and a message
    """
    response = requests.delete(f"{BASE_URL}/apps/{app_id}/caches/{cache_id}", headers=get_headers())
    # API returns 202 Accepted for successful cache deletion
    if response.status_code == 202:
        return response.json()
    response.raise_for_status()
    return response.json()

# Teams API

@mcp.tool()
def invite_team_member(team_id: str, email: str, role: str) -> Dict[str, Any]:
    """
    Invite a new team member to your team.
    
    Args:
        team_id: The team identifier
        email: User email to invite
        role: User role, can be 'owner' (Admin) or 'developer' (Member)
        
    Returns:
        Full team object
    """
    if role not in ["owner", "developer"]:
        raise ValueError("Role must be either 'owner' or 'developer'")
    
    data = {
        "email": email,
        "role": role
    }
    
    response = requests.post(f"{BASE_URL}/team/{team_id}/invitation", headers=get_headers(), json=data)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def delete_team_member(team_id: str, user_id: str) -> Dict[str, Any]:
    """
    Remove a team member from the team.
    
    Args:
        team_id: The team identifier
        user_id: The user identifier to remove
        
    Returns:
        Response from the API (empty if successful)
    """
    response = requests.delete(f"{BASE_URL}/team/{team_id}/collaborator/{user_id}", headers=get_headers())
    response.raise_for_status()
    return response.json() if response.content else {}
