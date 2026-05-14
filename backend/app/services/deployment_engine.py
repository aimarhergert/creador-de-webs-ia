import re
import logging
from pathlib import Path
import httpx
import base64
from app.config import settings

logger = logging.getLogger(__name__)

_LOCAL_SITES_DIR = Path("/app/static/sites")


def _sanitize_repo_name(keyword: str) -> str:
    name = keyword.lower().strip()
    name = re.sub(r"[^a-z0-9-]", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return f"aros-{name[:40]}"


async def deploy_local(keyword: str, files: dict[str, str]) -> dict:
    """Write files to local static directory and return a localhost URL."""
    repo_name = _sanitize_repo_name(keyword)
    site_dir = _LOCAL_SITES_DIR / repo_name

    site_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in files.items():
        (site_dir / filename).write_text(content, encoding="utf-8")

    public_url = f"http://localhost:8000/static/sites/{repo_name}/"
    logger.info(f"[Deploy] Sitio publicado localmente: {public_url}")
    return {"url": public_url, "repo_name": repo_name, "platform": "local"}


async def deploy_to_github_pages(keyword: str, files: dict[str, str]) -> dict:
    """Push files to GitHub + enable Pages. Returns public URL."""
    repo_name = _sanitize_repo_name(keyword)
    owner = settings.GITHUB_USERNAME
    headers = {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with httpx.AsyncClient(headers=headers, timeout=30) as client:
        # 1. Create repo (ignore 422 if already exists)
        logger.info(f"[Deploy] Creando repo GitHub: {owner}/{repo_name}")
        create_resp = await client.post(
            "https://api.github.com/user/repos",
            json={"name": repo_name, "private": False, "auto_init": False},
        )
        if create_resp.status_code not in (201, 422):
            create_resp.raise_for_status()

        # 2. Get default branch SHA (for updates)
        ref_resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo_name}/git/ref/heads/main"
        )
        base_sha = ref_resp.json().get("object", {}).get("sha") if ref_resp.status_code == 200 else None

        # 3. Upload each file via Contents API
        for filename, content in files.items():
            encoded = base64.b64encode(content.encode()).decode()
            payload = {"message": f"Auto-generated: {filename}", "content": encoded}

            # Get current file SHA if it exists (for update)
            existing = await client.get(
                f"https://api.github.com/repos/{owner}/{repo_name}/contents/{filename}"
            )
            if existing.status_code == 200:
                payload["sha"] = existing.json()["sha"]

            put_resp = await client.put(
                f"https://api.github.com/repos/{owner}/{repo_name}/contents/{filename}",
                json=payload,
            )
            put_resp.raise_for_status()
            logger.info(f"[Deploy] Subido: {filename}")

        # 4. Enable GitHub Pages on main branch
        pages_resp = await client.post(
            f"https://api.github.com/repos/{owner}/{repo_name}/pages",
            json={"source": {"branch": "main", "path": "/"}},
        )
        if pages_resp.status_code not in (201, 409):
            logger.warning(f"[Deploy] Pages ya activo o error no crítico: {pages_resp.status_code}")

    public_url = f"https://{owner}.github.io/{repo_name}/"
    logger.info(f"[Deploy] Sitio publicado: {public_url}")
    return {"url": public_url, "repo_name": repo_name, "platform": "github_pages"}


async def deploy_to_vercel(keyword: str, files: dict[str, str]) -> dict:
    """Deploy to Vercel via API. Returns deployment URL."""
    repo_name = _sanitize_repo_name(keyword)
    headers = {"Authorization": f"Bearer {settings.VERCEL_TOKEN}"}

    vercel_files = [
        {"file": name, "data": content}
        for name, content in files.items()
    ]

    async with httpx.AsyncClient(headers=headers, timeout=60) as client:
        resp = await client.post(
            "https://api.vercel.com/v13/deployments",
            json={
                "name": repo_name,
                "files": vercel_files,
                "projectSettings": {"framework": None},
            },
        )
        resp.raise_for_status()
        data = resp.json()

    deploy_url = f"https://{data.get('url', '')}"
    deploy_id = data.get("id", "")
    logger.info(f"[Deploy] Vercel deploy iniciado: {deploy_url}")
    return {"url": deploy_url, "deploy_id": deploy_id, "platform": "vercel"}


async def deploy_asset(keyword: str, files: dict[str, str]) -> dict:
    """Auto-selects deployment platform based on available credentials."""
    if settings.VERCEL_TOKEN and settings.VERCEL_TOKEN != "xxxxxxxxxxxxxxxxxx":
        return await deploy_to_vercel(keyword, files)
    elif (
        settings.GITHUB_TOKEN
        and settings.GITHUB_USERNAME
        and settings.GITHUB_TOKEN != "ghp_xxxxxxxxxxxxxxxxxx"
    ):
        return await deploy_to_github_pages(keyword, files)
    else:
        logger.info("[Deploy] No external credentials — using local static deployment")
        return await deploy_local(keyword, files)
