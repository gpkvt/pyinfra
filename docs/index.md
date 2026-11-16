# Infrastructure, made repeatable.

<div class="hero" markdown>
<div class="hero-kicker">PYTHON-POWERED LINUX AUTOMATION</div>

# Your infrastructure.<br><span>Under control.</span>

Build consistent Linux servers and workstations with reusable pyinfra tasks, declarative configuration, and idempotent operations.

<div class="hero-actions">
  <a class="md-button md-button--primary" href="deployment/">Get started</a>
  <a class="md-button" href="https://github.com/gpkvt/pyinfra">View source on GitHub ↗</a>
</div>
<div class="hero-meta"><span>Debian &amp; Ubuntu</span><span>Python 3.12+</span><span>MIT licensed</span></div>
</div>

<div class="stats-grid" markdown>
<div class="stat-card" markdown><span class="stat-value">01</span><span class="stat-label">Inventory-driven</span><p>One configuration model for local and remote hosts.</p></div>
<div class="stat-card" markdown><span class="stat-value">∞</span><span class="stat-label">Repeatable runs</span><p>Idempotent tasks designed to converge on the desired state.</p></div>
<div class="stat-card" markdown><span class="stat-value">100%</span><span class="stat-label">Your control</span><p>Review the plan before applying changes to your systems.</p></div>
</div>

## One toolkit. Your whole Linux environment.

From the base operating system to the applications running on it, pyinfra brings host configuration and automation together in one maintainable repository.

<div class="grid cards feature-grid" markdown>
-   :material-server-network: **Infrastructure**
    ---
    Configure packages, repositories, users, SSH, networking, firewall rules, system services, and core Linux settings.
    [Explore system configuration](system.md)

-   :material-docker: **Application services**
    ---
    Deploy Docker Compose applications with persistent host directories, systemd integration, and optional on-demand startup.
    [Browse the task reference](tasks.md#docker-services)

-   :material-monitor: **Workstations**
    ---
    Manage desktop applications, COSMIC settings, Flatpak, fonts, power management, hardware utilities, and user environments.
    [Explore configuration](configuration.md)

-   :material-shield-lock: **Secrets & security**
    ---
    Keep credentials out of tracked configuration with GPG-encrypted JSON and the <code>gpg-vault</code> workflows.
    [Read secrets management](secrets.md)
</div>

## From configuration to convergence

The repository separates host data, orchestration, reusable tasks, and generated configuration. That makes deployments easier to review, reason about, and repeat.

<div class="workflow" markdown>
<div class="workflow-step" markdown><span class="workflow-number">01</span>**Inventory**<p>Define the hosts and connection settings.</p></div>
<div class="workflow-arrow">→</div>
<div class="workflow-step" markdown><span class="workflow-number">02</span>**Configuration**<p>Select host roles, features, and desired settings.</p></div>
<div class="workflow-arrow">→</div>
<div class="workflow-step" markdown><span class="workflow-number">03</span>**Tasks**<p>Run reusable pyinfra operations and templates.</p></div>
<div class="workflow-arrow">→</div>
<div class="workflow-step" markdown><span class="workflow-number">04</span>**Converge**<p>Preview changes, review the diff, then apply.</p></div>
</div>

### Preview first. Apply with confidence.

~~~bash
# Inspect the operations and proposed changes
pyinfra inventory.py deploy.py --dry --diff

# Apply only after reviewing the plan
pyinfra inventory.py deploy.py --diff
~~~

<blockquote class="safety-note"><strong>Built around idempotency.</strong> Tasks should only run when their target state is not already satisfied. The project includes regression tests, pre-commit checks, and a CI deployment-idempotency check to help keep repeat runs clean.</blockquote>

## Get up and running

Start with a local checkout, create your private host configuration from the examples, and inspect the deployment before making changes.

~~~bash
git clone https://github.com/gpkvt/pyinfra.git
cd pyinfra

cp group_data/@local.py.example group_data/@local.py
cp group_data/workstation.py.example group_data/workstation.py

uv sync
source .venv/bin/activate

pyinfra inventory.py deploy.py --dry --diff
~~~

!!! warning "Review before deploying"
    Do not deploy the example configuration unchanged. Replace machine-specific placeholders and review every enabled feature. A deployment can install packages, modify system files and networking, enable services, and change firewall or USB authorization policies. Start with a non-production target.

[Read the full getting-started guide](configuration.md) · [Understand the deployment workflow](deployment.md)

## Explore the documentation

<div class="grid cards docs-grid" markdown>
-   :material-sitemap: **Architecture**
    Understand the repository layers and execution lifecycle.
    [Read architecture](architecture.md)

-   :material-tune: **Configuration**
    Learn about host data, roles, and feature flags.
    [Configure your hosts](configuration.md)

-   :material-rocket-launch: **Deployment**
    Preview, target, and apply operations safely.
    [Deploy with pyinfra](deployment.md)

-   :material-format-list-bulleted: **Task reference**
    Find managed services and reusable task modules.
    [Browse tasks](tasks.md)

-   :material-file-lock: **Secrets**
    Manage encrypted credentials and vault workflows.
    [Protect secrets](secrets.md)

-   :material-code-braces: **Development**
    Run tests, checks, and contribute improvements.
    [Developer guide](development.md)
</div>

<div class="closing-cta" markdown>
## Infrastructure should be predictable.

Explore the code, inspect the tasks, and adapt the configuration to your environment.

[GitHub repository](https://github.com/gpkvt/pyinfra){ .md-button .md-button--primary }
[Report an issue](https://github.com/gpkvt/pyinfra/issues){ .md-button }
</div>
