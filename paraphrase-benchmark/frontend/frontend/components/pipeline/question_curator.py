"""Componente para curadoria de perguntas (Step 2)."""

import reflex as rx
from frontend.state import PipelineState, QuestionItem


# Cores do Design System
COLORS = {
    "primary_500": "#1700a2",
    "primary_100": "#d1ccec",
    "primary_50": "#edeaf7",
    "secondary_500": "#28a1ce",
    "success_500": "#4db04f",
    "warning_500": "#ff9800",
    "danger_500": "#ef4444",
    "basic_900": "#333333",
    "basic_300": "#f2f2f2",
}


def complexity_badge(complexity: rx.Var) -> rx.Component:
    """Badge de complexidade com cor."""
    return rx.badge(
        complexity,
        style={
            "background": rx.cond(
                complexity == "simple",
                COLORS["success_500"],
                rx.cond(
                    complexity == "medium",
                    COLORS["warning_500"],
                    COLORS["danger_500"]
                )
            ),
            "color": "white",
            "fontSize": "10px"
        },
        size="1"
    )


def question_row(question: QuestionItem, index: int) -> rx.Component:
    """Linha de uma pergunta na tabela de curadoria."""
    return rx.box(
        rx.hstack(
            # Checkbox
            rx.checkbox(
                checked=question.selected,
                on_change=lambda: PipelineState.toggle_question_selection(index),
                style={"cursor": "pointer"}
            ),
            
            # Número
            rx.text(
                f"#{index + 1}",
                size="1",
                color="gray",
                style={"minWidth": "35px"}
            ),
            
            # Badges de metadados
            rx.hstack(
                complexity_badge(question.complexity),
                rx.badge(
                    question.query_type,
                    style={"background": COLORS["secondary_500"], "color": "white"},
                    size="1"
                ),
                spacing="1"
            ),
            
            # Texto da pergunta (editável)
            rx.box(
                rx.text_area(
                    value=question.nl_query,
                    on_change=lambda v: PipelineState.update_question_text(index, v),
                    style={
                        "width": "100%",
                        "minHeight": "60px",
                        "fontSize": "13px",
                        "border": f"1px solid {COLORS['primary_100']}",
                        "borderRadius": "6px",
                        "padding": "8px",
                        "resize": "vertical"
                    }
                ),
                flex="1"
            ),
            
            spacing="3",
            align="start",
            width="100%"
        ),
        padding="12px",
        background=rx.cond(
            question.selected,
            "white",
            COLORS["basic_300"]
        ),
        border=f"1px solid {COLORS['primary_100']}",
        border_radius="8px",
        opacity=rx.cond(question.selected, "1", "0.6"),
        style={"transition": "all 0.2s ease"}
    )


def question_curator_step() -> rx.Component:
    """Componente para curadoria das perguntas geradas."""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.icon("list-checks", size=24, color=COLORS["primary_500"]),
                rx.heading(
                    "Curadoria de Perguntas",
                    size="5",
                    style={"fontFamily": "'Quicksand', sans-serif", "fontWeight": "700"}
                ),
                spacing="3",
                align="center"
            ),
            rx.text(
                "Selecione e edite as perguntas que serão usadas para gerar SQLs. "
                "Você pode desmarcar perguntas irrelevantes ou editar o texto.",
                size="2",
                color="gray",
                style={"fontFamily": "'Quicksand', sans-serif"}
            ),
            
            # Estatísticas e ações em massa
            rx.hstack(
                rx.hstack(
                    rx.text(f"Total:", size="2", weight="medium"),
                    rx.text(
                        PipelineState.total_questions,
                        size="2",
                        color=COLORS["primary_500"],
                        weight="bold"
                    ),
                    rx.text("|", size="2", color="gray"),
                    rx.text(f"Selecionadas:", size="2", weight="medium"),
                    rx.text(
                        PipelineState.selected_questions_count,
                        size="2",
                        color=COLORS["success_500"],
                        weight="bold"
                    ),
                    spacing="2"
                ),
                rx.spacer(),
                rx.hstack(
                    rx.button(
                        "Selecionar todas",
                        on_click=PipelineState.select_all_questions,
                        variant="ghost",
                        size="1"
                    ),
                    rx.button(
                        "Desmarcar todas",
                        on_click=PipelineState.deselect_all_questions,
                        variant="ghost",
                        size="1"
                    ),
                    spacing="2"
                ),
                width="100%",
                align="center"
            ),
            
            # Lista de perguntas
            rx.box(
                rx.vstack(
                    rx.foreach(
                        PipelineState.questions,
                        lambda q, i: question_row(q, i)
                    ),
                    spacing="2",
                    width="100%"
                ),
                max_height="500px",
                overflow_y="auto",
                padding="4px",
                width="100%"
            ),
            
            # Botões de navegação
            rx.hstack(
                rx.button(
                    rx.hstack(
                        rx.icon("arrow-left", size=16),
                        rx.text("Voltar"),
                        spacing="2"
                    ),
                    on_click=PipelineState.prev_step,
                    variant="outline",
                    size="3"
                ),
                rx.spacer(),
                rx.button(
                    rx.cond(
                        PipelineState.is_loading,
                        rx.hstack(
                            rx.spinner(size="1"),
                            rx.text("Gerando SQLs..."),
                            spacing="2"
                        ),
                        rx.hstack(
                            rx.icon("code", size=16),
                            rx.text("Gerar SQLs"),
                            spacing="2"
                        )
                    ),
                    on_click=PipelineState.generate_sql,
                    disabled=PipelineState.is_loading,
                    size="3",
                    style={
                        "background": f"linear-gradient(135deg, {COLORS['primary_500']} 0%, {COLORS['secondary_500']} 100%)",
                        "fontFamily": "'Quicksand', sans-serif",
                        "fontWeight": "600"
                    }
                ),
                width="100%",
                align="center"
            ),
            
            spacing="4",
            width="100%"
        ),
        padding="24px",
        background="white",
        border_radius="12px",
        box_shadow="0 2px 8px rgba(23, 0, 162, 0.08)",
        width="100%"
    )

