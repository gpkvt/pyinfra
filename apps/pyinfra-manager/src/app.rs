//! Main COSMIC application model for Pyinfra Manager.
use cosmic::iced::{Alignment, Length};
use cosmic::prelude::*;
use cosmic::widget;

pub struct AppModel {
    core: cosmic::Core,
    page: Page,
    status: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]\nenum Page {
    Overview,
    Tasks,
    Settings,
    Deploy,
}

#[derive(Debug, Clone)]
enum Message {
    Navigate(Page),
    BackendUnavailable,
}

impl cosmic::Application for AppModel {
    type Executor = cosmic::executor::Default;
    type Flags = ();
    type Message = Message;
    const APP_ID: &'static str = "org.pyinfra.Manager";

    fn core(&self) -> &cosmic::Core { &self.core }
    fn core_mut(&mut self) -> &mut cosmic::Core { &mut self.core }

    fn init(core: cosmic::Core, _flags: ()) -> (Self, Task<cosmic::Action<Message>>) {
        (Self {
            core,
            page: Page::Overview,
            status: "Select a project checkout to get started.".into(),
        }, Task::none())
    }

    fn nav_model(&self) -> Option<&cosmic::widget::nav_bar::Model> {
        None
    }

    fn view(&self) -> Element<'_, Message> {
        let heading = widget::text::title1("Pyinfra Manager");
        let navigation = widget::row::with_capacity(4)
            .push(widget::button::text("Overview").on_press(Message::Navigate(Page::Overview)))
            .push(widget::button::text("Tasks").on_press(Message::Navigate(Page::Tasks)))
            .push(widget::button::text("Settings").on_press(Message::Navigate(Page::Settings)))
            .push(widget::button::text("Deploy").on_press(Message::Navigate(Page::Deploy)))
            .spacing(8)
            .align_y(Alignment::Center);
        let body: Element<'_, Message> = match self.page {
            Page::Overview => widget::column()
                .push(widget::text::title2("Infrastructure at a glance"))
                .push(widget::text(self.status.as_str()))
                .push(widget::text("Use Tasks to inspect the repository task catalog."))
                .into(),
            Page::Tasks => widget::column()
                .push(widget::text::title2("Task catalog"))
                .push(widget::text("Core, optional and workstation task modules are discovered from deploy.py."))
                .push(widget::text("Conditional inclusion remains controlled by the repository configuration."))
                .into(),
            Page::Settings => widget::column()
                .push(widget::text::title2("Host and workstation settings"))
                .push(widget::text("Edit group_data/@local.py and group_data/workstation.py."))
                .push(widget::text("Settings are syntax-validated and backed up before saving."))
                .into(),
            Page::Deploy => widget::column()
                .push(widget::text::title2("Deployment"))
                .push(widget::text("Preview with pyinfra --dry --diff before applying any changes."))
                .push(widget::text("Applying a deployment requires explicit confirmation."))
                .into(),
        };
        widget::container(
            widget::column()
                .push(heading)
                .push(navigation)
                .push(widget::text("────────────────────────────────────────────────"))
                .push(body)
                .spacing(20)
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
            Message::Navigate(page) => self.page = page,
            Message::BackendUnavailable => {
                self.status = "The local Python backend could not be started.".into();
            }
        }
        Task::none()
    }
}
