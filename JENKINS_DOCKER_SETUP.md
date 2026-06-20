# Jenkins CD Setup with Docker

This guide walks through setting up a local Jenkins CD pipeline that builds a Windows `.exe` from this project using Docker and PyInstaller.

**Architecture:** Jenkins controller runs in a Linux Docker container on your Windows PC. Your Windows host is attached as a build agent (label `windows`) so PyInstaller can produce a native `.exe` and the Windows-dependent tests can run.

---

## 1. Prerequisites on the Windows Host

| Tool | Why | Install |
|------|-----|---------|
| Docker Desktop | Runs the Jenkins controller container | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) |
| Python 3.12 | Runs tests and PyInstaller build | [python.org/downloads](https://www.python.org/downloads/) |
| Git | Jenkins checks out the repo | [git-scm.com/downloads](https://git-scm.com/downloads) |
| Java 17+ (JDK or JRE) | Runs the Jenkins agent `.jar` on Windows | [adoptium.net](https://adoptium.net/) |

Verify all four are on your PATH:

```powershell
docker --version
python --version
git --version
java -version
```

---

## 2. Start the Jenkins Controller

From the project root (where `docker-compose.yml` lives):

```powershell
docker compose up -d
```

Verify it's running:

```powershell
docker ps
```

You should see a container named `jenkins` with ports `8080` and `50000` mapped.

---

## 3. First-Time Jenkins Setup

### Retrieve the initial admin password

```powershell
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

### Complete the setup wizard

1. Open **http://localhost:8080** in your browser.
2. Paste the admin password from the command above.
3. Click **Install suggested plugins** — this installs Pipeline, Git, and other essentials.
4. Create your admin user when prompted.

---

## 4. Add the Windows Build Agent

The Jenkins controller runs on Linux (in Docker), but the build must run on your Windows host. You need to register your Windows machine as a Jenkins agent.

### Create the agent node

1. Go to **Manage Jenkins → Nodes → New Node**.
2. Node name: `windows`
3. Type: **Permanent Agent**
4. Click **Create**, then configure:
   - **# of executors:** `1`
   - **Remote root directory:** `C:\jenkins-agent` (create this folder)
   - **Labels:** `windows`
   - **Usage:** "Only build jobs with label expressions matching this node"
   - **Launch method:** "Launch agent by connecting it to the controller"
5. Click **Save**.

### Connect the agent

1. Click on the `windows` node in the Nodes list.
2. You'll see connection instructions with a command like:

   ```powershell
   java -jar agent.jar -url http://localhost:8080/ -secret <SECRET> -name windows -workDir "C:\jenkins-agent"
   ```

3. Download `agent.jar` from the link shown on that page.
4. Run the command in a PowerShell or CMD window on your Windows host.
5. Keep this terminal open — it's the agent process. The node status should change to **Connected** in the Jenkins UI.

> **Tip:** To run the agent as a background service, you can use Windows Task Scheduler or install it as a Windows service. For learning purposes, running it in a terminal is fine.

---

## 5. Create the Pipeline Job

1. From the Jenkins dashboard, click **New Item**.
2. Enter a name (e.g., `Apps-Analyst-CD`), select **Pipeline**, and click **OK**.
3. Under **Pipeline**, set:
   - **Definition:** Pipeline script from SCM
   - **SCM:** Git
   - **Repository URL:** `https://github.com/moshearz/Apps-Analyst-Extended.git` (or a local path)
   - **Branch Specifier:** `*/main`
   - **Script Path:** `Jenkinsfile`
4. Click **Save**.

---

## 6. Triggering Builds

### Why webhooks won't work

GitHub webhooks need to send HTTP requests to your Jenkins server. Since Jenkins runs on `localhost`, GitHub has no way to reach it from the internet. Webhook delivery will fail with a connection error.

### Your options

- **Manual:** Click **Build Now** on the job page whenever you want a build.
- **SCM Polling:** Under job configuration → Build Triggers → **Poll SCM**, set a schedule like `H/5 * * * *` (checks for new commits every 5 minutes). Jenkins pulls the repo and only builds if something changed.

---

## 7. Download the .exe Artifact

After a successful build:

1. Go to the job page (e.g., `Apps-Analyst-CD`).
2. Click on the latest build number (e.g., `#1`).
3. Click **Build Artifacts**.
4. Download `dist/Apps-Analyst.exe`.

This is the standalone Windows executable — no Python installation required to run it.

---

## Useful Docker Commands

```powershell
docker compose up -d       # Start Jenkins (detached)
docker compose down        # Stop Jenkins (data persists in the volume)
docker compose logs -f     # Stream Jenkins logs
docker exec -it jenkins bash   # Shell into the Jenkins container
docker volume ls           # List volumes (jenkins_home should be there)
```

---

## Pipeline Stages

The `Jenkinsfile` defines these stages, all running on the `windows` agent:

| Stage | What it does |
|-------|-------------|
| **Checkout** | Clones the repo |
| **Setup** | Creates a Python venv and installs dependencies + PyInstaller |
| **Test** | Runs the 21 safe unit tests (same marker filter as GitHub Actions CI) |
| **Build** | Runs `pyinstaller --onefile --name Apps-Analyst main.py` |

On success, `dist/Apps-Analyst.exe` is archived as a build artifact. The workspace is cleaned after every build.
