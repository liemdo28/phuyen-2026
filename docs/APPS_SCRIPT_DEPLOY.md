# Apps Script Auto-Redeploy Setup

To let GitHub Actions update the live Apps Script Web App automatically after every push to `main`, configure this secret:

- `APPS_SCRIPT_DEPLOYMENT_ID`

## How to get the deployment ID

1. Open the Apps Script project.
2. Go to `Deploy` -> `Manage deployments`.
3. Open the active Web App deployment.
4. Copy the deployment ID.
   It is not the `/exec` URL. It is the deployment identifier used by Apps Script deployments.
5. Add it in GitHub:
   `Repo -> Settings -> Secrets and variables -> Actions -> New repository secret`

## Required secrets

- `CLASP_CREDENTIALS`
- `APPS_SCRIPT_DEPLOYMENT_ID`

## Result

After this is configured, every push to `main` will:

1. `clasp push --force`
2. create a new Apps Script version
3. redeploy the existing Web App deployment to that new version

This keeps the same Web App URL while moving it to the newest code.
