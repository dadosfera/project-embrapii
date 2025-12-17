import reflex as rx
from frontend.state import State


# Cores do Beast/Dadosfera Design System
COLORS = {
    "primary_50": "#edeaf7",
    "primary_100": "#d1ccec",
    "primary_200": "#a299da",
    "primary_500": "#1700a2",
    "primary_600": "#14008a",
    "primary_800": "#0c0051",
    "secondary_400": "#3bbff0",
    "secondary_500": "#28a1ce",
    "success_500": "#4db04f",
    "auxiliary_orange": "#cc6d29",
    "danger_500": "#ef4444",
}


def pair_input(pair, index: int) -> rx.Component:
    """Componente para entrada de um par (original + paráfrase)."""
    return rx.box(
        rx.hstack(
            rx.box(
                rx.text("Original", size="1", color="gray", 
                    style={"fontFamily": "'Quicksand', sans-serif", "fontWeight": "600"}
                ),
                rx.text_area(
                    placeholder="Digite o texto original...",
                    value=pair.original,
                    on_change=lambda v: State.update_original(index, v),
                    width="100%",
                    min_height="80px",
                    style={
                        "background": "rgba(237, 234, 247, 0.5)",
                        "border": f"1px solid {COLORS['primary_200']}",
                        "borderRadius": "8px",
                        "fontFamily": "'Open Sans', sans-serif",
                        "color": "#333333",
                    }
                ),
                width="45%",
            ),
            rx.box(
                rx.text("Paráfrase", size="1", color="gray",
                    style={"fontFamily": "'Quicksand', sans-serif", "fontWeight": "600"}
                ),
                rx.text_area(
                    placeholder="Digite a paráfrase...",
                    value=pair.paraphrase,
                    on_change=lambda v: State.update_paraphrase(index, v),
                    width="100%",
                    min_height="80px",
                    style={
                        "background": "rgba(237, 234, 247, 0.5)",
                        "border": f"1px solid {COLORS['primary_200']}",
                        "borderRadius": "8px",
                        "fontFamily": "'Open Sans', sans-serif",
                        "color": "#333333",
                    }
                ),
                width="45%",
            ),
            rx.button(
                rx.icon("trash-2", size=16),
                on_click=lambda: State.remove_pair(index),
                variant="ghost",
                color_scheme="red",
                size="1",
            ),
            spacing="3",
            align="end",
            width="100%",
        ),
        padding="16px",
        background=f"rgba(255, 255, 255, 0.8)",
        border=f"1px solid {COLORS['primary_100']}",
        border_radius="12px",
        margin_bottom="12px",
        box_shadow="0 2px 8px rgba(23, 0, 162, 0.06)",
    )


def metric_card(title: str, value, description: str, color: str) -> rx.Component:
    """Card para exibir uma métrica com estilo Dadosfera."""
    return rx.box(
        rx.vstack(
            rx.text(title, size="2", weight="bold", color="gray",
                style={"fontFamily": "'Quicksand', sans-serif"}
            ),
            rx.text(value, size="7", weight="bold", 
                style={
                    "color": color,
                    "fontFamily": "'Quicksand', sans-serif",
                }
            ),
            rx.text(description, size="1", color="gray",
                style={"fontFamily": "'Open Sans', sans-serif"}
            ),
            spacing="1",
            align="center",
        ),
        padding="24px",
        background=f"rgba(255, 255, 255, 0.9)",
        border=f"1px solid {COLORS['primary_100']}",
        border_radius="16px",
        flex="1",
        min_width="180px",
        box_shadow="0 4px 12px rgba(23, 0, 162, 0.08)",
    )


def result_row(result) -> rx.Component:
    """Linha da tabela de resultados."""
    return rx.table.row(
        rx.table.cell(
            rx.text(result.original, size="2",
                style={"fontFamily": "'Open Sans', sans-serif"}
            ),
            max_width="300px",
            style={"overflow": "hidden", "textOverflow": "ellipsis"}
        ),
        rx.table.cell(
            rx.text(result.paraphrase, size="2",
                style={"fontFamily": "'Open Sans', sans-serif"}
            ),
            max_width="300px",
            style={"overflow": "hidden", "textOverflow": "ellipsis"}
        ),
        rx.table.cell(
            rx.badge(f"{result.cross_encoder:.3f}", 
                style={"background": COLORS["success_500"], "color": "white"}
            ),
        ),
        rx.table.cell(
            rx.badge(f"{result.sbert:.3f}", 
                style={"background": COLORS["secondary_500"], "color": "white"}
            ),
        ),
        rx.table.cell(
            rx.badge(f"{result.bleu:.1f}", 
                style={"background": COLORS["auxiliary_orange"], "color": "white"}
            ),
        ),
    )


