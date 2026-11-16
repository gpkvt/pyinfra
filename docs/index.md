# pyinfra

<div class="landing" markdown>

<div class="hero" markdown>
<div class="hero-copy">
  <div class="eyebrow">PYINFRA · LINUX INFRASTRUCTURE AUTOMATION</div>

  # Your infrastructure.<br><span>In perfect order.</span>

  <p class="lead">A predictable way to configure Linux servers and workstations. Reusable Python tasks, declarative host data, and idempotent deployments — all in your hands.</p>

  <div class="actions">
    <a class="action primary" href="deployment/">Get started <span>↗</span></a>
    <a class="action secondary" href="https://github.com/gpkvt/pyinfra">Explore on GitHub <span>↗</span></a>
  </div>

  <div class="hero-meta">
    <span><i></i> Debian &amp; Ubuntu</span>
    <span><i></i> Python 3.12+</span>
    <span><i></i> Open source</span>
  </div>
</div>

<div class="hero-visual" aria-label="Illustration of a pyinfra deployment plan">
  <div class="visual-glow"></div>
  <div class="terminal-window">
    <div class="terminal-bar"><span class="window-dots">● ● ●</span><span>deployment · preview</span><span class="terminal-status">READY</span></div>
    <div class="terminal-body">
      <div class="terminal-line"><span class="prompt">$</span> pyinfra inventory.py deploy.py --dry --diff</div>
      <div class="terminal-muted">--> Preparing operations</div>
      <div class="terminal-task"><span class="ok">✓</span><span>apt.packages</span><span class="task-state">in sync</span></div>
      <div class="terminal-task"><span class="ok">✓</span><span>files.directory</span><span class="task-state">in sync</span></div>
      <div class="terminal-task"><span class="change">◇</span><span>systemd.service</span><span class="task-pending">would change</span></div>
      <div class="terminal-task"><span class="ok">✓</span><span>users.user</span><span class="task-state">in sync</span></div>
      <div class="terminal-divider"></div>
      <div class="terminal-summary"><span>4 operations reviewed</span><strong>1 proposed change</strong></div>
      <div class="terminal-foot"><span class="pulse"></span> Dry run · no changes applied</div>
    </div>
  </div>
  <div class="floating-card inventory-card"><span class="mini-label">INVENTORY</span><strong>workstation</strong><small>group · @local</small></div>
  <div class="floating-card state-card"><span class="state-check">✓</span><span><strong>Idempotent by design</strong><small>Only change what needs changing</small></span></div>
</div>
</div>

<div class="trustline">
  <span>ONE CONFIGURATION</span><b>·</b><span>REUSABLE TASKS</span><b>·</b><span>REVIEWABLE CHANGES</span><b>·</b><span>REPEATABLE RESULTS</span>
</div>

<section class="intro-section" markdown>
  <div class="section-head">
    <div class="section-kicker">01 / THE TOOLKIT</div>
    ## Everything you need to manage your Linux environment.
    <p>From the first package to a complete application stack, pyinfra brings infrastructure and workstation automation into one maintainable workflow.</p>
  </div>
  <div class="feature-grid">
    <a class="feature-card" href="system/">
      <div class="feature-icon mint">⌘</div>
      <h3>System configuration</h3>
      <p>Packages, repositories, users, SSH, networking, firewall rules and system services.</p>
      <span class="card-link">Explore system tasks ↗</span>
    </a>
    <a class="feature-card" href="tasks/">
      <div class="feature-icon blue">▦</div>
      <h3>Application services</h3>
      <p>Deploy Docker Compose applications with persistent host directories and systemd integration.</p>
      <span class="card-link">Browse task reference ↗</span>
    </a>
    <a class="feature-card" href="configuration/">
      <div class="feature-icon violet">◈</div>
      <h3>Workstations</h3>
      <p>Manage desktop applications, COSMIC settings, Flatpak, fonts and user environments.</p>
      <span class="card-link">Explore configuration ↗</span>
    </a>
    <a class="feature-card" href="secrets/">
      <div class="feature-icon amber">⌑</div>
      <h3>Secrets &amp; security</h3>
      <p>Keep credentials out of tracked configuration with GPG-encrypted data and vault workflows.</p>
      <span class="card-link">Read secrets guide ↗</span>
    </a>
    <a class="feature-card" href="templates/">
      <div class="feature-icon blue">⌁</div>
      <h3>Reusable templates</h3>
      <p>Generate consistent configuration files from Jinja templates and host-specific data.</p>
      <span class="card-link">Explore templates ↗</span>
    </a>
    <a class="feature-card" href="architecture/">
      <div class="feature-icon mint">◎</div>
      <h3>Clear architecture</h3>
      <p>Separate inventory, host data, orchestration and task modules for easier maintenance.</p>
      <span class="card-link">Understand the design ↗</span>
    </a>
  </div>
</section>

