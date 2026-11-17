//! Main COSMIC application model for Pyinfra Manager.
use cosmic::iced::{Alignment, Length};
use cosmic::prelude::*;
use cosmic::widget;
use std::path::PathBuf;

fn repository_root(path: &std::path::Path) -> Result<PathBuf, String> {
    let root = path.canonicalize().map_err(|error| format!("Cannot access repository directory {}: {error}", path.display()))?;
    let required = ["deploy.py", "inventory.py", "pyproject.toml", "group_data", "tasks", "apps/pyinfra-manager/backend/manager.py"];
    let missing: Vec<_> = required.iter().filter(|relative| !root.join(relative).exists()).copied().collect();
    if !missing.is_empty() { return Err(format!("Not a pyinfra checkout ({}). Missing: {}", root.display(), missing.join(", "))); }
    Ok(root)
}
fn backend_script(project: &str) -> Result<(PathBuf, PathBuf), String> {
    let root = repository_root(&PathBuf::from(project))?;
    let script = root.join("apps/pyinfra-manager/backend/manager.py");
    if !script.is_file() { return Err(format!("Pyinfra backend not found: {}", script.display())); }
    Ok((root, script))
}
fn project_config_file() -> Option<PathBuf> {
    let base = std::env::var_os("XDG_CONFIG_HOME").map(PathBuf::from).or_else(|| std::env::var_os("HOME").map(|home| PathBuf::from(home).join(".config")))?;
    Some(base.join("pyinfra-manager").join("repository"))
}
fn remember_project(root: &std::path::Path) {
    if let Some(file) = project_config_file() { if let Some(parent) = file.parent() { if std::fs::create_dir_all(parent).is_ok() { let _ = std::fs::write(file, root.display().to_string()); } } }
}
fn discover_project() -> Option<PathBuf> {
    let mut candidates = Vec::new();
    if let Some(path) = std::env::var_os("PYINFRA_REPOSITORY") { candidates.push(PathBuf::from(path)); }
    if let Some(file) = project_config_file() { if let Ok(path) = std::fs::read_to_string(file) { candidates.push(PathBuf::from(path.trim())); } }
    if let Ok(path) = std::env::current_dir() { candidates.push(path); }
    if let Ok(executable) = std::env::current_exe() { if let Some(parent) = executable.parent() { candidates.push(parent.to_path_buf()); } }
    for candidate in candidates { for ancestor in candidate.ancestors() { if let Ok(root) = repository_root(ancestor) { return Some(root); } } }
    None
}

use tokio::process::Command;

pub struct AppModel {
    core: cosmic::Core,
    page: Page,
    project_path: String,
    host: String,
    output: String,
    confirm_apply: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Page {
    Overview,
    Tasks,
    Settings,
    Deploy,
}

#[derive(Debug, Clone)]
pub enum Message {
    Navigate(Page),
    ProjectPathChanged(String),
    HostChanged(String),
    LoadCatalog,
    OpenSettings,
    OpenWorkstationSettings,
    ValidateSettings,
    PreviewDeployment,
    RequestApply,
    ConfirmApply,
    CancelApply,
    BackendOutput(String),
}

async fn backend_command(project: String, args: Vec<String>) -> String {
    let (root, script) = match backend_script(&project) { Ok(paths) => paths, Err(error) => return error };
    remember_project(&root);
    let result = Command::new("uv").args(["run", "python"]).arg(&script).args(args).current_dir(&root).output().await;
    match result {
        Ok(output) => { let stdout = String::from_utf8_lossy(&output.stdout); let stderr = String::from_utf8_lossy(&output.stderr); format!("{stdout}{stderr}") }
        Err(error) => format!("Could not start the local backend: {error}"),
    }
}

async fn open_settings(project: String, config_file: &'static str, config_key: &'static str) -> String {
    let (root, script) = match backend_script(&project) { Ok(paths) => paths, Err(error) => return error };
    remember_project(&root);
    let result = Command::new("uv").args(["run", "python"]).arg(&script).arg("init-config").current_dir(&root).output().await;
    match result {
        Ok(output) if output.status.success() => {
            let backup = Command::new("uv").args(["run", "python"]).arg(&script).args(["backup-config", config_key]).current_dir(&root).output().await;
            match backup {
                Ok(backup) if backup.status.success() => {
                    let backup_info = String::from_utf8_lossy(&backup.stdout);
                    let path = root.join("group_data").join(config_file);
                    match Command::new("xdg-open").arg(path).spawn() {
                        Ok(_) => format!("Opened {config_file}. A private backup was created first: {backup_info}"),
                        Err(error) => format!("Backup created, but could not open editor: {error}"),
                    }
                }
                Ok(backup) => format!("Could not create a settings backup: {}{}", String::from_utf8_lossy(&backup.stdout), String::from_utf8_lossy(&backup.stderr)),
                Err(error) => format!("Could not start the backup operation: {error}"),
            }
        }
        Ok(output) => format!("{}{}", String::from_utf8_lossy(&output.stdout), String::from_utf8_lossy(&output.stderr)),
        Err(error) => format!("Could not initialize settings: {error}"),
    }
}

impl cosmic::Application for AppModel {
    type Executor = cosmic::executor::Default;
    type Flags = ();
    type Message = Message;
    const APP_ID: &'static str = "org.pyinfra.Manager";

