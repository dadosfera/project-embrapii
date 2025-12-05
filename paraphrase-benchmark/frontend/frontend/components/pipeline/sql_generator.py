"""Componente para visualização/edição de SQLs (Step 3)."""

import reflex as rx
from frontend.state import PipelineState, SQLPairItem


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


def sql_pair_card(pair: SQLPairItem, index: int) -> rx.Component:
    """Card de um par NL-SQL."""
    return rx.box(
        rx.vstack(
            # Header com número e badges
            rx.hstack(
                rx.text(
                    f"#{index + 1}",
                    size="2",
                    weight="bold",
                    color=COLORS["primary_500"]
                ),
                rx.hstack(
                    rx.badge(
                        pair.complexity,
                        style={
                            "background": rx.cond(
                                pair.complexity == "simple",
                                COLORS["success_500"],
                                rx.cond(
                                    pair.complexity == "medium",
                                    COLORS["warning_500"],
                                    COLORS["danger_500"]
                                )
                            ),
                            "color": "white"
                        },
                        size="1"
                    ),
                    rx.badge(
                        pair.query_type,
                        style={"background": COLORS["secondary_500"], "color": "white"},
                        size="1"
                    ),
                    spacing="1"
                ),
                spacing="3",
                align="center"
            ),
            
            # Pergunta em linguagem natural
            rx.box(
                rx.text(
                    pair.nl_query,
                    size="2",
                    style={
                        "fontFamily": "'Quicksand', sans-serif",
                        "lineHeight": "1.5"
                    }
                ),
                padding="12px",
                background=COLORS["primary_50"],
                border_radius="6px",
                width="100%"
            ),
            
            # SQL Query (editável)
            rx.box(
                rx.text("SQL Query", size="1", weight="medium", color="gray"),
                rx.text_area(
                    value=pair.sql_query,
                    on_change=lambda v: PipelineState.update_sql_query(index, v),
                    style={
                        "width": "100%",
                        "minHeight": "120px",
                        "fontFamily": "'Fira Code', 'Monaco', monospace",
                        "fontSize": "12px",
                        "backgroundColor": "#1e1e1e",
                        "color": "#d4d4d4",
                        "border": f"1px solid {COLORS['primary_100']}",
                        "borderRadius": "6px",
                        "padding": "12px",
                        "marginTop": "4px"
                    }
                ),
                width="100%"
            ),
            
            # Explicação (se houver)
            rx.cond(
                pair.sql_explanation != "",
                rx.box(
                    rx.text(
                        pair.sql_explanation,
                        size="1",
                        color="gray",
                        style={"fontStyle": "italic"}
                    ),
                    padding="8px",
                    background=COLORS["basic_300"],
                    border_radius="4px",
                    width="100%"
                ),
                rx.box()
            ),
            
            spacing="3",
            width="100%"
        ),
        padding="16px",
        background="white",
        border=f"1px solid {COLORS['primary_100']}",
        border_radius="10px",
        box_shadow="0 1px 3px rgba(0,0,0,0.05)",
        width="100%"
    )


def sql_generator_step() -> rx.Component:
    """Componente para visualização e edição dos SQLs gerados."""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.icon("code", size=24, color=COLORS["primary_500"]),
                rx.heading(
                    "Consultas SQL Geradas",
                    size="5",
                    style={"fontFamily": "'Quicksand', sans-serif", "fontWeight": "700"}
                ),
                spacing="3",
                align="center"
            ),
            rx.text(
                "Revise e edite as consultas SQL geradas para cada pergunta. "
                "Você pode ajustar o SQL diretamente se necessário.",
                size="2",
                color="gray",
                style={"fontFamily": "'Quicksand', sans-serif"}
            ),
            
            # Estatísticas
            rx.hstack(
                rx.text(f"Total de pares NL-SQL:", size="2", weight="medium"),
                rx.text(
                    PipelineState.total_sql_pairs,
                    size="2",
                    color=COLORS["primary_500"],
                    weight="bold"
                ),
                spacing="2"
            ),
            
            # Lista de pares SQL
            rx.box(
                rx.vstack(
                    rx.foreach(
                        PipelineState.sql_pairs,
                        lambda p, i: sql_pair_card(p, i)
                    ),
                    spacing="3",
                    width="100%"
                ),
                max_height="550px",
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
                rx.hstack(
                    rx.vstack(
                        rx.text("Paráfrases por pergunta", size="1", color="gray"),
                        rx.input(
                            value=PipelineState.num_paraphrases.to_string(),
                            on_change=PipelineState.update_num_paraphrases,
                            type="number",
                            min="1",
                            max="10",
                            style={"width": "60px"}
                        ),
                        spacing="1",
                        align="center"
                    ),
                    rx.button(
                        rx.cond(
                            PipelineState.is_loading,
                            rx.hstack(
                                rx.spinner(size="1"),
                                rx.text("Gerando paráfrases..."),
                                spacing="2"
                            ),
                            rx.hstack(
                                rx.icon("messages-square", size=16),
                                rx.text("Gerar Paráfrases"),
                                spacing="2"
                            )
                        ),
                        on_click=PipelineState.generate_paraphrases,
                        disabled=PipelineState.is_loading,
                        size="3",
                        style={
                            "background": f"linear-gradient(135deg, {COLORS['primary_500']} 0%, {COLORS['secondary_500']} 100%)",
                            "fontFamily": "'Quicksand', sans-serif",
                            "fontWeight": "600"
                        }
                    ),
                    spacing="4",
                    align="end"
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