<section class="showcase-section" markdown>
  <div class="section-head">
    <div class="section-kicker">02 / HOW IT WORKS</div>
    ## A workflow you can reason about.
    <p>Define the desired state, inspect the operations, and apply only after you understand the plan.</p>
  </div>
  <div class="workflow">
    <div class="workflow-step"><span>01</span><div class="workflow-symbol">⌗</div><h3>Inventory</h3><p>Choose the hosts and connection settings.</p></div>
    <div class="workflow-connector">→</div>
    <div class="workflow-step"><span>02</span><div class="workflow-symbol">◇</div><h3>Configuration</h3><p>Describe roles, features and host-specific data.</p></div>
    <div class="workflow-connector">→</div>
    <div class="workflow-step"><span>03</span><div class="workflow-symbol">⌘</div><h3>Tasks</h3><p>Run reusable operations and render templates.</p></div>
    <div class="workflow-connector">→</div>
    <div class="workflow-step"><span>04</span><div class="workflow-symbol">✓</div><h3>Converge</h3><p>Review the diff, then apply the desired state.</p></div>
  </div>
  <div class="code-showcase">
    <div class="code-copy">
      <div class="section-kicker">PREVIEW BEFORE YOU APPLY</div>
      <h3>Know what will change. Before it changes.</h3>
      <p>Dry runs and diffs make operations reviewable. Idempotent tasks avoid unnecessary work and keep repeated deployments quiet.</p>
      <ul class="check-list">
        <li>Inspect planned operations</li>
        <li>Review file and configuration diffs</li>
        <li>Run again without noisy false changes</li>
      </ul>
      <a class="text-link" href="deployment/">Read the deployment guide ↗</a>
    </div>
    <div class="code-panel">
      <div class="code-panel-head"><span>TERMINAL</span><span>bash</span></div>
      <pre><code><span class="code-comment"># Preview operations and diffs</span>
<span class="code-prompt">$</span> pyinfra inventory.py deploy.py --dry --diff

<span class="code-comment"># Apply after reviewing the plan</span>
<span class="code-prompt">$</span> pyinfra inventory.py deploy.py --diff</code></pre>
      <div class="code-panel-foot"><span class="pulse"></span> Review first · Apply deliberately</div>
    </div>
  </div>
</section>

<section class="install-section" markdown>
  <div class="install-copy">
    <div class="section-kicker">03 / GET STARTED</div>
    ## Your next deployment starts here.
    <p>Clone the repository, prepare your local host configuration, and inspect the first run. Start with a non-production target and adapt the examples before deploying.</p>
    <a class="action primary" href="configuration/">Read the getting-started guide <span>↗</span></a>
  </div>
  <div class="install-terminal">
    <div class="code-panel-head"><span>QUICK START</span><span>bash</span></div>
    <pre><code><span class="code-prompt">$</span> git clone https://github.com/gpkvt/pyinfra.git
<span class="code-prompt">$</span> cd pyinfra
<span class="code-prompt">$</span> cp group_data/@local.py.example group_data/@local.py
<span class="code-prompt">$</span> uv sync
<span class="code-prompt">$</span> source .venv/bin/activate
<span class="code-prompt">$</span> pyinfra inventory.py deploy.py --dry --diff</code></pre>
  </div>
</section>

<div class="safety-note">
  <span class="safety-icon">!</span>
  <div><strong>Review before deploying.</strong><p>Example configuration contains machine-specific assumptions. Replace placeholders and inspect enabled features. Deployments can install packages, modify system files, networking, services and security policies.</p></div>
</div>

<section class="docs-section" markdown>
  <div class="section-head">
    <div class="section-kicker">04 / DOCUMENTATION</div>
    ## Go deeper.
    <p>Find the details you need, from the architecture to individual task modules.</p>
  </div>
  <div class="docs-grid">
    <a href="architecture/"><span>01</span><strong>Architecture</strong><small>Repository layers and execution lifecycle</small><b>↗</b></a>
    <a href="configuration/"><span>02</span><strong>Configuration</strong><small>Host data, roles and feature flags</small><b>↗</b></a>
    <a href="deployment/"><span>03</span><strong>Deployment</strong><small>Preview, target and apply operations</small><b>↗</b></a>
    <a href="tasks/"><span>04</span><strong>Task reference</strong><small>Reusable modules and managed services</small><b>↗</b></a>
    <a href="secrets/"><span>05</span><strong>Secrets</strong><small>Encrypted credentials and vault workflows</small><b>↗</b></a>
    <a href="development/"><span>06</span><strong>Development</strong><small>Tests, checks and contribution guide</small><b>↗</b></a>
  </div>
</section>

<div class="final-cta">
  <div class="eyebrow">PYINFRA · OPEN SOURCE</div>
  <h2>Make infrastructure<br><span>predictable.</span></h2>
  <p>Explore the code, inspect the tasks, and shape a Linux environment that stays the way you intend.</p>
  <div class="actions">
    <a class="action primary" href="https://github.com/gpkvt/pyinfra">View the repository ↗</a>
    <a class="action secondary" href="https://github.com/gpkvt/pyinfra/issues">Report an issue</a>
  </div>
</div>

</div>
