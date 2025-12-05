"""Componente principal do wizard de pipeline."""

import reflex as rx
from frontend.state import PipelineState
from frontend.components.pipeline.schema_input import schema_input_step
from frontend.components.pipeline.question_curator import question_curator_step
from frontend.components.pipeline.sql_generator import sql_generator_step
from frontend.components.pipeline.paraphrase_view import paraphrase_view_step
from frontend.components.pipeline.evaluation_step import evaluation_step


# Cores do Design System
COLORS = {
    "primary_500": "#1700a2",
    "primary_400": "#4533b5",
    "primary_100": "#d1ccec",
    "primary_50": "#edeaf7",
    "secondary_500": "#28a1ce",
    "success_500": "#4db04f",
    "warning_500": "#ff9800",
    "danger_500": "#ef4444",
    "basic_900": "#333333",
    "basic_300": "#f2f2f2",
    "basic_100": "#ffffff",
}


def step_indicator(step_num: int, title: str, is_current: rx.Var, is_completed: rx.Var) -> rx.Component:
    """Indicador de um step no wizard."""
    return rx.box(
        rx.vstack(
            rx.box(
                rx.text(
                    str(step_num),
                    size="2",
                    weight="bold",
                    style={
                        "color": rx.cond(
                            is_current,
                            "white",
                            rx.cond(is_completed, "white", COLORS["primary_500"])
                        )
                    }
                ),
                width="32px",
                height="32px",
                display="flex",
                align_items="center",
                justify_content="center",
                border_radius="50%",
                background=rx.cond(
                    is_current,
                    f"linear-gradient(135deg, {COLORS['primary_500']} 0%, {COLORS['secondary_500']} 100%)",
                    rx.cond(
                        is_completed,
                        COLORS["success_500"],
                        "transparent"
                    )
                ),
                border=rx.cond(
                    is_current | is_completed,
                    "none",
                    f"2px solid {COLORS['primary_100']}"
                ),
                style={"transition": "all 0.3s ease"}
            ),
            rx.text(
                title,
                size="1",
                weight=rx.cond(is_current, "bold", "medium"),
                color=rx.cond(
                    is_current,
                    COLORS["primary_500"],
                    rx.cond(is_completed, COLORS["success_500"], "gray")
                ),
                style={
                    "fontFamily": "'Quicksand', sans-serif",
                    "whiteSpace": "nowrap"
                }
            ),
            spacing="1",
            align="center"
        ),
        cursor="pointer",
        on_click=lambda: PipelineState.go_to_step(step_num),
        opacity=rx.cond(step_num <= PipelineState.current_step, "1", "0.5"),
        style={"transition": "opacity 0.2s ease"}
    )


def step_connector(is_completed: rx.Var) -> rx.Component:
    """Conector entre steps."""
    return rx.box(
        width="40px",
        height="2px",
        background=rx.cond(
            is_completed,
            COLORS["success_500"],
            COLORS["primary_100"]
        ),
        margin_bottom="20px",
        style={"transition": "background 0.3s ease"}
    )


def progress_bar() -> rx.Component:
    """Barra de progresso do wizard."""
    steps = [
        (1, "Schema"),
        (2, "Curadoria"),
        (3, "SQL"),
        (4, "Paráfrases"),
        (5, "SQL Final"),
        (6, "Avaliação"),
    ]
    
    items = []
    for i, (step_num, title) in enumerate(steps):
        items.append(
            step_indicator(
                step_num,
                title,
                PipelineState.current_step == step_num,
                PipelineState.current_step > step_num
            )
        )
        if i < len(steps) - 1:
            items.append(
                step_connector(PipelineState.current_step > step_num)
            )
    
    return rx.box(
        rx.hstack(
            *items,
            spacing="0",
            align="center",
            justify="center",
            wrap="wrap"
        ),
        padding="16px",
        background="white",
        border_radius="12px",
        box_shadow="0 2px 8px rgba(23, 0, 162, 0.08)",
        width="100%",
        overflow_x="auto"
    )


def message_box() -> rx.Component:
    """Box de mensagens de erro/sucesso."""
    return rx.vstack(
        # Error message
        rx.cond(
            PipelineState.error_message != "",
            rx.box(
                rx.hstack(
                    rx.icon("alert-circle", size=16, color=COLORS["danger_500"]),
                    rx.text(
                        PipelineState.error_message,
                        size="2",
                        color=COLORS["danger_500"]
                    ),
                    spacing="2",
                    align="center"
                ),
                padding="12px 16px",
                background="#fef2f2",
                border=f"1px solid {COLORS['danger_500']}",
                border_radius="8px",
                width="100%"
            ),
            rx.box()
        ),
        # Success message
        rx.cond(
            PipelineState.success_message != "",
            rx.box(
                rx.hstack(
                    rx.icon("check-circle", size=16, color=COLORS["success_500"]),
                    rx.text(
                        PipelineState.success_message,
                        size="2",
                        color=COLORS["success_500"]
                    ),
                    spacing="2",
                    align="center"
                ),
                padding="12px 16px",
                background="#f0fdf4",
                border=f"1px solid {COLORS['success_500']}",
                border_radius="8px",
                width="100%"
            ),
            rx.box()
        ),
        spacing="2",
        width="100%"
    )


def current_step_content() -> rx.Component:
    """Renderiza o conteúdo do step atual."""
    return rx.match(
        PipelineState.current_step,
        (1, schema_input_step()),
        (2, question_curator_step()),
        (3, sql_generator_step()),
        (4, paraphrase_view_step()),
        (5, paraphrase_view_step()),  # Step 4 e 5 usam o mesmo componente
        (6, evaluation_step()),
        schema_input_step()  # Default
    )


def pipeline_wizard() -> rx.Component:
    """Componente principal do wizard de pipeline."""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.heading(
                    "Pipeline de Geração NL-SQL",
                    size="6",
                    style={
                        "background": f"linear-gradient(135deg, {COLORS['primary_500']} 0%, {COLORS['secondary_500']} 100%)",
                        "backgroundClip": "text",
                        "WebkitBackgroundClip": "text",
                        "WebkitTextFillColor": "transparent",
                        "fontFamily": "'Quicksand', sans-serif",
                        "fontWeight": "700",
                    }
                ),
                rx.spacer(),
                rx.cond(
                    PipelineState.session_id.is_not_none(),
                    rx.badge(
                        f"Sessão #{PipelineState.session_id}",
                        style={"background": COLORS["primary_100"], "color": COLORS["primary_500"]}
                    ),
                    rx.box()
                ),
                width="100%",
                align="center"
            ),
            
            # Progress bar
            progress_bar(),
            
            # Messages
            message_box(),
            
            # Content
            current_step_content(),
            
            spacing="4",
            width="100%"
        ),
        width="100%"
    )