    fn core(&self) -> &cosmic::Core {
        &self.core
    }

    fn core_mut(&mut self) -> &mut cosmic::Core {
        &mut self.core
    }

    fn init(core: cosmic::Core, _flags: ()) -> (Self, Task<cosmic::Action<Message>>) {
        let project_path = discover_project().unwrap_or_else(|| std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."))).display().to_string();
        (
            Self {
                core,
                page: Page::Overview,
                project_path,
                host: "@local".into(),
                output: "Choose your pyinfra checkout, then load its task catalog.".into(),
                confirm_apply: false,
            },
            Task::none(),
        )
    }

    fn nav_model(&self) -> Option<&cosmic::widget::nav_bar::Model> {
        None
    }

    fn view(&self) -> Element<'_, Message> {
        let heading = widget::text::title1("Pyinfra Manager");
        let project_input = widget::text_input("Repository checkout", &self.project_path)
            .on_input(Message::ProjectPathChanged);
        let navigation = widget::row::with_capacity(4)
            .push(widget::button::text("Overview").on_press(Message::Navigate(Page::Overview)))
            .push(widget::button::text("Tasks").on_press(Message::Navigate(Page::Tasks)))
            .push(widget::button::text("Settings").on_press(Message::Navigate(Page::Settings)))
            .push(widget::button::text("Deploy").on_press(Message::Navigate(Page::Deploy)))
            .spacing(8)
            .align_y(Alignment::Center);

        let body: Element<'_, Message> = match self.page {
            Page::Overview => widget::column::with_capacity(3)
                .push(widget::text::title2("Infrastructure at a glance"))
                .push(widget::text(
                    "The app delegates execution to this checkout's deploy.py.",
                ))
                .push(widget::button::text("Load task catalog").on_press(Message::LoadCatalog))
                .into(),
            Page::Tasks => widget::column::with_capacity(3)
                .push(widget::text::title2("Task catalog"))
                .push(widget::text(
                    "Catalog includes task modules discovered from deploy.py and tasks/.",
                ))
                .push(widget::button::text("Refresh task catalog").on_press(Message::LoadCatalog))
                .into(),
            Page::Settings => widget::column::with_capacity(4)
                .push(widget::text::title2("Host and workstation settings"))
                .push(widget::text(
                    "Choose a file to open it in your system's configured editor.",
                ))
                .push(
                    widget::button::text("Initialize / edit @local.py")
                        .on_press(Message::OpenSettings),
                )
                .push(
                    widget::button::text("Initialize / edit workstation.py")
                        .on_press(Message::OpenWorkstationSettings),
                )
                .push(
                    widget::button::text("Validate both settings files")
                        .on_press(Message::ValidateSettings),
                )
                .into(),
            Page::Deploy => widget::column::with_capacity(5)
                .push(widget::text::title2("Deployment"))
                .push(
                    widget::text_input("Inventory host (for example @local)", &self.host)
                        .on_input(Message::HostChanged),
                )
                .push(
                    widget::button::text("Preview (dry-run)").on_press(Message::PreviewDeployment),
                )
                .push(widget::button::text("Apply deployment…").on_press(Message::RequestApply))
                .push(if self.confirm_apply {
                    widget::row::with_capacity(2)
                        .push(widget::button::text("Confirm apply").on_press(Message::ConfirmApply))
                        .push(widget::button::text("Cancel").on_press(Message::CancelApply))
                } else {
                    widget::row::with_capacity(1)
                        .push(widget::text("Apply requires a separate confirmation."))
                })
                .into(),
        };

        let output = widget::scrollable(widget::text(self.output.as_str())).height(Length::Fill);
        widget::container(
            widget::column::with_capacity(6)
                .push(heading)
                .push(project_input)
                .push(navigation)
                .push(widget::text(
                    "────────────────────────────────────────────────",
                ))
                .push(body)
                .push(widget::text::title3("Activity"))
                .push(output)
                .spacing(16)
                .padding(24)
                .width(Length::Fill)
                .height(Length::Fill),
        )
        .width(Length::Fill)
        .height(Length::Fill)
        .into()
    }

