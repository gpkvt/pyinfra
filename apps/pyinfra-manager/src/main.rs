//! Pyinfra Manager COSMIC application entry point.
//! The full application model is implemented in app.rs.
mod app;

fn main() -> cosmic::iced::Result {
    let settings = cosmic::app::Settings::default().size_limits(
        cosmic::iced::Limits::NONE
            .min_width(760.0)
            .min_height(520.0),
    );
    cosmic::app::run::<app::AppModel>(settings, ())
}
