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
}


def history_row(item) -> rx.Component:
    """Linha da tabela de histórico."""
    return rx.table.row(
        rx.table.cell(
            rx.text(f"#{item.id}", weight="bold",
                style={"fontFamily": "'Quicksand', sans-serif"}
            ),
        ),
        rx.table.cell(
            rx.text(item.created_at[:19].replace("T", " "), size="2", color="gray",
                style={"fontFamily": "'Open Sans', sans-serif"}
            ),
        ),
        rx.table.cell(
            rx.badge(f"{item.total_pairs} pares", 
                style={"background": COLORS["primary_500"], "color": "white"}
            ),
        ),
        rx.table.cell(
            rx.badge(f"{item.cross_encoder_avg:.3f}", 
                style={"background": COLORS["success_500"], "color": "white"}
            ),
        ),
        rx.table.cell(
            rx.badge(f"{item.sbert_avg:.3f}", 
                style={"background": COLORS["secondary_500"], "color": "white"}
            ),
        ),
        rx.table.cell(
            rx.badge(f"{item.bleu_avg:.1f}", 
                style={"background": COLORS["auxiliary_orange"], "color": "white"}
            ),
        ),
        rx.table.cell(
            rx.hstack(
                rx.button(
                    rx.icon("eye", size=14),
                    on_click=lambda: State.load_evaluation_details(item.id),
                    variant="ghost",
                    size="1",
                ),
                rx.button(
                    rx.icon("trash-2", size=14),
                    on_click=lambda: State.delete_evaluation(item.id),
                    variant="ghost",
                    color_scheme="red",
                    size="1",
                ),
                spacing="1",
            ),
        ),
    )


def history_table() -> rx.Component:
    """Tabela de histórico de avaliações com estilo Dadosfera."""
    return rx.box(
        # Header
        rx.hstack(
            rx.vstack(
                rx.heading("Histórico de Avaliações", size="6",
                    style={"fontFamily": "'Quicksand', sans-serif", "fontWeight": "700"}
                ),
                rx.text(
                    "Visualize e gerencie avaliações anteriores.",
                    color="gray",
                    size="2",
                    style={"fontFamily": "'Open Sans', sans-serif"}
                ),
                align="start",
                spacing="1",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("refresh-cw", size=16),
                "Atualizar",
                on_click=State.load_history,
                variant="soft",
                style={
                    "background": COLORS["primary_50"],
                    "color": COLORS["primary_500"],
                    "fontFamily": "'Quicksand', sans-serif",
                    "fontWeight": "600",
                }
            ),
            width="100%",
            align="center",
            margin_bottom="24px",
        ),
        
        # Mensagem de erro
        rx.cond(
            State.error_message != "",
            rx.callout(
                State.error_message,
                icon="info",
                color="red",
                margin_bottom="16px",
            ),
        ),
        
        # Loading
        rx.cond(
            State.is_loading,
            rx.center(
                rx.spinner(size="3"),
                padding="48px",
            ),
            # Tabela ou mensagem vazia
            rx.cond(
                State.history.length() > 0,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("ID"),
                            rx.table.column_header_cell("Data"),
                            rx.table.column_header_cell("Pares"),
                            rx.table.column_header_cell("Cross-Enc"),
                            rx.table.column_header_cell("SBERT"),
                            rx.table.column_header_cell("BLEU"),
                            rx.table.column_header_cell("Ações"),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(State.history, history_row)
                    ),
                    width="100%",
                    style={
                        "background": f"rgba(255, 255, 255, 0.9)",
                        "borderRadius": "12px",
                        "border": f"1px solid {COLORS['primary_100']}",
                    }
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("inbox", size=48, color="gray"),
                        rx.text("Nenhuma avaliação encontrada", color="gray",
                            style={"fontFamily": "'Quicksand', sans-serif", "fontWeight": "600"}
                        ),
                        rx.text("Faça sua primeira avaliação na aba 'Avaliar'", size="2", color="gray",
                            style={"fontFamily": "'Open Sans', sans-serif"}
                        ),
                        spacing="2",
                        align="center",
                    ),
                    padding="48px",
                ),
            ),
        ),
        
        width="100%",
    )