    fn update(&mut self, message: Message) -> Task<cosmic::Action<Message>> {
        match message {
            Message::Navigate(page) => {
                self.page = page;
                self.confirm_apply = false;
            }
            Message::ProjectPathChanged(path) => {
                self.project_path = path;
                if let Ok(root) = repository_root(&PathBuf::from(&self.project_path)) {
                    remember_project(&root);
                    self.output = format!("Using pyinfra checkout: {}", root.display());
                }
            },
            Message::HostChanged(host) => self.host = host,
            Message::LoadCatalog => {
                let project = self.project_path.clone();
                return Task::perform(
                    backend_command(project, vec!["catalog".into()]),
                    Message::BackendOutput,
                )
                .map(cosmic::Action::App);
            }
            Message::OpenSettings => {
                let project = self.project_path.clone();
                return Task::perform(
                    open_settings(project, "@local.py", "local"),
                    Message::BackendOutput,
                )
                .map(cosmic::Action::App);
            }
            Message::OpenWorkstationSettings => {
                let project = self.project_path.clone();
                return Task::perform(
                    open_settings(project, "workstation.py", "workstation"),
                    Message::BackendOutput,
                )
                .map(cosmic::Action::App);
            }
            Message::ValidateSettings => {
                let project = self.project_path.clone();
                return Task::perform(
                    async move {
                        let (root, script) = match backend_script(&project) { Ok(paths) => paths, Err(error) => return error };
                        remember_project(&root);
                        let mut messages = Vec::new();
                        for (key, file) in [
                            ("local", "group_data/@local.py"),
                            ("workstation", "group_data/workstation.py"),
                        ] {
                            let result = Command::new("uv").args(["run", "python"]).arg(&script).args(["validate-config", key, file]).current_dir(&root)
                                .output()
                                .await;
                            match result {
                                Ok(output) => messages.push(format!(
                                    "{}: {}{}",
                                    file,
                                    String::from_utf8_lossy(&output.stdout),
                                    String::from_utf8_lossy(&output.stderr)
                                )),
                                Err(error) => messages.push(format!("{file}: {error}")),
                            }
                        }
                        messages.join("\n")
                    },
                    Message::BackendOutput,
                )
                .map(cosmic::Action::App);
            }
            Message::PreviewDeployment => {
                let project = self.project_path.clone();
                let host = self.host.trim().to_string();
                self.confirm_apply = false;
                return Task::perform(
                    backend_command(project, vec!["run".into(), host]),
                    Message::BackendOutput,
                )
                .map(cosmic::Action::App);
            }
            Message::RequestApply => self.confirm_apply = true,
            Message::ConfirmApply => {
                let project = self.project_path.clone();
                let host = self.host.trim().to_string();
                self.confirm_apply = false;
                return Task::perform(
                    backend_command(project, vec!["run".into(), host, "--apply".into()]),
                    Message::BackendOutput,
                )
                .map(cosmic::Action::App);
            }
            Message::CancelApply => self.confirm_apply = false,
            Message::BackendOutput(output) => self.output = output,
        }
        Task::none()
    }
}


#[cfg(test)]
mod tests {
    use super::*;
    use std::time::{SystemTime, UNIX_EPOCH};

    #[test]
    fn repository_root_rejects_an_incomplete_directory() {
        let path = std::env::temp_dir().join(format!(
            "pyinfra-manager-incomplete-{}",
            std::process::id()
        ));
        std::fs::create_dir_all(&path).expect("create test directory");
        let result = repository_root(&path);
        std::fs::remove_dir_all(&path).expect("remove test directory");
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("Not a pyinfra checkout"));
    }

    #[test]
    fn repository_root_accepts_the_required_checkout_layout() {
        let nonce = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("clock after epoch")
            .as_nanos();
        let path = std::env::temp_dir().join(format!(
            "pyinfra-manager-valid-{}-{nonce}",
            std::process::id()
        ));
        for relative in [
            "group_data",
            "tasks",
            "apps/pyinfra-manager/backend",
        ] {
            std::fs::create_dir_all(path.join(relative)).expect("create required directory");
        }
        for relative in [
            "deploy.py",
            "inventory.py",
            "pyproject.toml",
            "apps/pyinfra-manager/backend/manager.py",
        ] {
            std::fs::write(path.join(relative), "").expect("create required file");
        }

        let result = repository_root(&path).expect("valid checkout");
        assert_eq!(result, path.canonicalize().expect("canonical test path"));
        std::fs::remove_dir_all(path).expect("remove test checkout");
    }
}
