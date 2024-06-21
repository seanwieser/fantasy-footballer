from nicegui import ui


@ui.page('/leaderboard')
def page():
    ui.label("Leaderboard")
    ui.link("Go down", "/leaderboard-sub")


@ui.page('/leaderboard-sub')
def leaderboard_sub():
    ui.label('This is content on /sub-path/sub-sub-path')