def evaluation_form() -> rx.Component:
    """Formulário de avaliação de paráfrases com estilo Dadosfera."""
    return rx.box(
        # Header
        rx.hstack(
            rx.vstack(
                rx.heading("Avaliar Paráfrases", size="6",
                    style={
                        "fontFamily": "'Quicksand', sans-serif",
                        "fontWeight": "700",
                    }
                ),
                rx.text(
                    "Insira pares de texto original e paráfrase para avaliar a qualidade.",
                    color="gray",
                    size="2",
                    style={"fontFamily": "'Open Sans', sans-serif"}
                ),
                align="start",
                spacing="1",
            ),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    rx.icon("plus", size=16),
                    "Adicionar Par",
                    on_click=State.add_pair,
                    variant="soft",
                    style={
                        "background": COLORS["primary_50"],
                        "color": COLORS["primary_500"],
                        "fontFamily": "'Quicksand', sans-serif",
                        "fontWeight": "600",
                    }
                ),
                rx.button(
                    rx.icon("eraser", size=16),
                    "Limpar",
                    on_click=State.clear_form,
                    variant="ghost",
                    style={"fontFamily": "'Quicksand', sans-serif"}
                ),
                spacing="2",
            ),
            width="100%",
            align="center",
            margin_bottom="24px",
        ),
        
        # Formulário de pares
        rx.foreach(
            State.pairs,
            lambda pair, idx: pair_input(pair, idx)
        ),
        
        # Botão de avaliação
        rx.button(
            rx.cond(
                State.is_loading,
                rx.hstack(
                    rx.spinner(size="1"),
                    rx.text("Avaliando..."),
                    spacing="2",
                ),
                rx.hstack(
                    rx.icon("sparkles", size=16),
                    rx.text("Avaliar"),
                    spacing="2",
                ),
            ),
            on_click=State.evaluate,
            disabled=State.is_loading,
            size="3",
            width="100%",
            margin_top="16px",
            style={
                "background": f"linear-gradient(135deg, {COLORS['primary_500']} 0%, {COLORS['secondary_500']} 100%)",
                "cursor": "pointer",
                "fontFamily": "'Quicksand', sans-serif",
                "fontWeight": "700",
                "fontSize": "1rem",
            }
        ),
        
        # Mensagem de erro
        rx.cond(
            State.error_message != "",
            rx.callout(
                State.error_message,
                icon="info",
                color="red",
                margin_top="16px",
            ),
        ),
        
        # Resultados
        rx.cond(
            State.results.length() > 0,
            rx.box(
                rx.divider(margin_y="32px", style={"borderColor": COLORS["primary_100"]}),
                
                rx.heading("Resultados", size="5", margin_bottom="16px",
                    style={"fontFamily": "'Quicksand', sans-serif", "fontWeight": "700"}
                ),
                
                # Cards de métricas
                rx.hstack(
                    metric_card(
                        "Cross-Encoder",
                        State.cross_encoder_display,
                        "Similaridade semântica",
                        COLORS["success_500"]
                    ),
                    metric_card(
                        "SBERT",
                        State.sbert_display,
                        "Embeddings cosine",
                        COLORS["secondary_400"]
                    ),
                    metric_card(
                        "BLEU",
                        State.bleu_display,
                        "Diversidade (menor = mais diverso)",
                        COLORS["auxiliary_orange"]
                    ),
                    spacing="4",
                    wrap="wrap",
                    justify="center",
                    margin_bottom="24px",
                ),
                
                # Tabela de resultados detalhados
                rx.box(
                    rx.text("Detalhes por Par", size="3", weight="medium", margin_bottom="12px",
                        style={"fontFamily": "'Quicksand', sans-serif"}
                    ),
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Original"),
                                rx.table.column_header_cell("Paráfrase"),
                                rx.table.column_header_cell("Cross-Enc"),
                                rx.table.column_header_cell("SBERT"),
                                rx.table.column_header_cell("BLEU"),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(State.results, result_row)
                        ),
                        width="100%",
                        style={
                            "background": f"rgba(255, 255, 255, 0.9)",
                            "borderRadius": "12px",
                            "border": f"1px solid {COLORS['primary_100']}",
                        }
                    ),
                ),
            ),
        ),
        
        width="100%",
    )
