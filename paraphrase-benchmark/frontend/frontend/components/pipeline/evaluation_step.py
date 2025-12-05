"""Componente para avaliação final (Step 6)."""

import reflex as rx
from frontend.state import PipelineState, ResultItem


# Cores do Design System
COLORS = {
    "primary_500": "#1700a2",
    "primary_100": "#d1ccec",
    "primary_50": "#edeaf7",
    "secondary_500": "#28a1ce",
    "success_500": "#4db04f",
    "warning_500": "#ff9800",
    "danger_500": "#ef4444",
    "auxiliary_orange": "#cc6d29",
    "basic_900": "#333333",
    "basic_300": "#f2f2f2",
}


def metric_card(title: str, value: rx.Var, color: str, description: str) -> rx.Component:
    """Card de uma métrica."""
    return rx.box(
        rx.vstack(
            rx.text(title, size="2", weight="medium", color="gray"),
            rx.text(
                value,
                size="7",
                weight="bold",
                style={"color": color, "fontFamily": "'Quicksand', sans-serif"}
            ),
            rx.text(
                description,
                size="1",
                color="gray",
                style={"textAlign": "center"}
            ),
            spacing="1",
            align="center"
        ),
        padding="20px",
        background="white",
        border=f"2px solid {color}",
        border_radius="12px",
        min_width="150px",
        style={"boxShadow": f"0 4px 12px {color}22"}
    )


def result_row(result: ResultItem, index: int) -> rx.Component:
    """Linha de resultado na tabela."""
    return rx.box(
        rx.hstack(
            rx.text(f"#{index + 1}", size="1", color="gray", style={"minWidth": "30px"}),
            rx.vstack(
                rx.text(
                    result.original,
                    size="1",
                    style={"fontWeight": "500", "color": COLORS["primary_500"]}
                ),
                rx.text(
                    result.paraphrase,
                    size="1",
                    color=COLORS["basic_900"]
                ),
                spacing="1",
                align="start",
                flex="1"
            ),
            rx.hstack(
                rx.vstack(
                    rx.text("CE", size="1", color="gray"),
                    rx.text(
                        result.cross_encoder.to(str),
                        size="1",
                        weight="bold",
                        color=COLORS["success_500"]
                    ),
                    spacing="0",
                    align="center"
                ),
                rx.vstack(
                    rx.text("SB", size="1", color="gray"),
                    rx.text(
                        result.sbert.to(str),
                        size="1",
                        weight="bold",
                        color=COLORS["secondary_500"]
                    ),
                    spacing="0",
                    align="center"
                ),
                rx.vstack(
                    rx.text("BL", size="1", color="gray"),
                    rx.text(
                        result.bleu.to(str),
                        size="1",
                        weight="bold",
                        color=COLORS["auxiliary_orange"]
                    ),
                    spacing="0",
                    align="center"
                ),
                spacing="4"
            ),
            spacing="3",
            align="center",
            width="100%"
        ),
        padding="12px",
        background=rx.cond(
            index % 2 == 0,
            "white",
            COLORS["basic_300"]
        ),
        border_radius="6px",
        width="100%"
    )


def evaluation_step() -> rx.Component:
    """Componente de avaliação final das paráfrases."""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.icon("bar-chart-2", size=24, color=COLORS["primary_500"]),
                rx.heading(
                    "Avaliação das Paráfrases",
                    size="5",
                    style={"fontFamily": "'Quicksand', sans-serif", "fontWeight": "700"}
                ),
                spacing="3",
                align="center"
            ),
            rx.text(
                "Avalie a qualidade semântica das paráfrases geradas usando métricas de similaridade.",
                size="2",
                color="gray",
                style={"fontFamily": "'Quicksand', sans-serif"}
            ),
            
            # Botão de avaliação (se ainda não avaliou)
            rx.cond(
                PipelineState.evaluation_results.length() == 0,
                rx.box(
                    rx.vstack(
                        rx.text(
                            f"Total de pares para avaliar: {PipelineState.paraphrase_only_count}",
                            size="2",
                            weight="medium"
                        ),
                        rx.button(
                            rx.cond(
                                PipelineState.is_loading,
                                rx.hstack(
                                    rx.spinner(size="1"),
                                    rx.text("Avaliando..."),
                                    spacing="2"
                                ),
                                rx.hstack(
                                    rx.icon("play", size=16),
                                    rx.text("Executar Avaliação"),
                                    spacing="2"
                                )
                            ),
                            on_click=PipelineState.run_evaluation,
                            disabled=PipelineState.is_loading,
                            size="3",
                            style={
                                "background": f"linear-gradient(135deg, {COLORS['primary_500']} 0%, {COLORS['secondary_500']} 100%)",
                                "fontFamily": "'Quicksand', sans-serif",
                                "fontWeight": "600"
                            }
                        ),
                        spacing="3",
                        align="center"
                    ),
                    padding="32px",
                    background=COLORS["primary_50"],
                    border_radius="12px",
                    width="100%",
                    style={"textAlign": "center"}
                ),
                # Resultados da avaliação
                rx.vstack(
                    # Cards de métricas
                    rx.hstack(
                        metric_card(
                            "Cross-Encoder",
                            f"{PipelineState.pipeline_cross_encoder_avg:.3f}",
                            COLORS["success_500"],
                            "Similaridade semântica"
                        ),
                        metric_card(
                            "SBERT",
                            f"{PipelineState.pipeline_sbert_avg:.3f}",
                            COLORS["secondary_500"],
                            "Embeddings de sentenças"
                        ),
                        metric_card(
                            "BLEU",
                            f"{PipelineState.pipeline_bleu_avg:.1f}",
                            COLORS["auxiliary_orange"],
                            "Diversidade lexical"
                        ),
                        spacing="4",
                        justify="center",
                        wrap="wrap",
                        width="100%"
                    ),
                    
                    # Interpretação
                    rx.box(
                        rx.vstack(
                            rx.text("Interpretação", size="2", weight="bold"),
                            rx.text(
                                "• Cross-Encoder > 0.7: Alta similaridade semântica",
                                size="1",
                                color="gray"
                            ),
                            rx.text(
                                "• SBERT > 0.8: Embeddings muito próximos",
                                size="1",
                                color="gray"
                            ),
                            rx.text(
                                "• BLEU 15-40: Diversidade estrutural adequada",
                                size="1",
                                color="gray"
                            ),
                            spacing="1",
                            align="start"
                        ),
                        padding="12px",
                        background=COLORS["basic_300"],
                        border_radius="8px",
                        width="100%"
                    ),
                    
                    # Tabela de resultados
                    rx.text("Resultados Detalhados", size="3", weight="bold"),
                    rx.box(
                        rx.vstack(
                            rx.foreach(
                                PipelineState.evaluation_results,
                                lambda r, i: result_row(r, i)
                            ),
                            spacing="1",
                            width="100%"
                        ),
                        max_height="300px",
                        overflow_y="auto",
                        width="100%"
                    ),
                    
                    spacing="4",
                    width="100%"
                )
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
                    rx.hstack(
                        rx.icon("refresh-cw", size=16),
                        rx.text("Novo Pipeline"),
                        spacing="2"
                    ),
                    on_click=PipelineState.reset_pipeline,
                    variant="outline",
                    size="3",
                    color_scheme="green"
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

