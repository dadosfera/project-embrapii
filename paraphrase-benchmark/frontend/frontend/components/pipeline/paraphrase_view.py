"""Componente para visualização de paráfrases (Steps 4 e 5)."""

import reflex as rx
from frontend.state import PipelineState, ParaphraseResultItem


# Cores do Design System
COLORS = {
    "primary_500": "#1700a2",
    "primary_100": "#d1ccec",
    "primary_50": "#edeaf7",
    "secondary_500": "#28a1ce",
    "secondary_100": "#d1f0fa",
    "success_500": "#4db04f",
    "warning_500": "#ff9800",
    "danger_500": "#ef4444",
    "basic_900": "#333333",
    "basic_300": "#f2f2f2",
}


def paraphrase_card(item: ParaphraseResultItem, index: int) -> rx.Component:
    """Card de uma paráfrase."""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.text(
                    f"#{index + 1}",
                    size="1",
                    color="gray"
                ),
                rx.cond(
                    item.is_original,
                    rx.badge(
                        "Original",
                        style={"background": COLORS["primary_500"], "color": "white"},
                        size="1"
                    ),
                    rx.badge(
                        "Paráfrase",
                        style={"background": COLORS["secondary_500"], "color": "white"},
                        size="1"
                    )
                ),
                rx.badge(
                    item.complexity,
                    style={
                        "background": rx.cond(
                            item.complexity == "simple",
                            COLORS["success_500"],
                            rx.cond(
                                item.complexity == "medium",
                                COLORS["warning_500"],
                                COLORS["danger_500"]
                            )
                        ),
                        "color": "white"
                    },
                    size="1"
                ),
                spacing="2",
                align="center"
            ),
            
            # Pergunta original (se for paráfrase)
            rx.cond(
                ~item.is_original,
                rx.box(
                    rx.text("Original:", size="1", weight="medium", color="gray"),
                    rx.text(
                        item.original_nl_query,
                        size="1",
                        color=COLORS["basic_900"],
                        style={"fontStyle": "italic"}
                    ),
                    padding="8px",
                    background=COLORS["basic_300"],
                    border_radius="4px",
                    width="100%"
                ),
                rx.box()
            ),
            
            # Pergunta atual
            rx.box(
                rx.text(
                    item.nl_query,
                    size="2",
                    style={
                        "fontFamily": "'Quicksand', sans-serif",
                        "lineHeight": "1.5"
                    }
                ),
                padding="12px",
                background=rx.cond(
                    item.is_original,
                    COLORS["primary_50"],
                    COLORS["secondary_100"]
                ),
                border_radius="6px",
                width="100%"
            ),
            
            # SQL (se tiver)
            rx.cond(
                item.sql_query != "",
                rx.box(
                    rx.text("SQL:", size="1", weight="medium", color="gray"),
                    rx.code(
                        item.sql_query,
                        style={
                            "display": "block",
                            "whiteSpace": "pre-wrap",
                            "fontFamily": "'Fira Code', monospace",
                            "fontSize": "11px",
                            "padding": "8px",
                            "backgroundColor": "#1e1e1e",
                            "color": "#d4d4d4",
                            "borderRadius": "4px",
                            "marginTop": "4px",
                            "maxHeight": "100px",
                            "overflowY": "auto"
                        }
                    ),
                    width="100%"
                ),
                rx.box()
            ),
            
            spacing="2",
            width="100%"
        ),
        padding="12px",
        background="white",
        border=f"1px solid {COLORS['primary_100']}",
        border_radius="8px",
        width="100%"
    )


def paraphrase_view_step() -> rx.Component:
    """Componente para visualização das paráfrases (Step 4-5)."""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.icon("messages-square", size=24, color=COLORS["primary_500"]),
                rx.heading(
                    rx.cond(
                        PipelineState.current_step == 4,
                        "Paráfrases Geradas",
                        "Paráfrases com SQL"
                    ),
                    size="5",
                    style={"fontFamily": "'Quicksand', sans-serif", "fontWeight": "700"}
                ),
                spacing="3",
                align="center"
            ),
            rx.text(
                rx.cond(
                    PipelineState.current_step == 4,
                    "As paráfrases foram geradas! Agora vamos gerar os SQLs correspondentes para cada uma.",
                    "Os SQLs foram regenerados para manter consistência. Revise e prossiga para avaliação."
                ),
                size="2",
                color="gray",
                style={"fontFamily": "'Quicksand', sans-serif"}
            ),
            
            # Estatísticas
            rx.hstack(
                rx.hstack(
                    rx.text("Originais:", size="2", weight="medium"),
                    rx.text(
                        PipelineState.original_count,
                        size="2",
                        color=COLORS["primary_500"],
                        weight="bold"
                    ),
                    spacing="1"
                ),
                rx.text("|", color="gray"),
                rx.hstack(
                    rx.text("Paráfrases:", size="2", weight="medium"),
                    rx.text(
                        PipelineState.paraphrase_only_count,
                        size="2",
                        color=COLORS["secondary_500"],
                        weight="bold"
                    ),
                    spacing="1"
                ),
                rx.text("|", color="gray"),
                rx.hstack(
                    rx.text("Total:", size="2", weight="medium"),
                    rx.text(
                        PipelineState.total_paraphrases,
                        size="2",
                        color=COLORS["success_500"],
                        weight="bold"
                    ),
                    spacing="1"
                ),
                spacing="3"
            ),
            
            # Lista de paráfrases
            rx.box(
                rx.vstack(
                    rx.foreach(
                        PipelineState.paraphrases,
                        lambda p, i: paraphrase_card(p, i)
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
                rx.cond(
                    PipelineState.current_step == 4,
                    # Step 4: Botão para regenerar SQL
                    rx.button(
                        rx.cond(
                            PipelineState.is_loading,
                            rx.hstack(
                                rx.spinner(size="1"),
                                rx.text("Gerando SQLs..."),
                                spacing="2"
                            ),
                            rx.hstack(
                                rx.icon("refresh-cw", size=16),
                                rx.text("Gerar SQLs para Paráfrases"),
                                spacing="2"
                            )
                        ),
                        on_click=PipelineState.regenerate_sql,
                        disabled=PipelineState.is_loading,
                        size="3",
                        style={
                            "background": f"linear-gradient(135deg, {COLORS['primary_500']} 0%, {COLORS['secondary_500']} 100%)",
                            "fontFamily": "'Quicksand', sans-serif",
                            "fontWeight": "600"
                        }
                    ),
                    # Step 5: Botão para avaliação
                    rx.button(
                        rx.hstack(
                            rx.icon("bar-chart-2", size=16),
                            rx.text("Avaliar Paráfrases"),
                            spacing="2"
                        ),
                        on_click=PipelineState.next_step,
                        size="3",
                        style={
                            "background": f"linear-gradient(135deg, {COLORS['primary_500']} 0%, {COLORS['secondary_500']} 100%)",
                            "fontFamily": "'Quicksand', sans-serif",
                            "fontWeight": "600"
                        }
                    )
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

