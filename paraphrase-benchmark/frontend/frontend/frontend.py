import reflex as rx
from frontend.state import State, PipelineState
from frontend.components.evaluation_form import evaluation_form
from frontend.components.history_table import history_table
from frontend.components.pipeline.pipeline_wizard import pipeline_wizard


# Cores do Beast/Dadosfera Design System
COLORS = {
    # Primary - Roxo Dadosfera
    "primary_50": "#edeaf7",
    "primary_100": "#d1ccec",
    "primary_200": "#a299da",
    "primary_300": "#7466c7",
    "primary_400": "#4533b5",
    "primary_500": "#1700a2",  # Main primary
    "primary_600": "#14008a",
    "primary_700": "#14008a",
    "primary_800": "#0c0051",
    "primary_900": "#0d003b",
    
    # Secondary - Azul
    "secondary_400": "#3bbff0",
    "secondary_500": "#28a1ce",
    "secondary_600": "#1884ac",
    
    # Auxiliary
    "auxiliary_orange": "#cc6d29",
    "auxiliary_red": "#cc3e29",
    "auxiliary_pink": "#e10b69",
    
    # Success
    "success_500": "#4db04f",
    "success_600": "#419643",
    
    # Warning
    "warning_500": "#ff9800",
    
    # Danger
    "danger_500": "#ef4444",
    
    # Basic
    "basic_100": "#ffffff",
    "basic_200": "#f9f9f9",
    "basic_300": "#f2f2f2",
    "basic_800": "#5c5c5c",
    "basic_900": "#333333",
    "basic_1000": "#222222",
    "basic_1100": "#101426",
}


# Estilo global com Beast/Dadosfera Design System - Tema Claro
GLOBAL_STYLE = {
    "fontFamily": "'Quicksand', 'Open Sans', sans-serif",
    "background": f"linear-gradient(135deg, {COLORS['basic_100']} 0%, {COLORS['basic_200']} 50%, {COLORS['primary_50']} 100%)",
    "minHeight": "100vh",
    "color": COLORS["basic_900"],
}


def navbar() -> rx.Component:
    """Barra de navegação com estilo Dadosfera."""
    return rx.box(
        rx.hstack(
            rx.hstack(
                rx.box(
                    rx.text("P", weight="bold", size="4", color="white"),
                    background=f"linear-gradient(135deg, {COLORS['primary_500']} 0%, {COLORS['secondary_500']} 100%)",
                    padding="8px 12px",
                    border_radius="8px",
                ),
                rx.heading(
                    "Paraphrase Benchmark",
                    size="5",
                    style={
                        "background": f"linear-gradient(135deg, {COLORS['secondary_400']} 0%, {COLORS['primary_300']} 100%)",
                        "backgroundClip": "text",
                        "WebkitBackgroundClip": "text",
                        "WebkitTextFillColor": "transparent",
                        "fontFamily": "'Quicksand', sans-serif",
                        "fontWeight": "700",
                    }
                ),
                spacing="3",
                align="center",
            ),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    rx.icon("workflow", size=16),
                    "Pipeline",
                    on_click=State.go_to_pipeline,
                    variant=rx.cond(State.current_page == "pipeline", "solid", "ghost"),
                    style={
                        "background": rx.cond(
                            State.current_page == "pipeline",
                            f"linear-gradient(135deg, {COLORS['primary_500']} 0%, {COLORS['secondary_500']} 100%)",
                            "transparent"
                        ),
                        "fontFamily": "'Quicksand', sans-serif",
                        "fontWeight": "600",
                    }
                ),
                rx.button(
                    rx.icon("file-text", size=16),
                    "Avaliar",
                    on_click=State.go_to_evaluate,
                    variant=rx.cond(State.current_page == "evaluate", "solid", "ghost"),
                    style={
                        "background": rx.cond(
                            State.current_page == "evaluate",
                            f"linear-gradient(135deg, {COLORS['primary_500']} 0%, {COLORS['primary_600']} 100%)",
                            "transparent"
                        ),
                        "fontFamily": "'Quicksand', sans-serif",
                        "fontWeight": "600",
                    }
                ),
                rx.button(
                    rx.icon("clock", size=16),
                    "Histórico",
                    on_click=[State.go_to_history, State.load_history],
                    variant=rx.cond(State.current_page == "history", "solid", "ghost"),
                    style={
                        "background": rx.cond(
                            State.current_page == "history",
                            f"linear-gradient(135deg, {COLORS['primary_500']} 0%, {COLORS['primary_600']} 100%)",
                            "transparent"
                        ),
                        "fontFamily": "'Quicksand', sans-serif",
                        "fontWeight": "600",
                    }
                ),
                spacing="2",
            ),
            width="100%",
            align="center",
            padding_x="24px",
            padding_y="16px",
        ),
        background=f"rgba(255, 255, 255, 0.95)",
        backdrop_filter="blur(12px)",
        border_bottom=f"1px solid {COLORS['primary_100']}",
        box_shadow="0 2px 8px rgba(23, 0, 162, 0.08)",
        position="sticky",
        top="0",
        z_index="100",
    )


def footer() -> rx.Component:
    """Rodapé da aplicação com estilo Dadosfera."""
    return rx.box(
        rx.hstack(
            rx.hstack(
                rx.text(
                    "Dadosfera",
                    size="2",
                    weight="bold",
                    style={
                        "background": f"linear-gradient(135deg, {COLORS['secondary_400']} 0%, {COLORS['primary_400']} 100%)",
                        "backgroundClip": "text",
                        "WebkitBackgroundClip": "text",
                        "WebkitTextFillColor": "transparent",
                    }
                ),
                rx.text(
                    " | Paraphrase Benchmark API",
                    size="1",
                    color="gray",
                ),
                spacing="1",
                align="center",
            ),
            rx.spacer(),
            rx.hstack(
                rx.text("Métricas:", size="1", color="gray"),
                rx.badge("Cross-Encoder", 
                    style={"background": COLORS["success_500"], "color": "white"},
                    size="1"
                ),
                rx.badge("SBERT", 
                    style={"background": COLORS["secondary_500"], "color": "white"},
                    size="1"
                ),
                rx.badge("BLEU", 
                    style={"background": COLORS["auxiliary_orange"], "color": "white"},
                    size="1"
                ),
                spacing="2",
            ),
            width="100%",
            align="center",
        ),
        padding="16px 24px",
        background=f"rgba(255, 255, 255, 0.95)",
        border_top=f"1px solid {COLORS['primary_100']}",
    )


def index() -> rx.Component:
    """Página principal."""
    return rx.box(
        navbar(),
        rx.box(
            rx.match(
                State.current_page,
                ("pipeline", pipeline_wizard()),
                ("evaluate", evaluation_form()),
                ("history", history_table()),
                evaluation_form()  # Default
            ),
            max_width="1200px",
            margin="0 auto",
            padding="32px 24px",
        ),
        footer(),
        style=GLOBAL_STYLE,
    )


# Configura o app Reflex
app = rx.App(
    theme=rx.theme(
        appearance="light",
        accent_color="violet",
        radius="medium",
    ),
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Quicksand:wght@300;400;500;600;700&family=Open+Sans:wght@300;400;500;600;700&display=swap",
    ],
)

# Adiciona a página
app.add_page(index, route="/", title="Paraphrase Benchmark | Dadosfera")
