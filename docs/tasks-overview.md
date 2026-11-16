# Tasks

<div class="task-hub" markdown>

<div class="task-hub-hero" markdown>
  <div class="task-hub-eyebrow">PYINFRA · TASK LIBRARY</div>
  ## Infrastructure work, ready to reuse.
  <p>Explore the task modules that configure Linux hosts, provision Docker services and tailor workstation environments. Core tasks establish the baseline; optional tasks are enabled through host and group data.</p>
  <a class="task-hub-primary" href="../tasks/">Browse the complete task reference ↗</a>
</div>

<div class="task-hub-grid">
  <a href="../tasks/#core-tasks">
    <span class="task-hub-index">01 / ALWAYS INCLUDED</span>
    <strong>Core system tasks</strong>
    <p>APT, hosts, sudo, system settings, SSH keys, Git, fonts, scripts and Midnight Commander.</p>
    <b>Explore core tasks ↗</b>
  </a>
  <a href="../tasks/#optional-tasks">
    <span class="task-hub-index">02 / FEATURE GATED</span>
    <strong>Optional features</strong>
    <p>WireGuard, VPN, Syncthing, firewall, Docker, AppArmor, Flatpak, Proton and more.</p>
    <b>Explore optional tasks ↗</b>
  </a>
  <a href="../tasks/#workstation-role-tasks">
    <span class="task-hub-index">03 / WORKSTATION ROLE</span>
    <strong>Desktop &amp; hardware</strong>
    <p>Power, backup, firmware, storage, peripherals, desktop integration and COSMIC.</p>
    <b>Explore workstation tasks ↗</b>
  </a>
  <a href="../tasks/#docker-services">
    <span class="task-hub-index">04 / CONTAINER STACKS</span>
    <strong>Docker services</strong>
    <p>Compose projects, persistent bind-mounted data, systemd lifecycle and service-specific settings.</p>
    <b>Explore Docker tasks ↗</b>
  </a>
</div>

<div class="task-hub-note">
  <strong>Designed for repeatable deployments.</strong>
  <p>Optional modules are gated by configuration, and tasks should avoid reporting changes when the target is already in the desired state. Review dry-run output before applying changes.</p>
</div>

</div>
