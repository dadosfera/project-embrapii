"""Componente para input do schema (Step 1)."""

import reflex as rx
from frontend.state import PipelineState


# Cores do Design System
COLORS = {
    "primary_500": "#1700a2",
    "primary_100": "#d1ccec",
    "primary_50": "#edeaf7",
    "secondary_500": "#28a1ce",
    "secondary_100": "#d1f0fa",
    "success_500": "#4db04f",
    "basic_900": "#333333",
    "basic_800": "#5c5c5c",
    "basic_300": "#f2f2f2",
    "basic_100": "#ffffff",
}

# Estilos de input melhorados
INPUT_STYLE = {
    "backgroundColor": COLORS["basic_100"],
    "color": COLORS["basic_900"],
    "border": f"1px solid {COLORS['primary_100']}",
    "borderRadius": "6px",
    "padding": "8px 12px",
    "fontSize": "14px",
    "fontFamily": "'Quicksand', sans-serif",
    "outline": "none",
    "&:focus": {
        "borderColor": COLORS["primary_500"],
        "boxShadow": f"0 0 0 2px {COLORS['primary_100']}"
    },
    "&::placeholder": {
        "color": COLORS["basic_800"],
        "opacity": "0.7"
    }
}


def model_badge() -> rx.Component:
    """Badge mostrando o modelo atual."""
    return rx.hstack(
        rx.icon("cpu", size=14, color=COLORS["secondary_500"]),
        rx.text(
            PipelineState.selected_model,
            size="1",
            weight="medium",
            color=COLORS["secondary_500"]
        ),
        spacing="1",
        padding="4px 10px",
        background=COLORS["secondary_100"],
        border_radius="20px",
        align="center"
    )


def provider_selector() -> rx.Component:
    """Seletor de provedor e modelo."""
    return rx.hstack(
        # Provider
        rx.vstack(
            rx.text("Provedor", size="1", weight="medium", color=COLORS["basic_800"]),
            rx.select(
                ["openai", "anthropic", "google"],
                value=PipelineState.selected_provider,
                on_change=PipelineState.update_provider,
                style={
                    "minWidth": "130px",
                    **INPUT_STYLE
                }
            ),
            spacing="1",
            align="start"
        ),
        # Model
        rx.vstack(
            rx.text("Modelo", size="1", weight="medium", color=COLORS["basic_800"]),
            rx.match(
                PipelineState.selected_provider,
                ("openai", rx.select(
                    ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
                    value=PipelineState.selected_model,
                    on_change=PipelineState.update_model,
                    style={"minWidth": "160px", **INPUT_STYLE}
                )),
                ("anthropic", rx.select(
                    ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
                    value=PipelineState.selected_model,
                    on_change=PipelineState.update_model,
                    style={"minWidth": "220px", **INPUT_STYLE}
                )),
                ("google", rx.select(
                    ["gemini-2.0-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro-latest", "gemini-pro"],
                    value=PipelineState.selected_model,
                    on_change=PipelineState.update_model,
                    style={"minWidth": "200px", **INPUT_STYLE}
                )),
                rx.select(
                    ["gpt-4o"],
                    value=PipelineState.selected_model,
                    on_change=PipelineState.update_model,
                    style={"minWidth": "160px", **INPUT_STYLE}
                )
            ),
            spacing="1",
            align="start"
        ),
        spacing="4",
        align="end"
    )


def schema_input_step() -> rx.Component:
    """Componente para entrada do schema do banco de dados."""
    return rx.box(
        rx.vstack(
            # Header com badge do modelo
            rx.hstack(
                rx.hstack(
                    rx.icon("database", size=24, color=COLORS["primary_500"]),
                    rx.heading(
                        "Schema do Banco de Dados",
                        size="5",
                        style={"fontFamily": "'Quicksand', sans-serif", "fontWeight": "700"}
                    ),
                    spacing="3",
                    align="center"
                ),
                rx.spacer(),
                model_badge(),
                width="100%",
                align="center"
            ),
            rx.text(
                "Cole abaixo o DDL (CREATE TABLE) ou descrição do schema do seu banco de dados. "
                "O modelo usará essa informação para gerar perguntas relevantes.",
                size="2",
                color="gray",
                style={"fontFamily": "'Quicksand', sans-serif"}
            ),
            
            # Seletor de modelo
            rx.box(
                provider_selector(),
                padding="12px 16px",
                background=COLORS["primary_50"],
                border_radius="8px",
                width="100%"
            ),
            
            # Schema textarea
            rx.box(
                rx.text_area(
                    placeholder="""-- Cole seu schema aqui. Exemplo:
CREATE TABLE clientes (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100),
    email VARCHAR(150),
    cidade VARCHAR(80),
    data_cadastro DATE
);

CREATE TABLE pedidos (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER REFERENCES clientes(id),
    valor_total DECIMAL(12,2),
    data_pedido TIMESTAMP
);""",
                    value=PipelineState.schema_input,
                    on_change=PipelineState.update_schema,
                    style={
                        "width": "100%",
                        "minHeight": "280px",
                        "fontFamily": "'Fira Code', 'Monaco', monospace",
                        "fontSize": "13px",
                        "backgroundColor": "#1e1e1e",
                        "color": "#d4d4d4",
                        "border": f"1px solid {COLORS['primary_100']}",
                        "borderRadius": "8px",
                        "padding": "16px",
                    }
                ),
                width="100%"
            ),
            
            # Opções adicionais
            rx.hstack(
                rx.vstack(
                    rx.text("Número de perguntas", size="2", weight="medium", color=COLORS["basic_800"]),
                    rx.input(
                        value=PipelineState.num_questions.to_string(),
                        on_change=PipelineState.update_num_questions,
                        type="number",
                        min="10",
                        max="100",
                        style={"width": "100px", **INPUT_STYLE}
                    ),
                    spacing="1",
                    align="start"
                ),
                rx.vstack(
                    rx.text("Contexto adicional (opcional)", size="2", weight="medium", color=COLORS["basic_800"]),
                    rx.input(
                        placeholder="Ex: Dados de e-commerce, vendas e clientes",
                        value=PipelineState.context_input,
                        on_change=PipelineState.update_context,
                        style={"width": "380px", **INPUT_STYLE}
                    ),
                    spacing="1",
                    align="start"
                ),
                spacing="6",
                align="end",
                width="100%"
            ),
            
            # Loading indicator
            rx.cond(
                PipelineState.is_loading,
                rx.box(
                    rx.hstack(
                        rx.spinner(size="2", color=COLORS["primary_500"]),
                        rx.vstack(
                            rx.text(
                                "Gerando perguntas...",
                                size="2",
                                weight="medium",
                                color=COLORS["primary_500"]
                            ),
                            rx.text(
                                f"Usando {PipelineState.selected_model}",
                                size="1",
                                color=COLORS["basic_800"]
                            ),
                            spacing="0",
                            align="start"
                        ),
                        spacing="3",
                        align="center"
                    ),
                    padding="16px 20px",
                    background=COLORS["primary_50"],
                    border=f"1px solid {COLORS['primary_100']}",
                    border_radius="8px",
                    width="100%"
                ),
                rx.box()
            ),
            
            # Botão de ação
            rx.hstack(
                rx.button(
                    rx.cond(
                        PipelineState.is_loading,
                        rx.hstack(
                            rx.spinner(size="1"),
                            rx.text("Aguarde..."),
                            spacing="2"
                        ),
                        rx.hstack(
                            rx.icon("sparkles", size=16),
                            rx.text("Gerar Perguntas"),
                            spacing="2"
                        )
                    ),
                    on_click=PipelineState.generate_questions,
                    disabled=PipelineState.is_loading,
                    size="3",
                    style={
                        "background": f"linear-gradient(135deg, {COLORS['primary_500']} 0%, {COLORS['secondary_500']} 100%)",
                        "fontFamily": "'Quicksand', sans-serif",
                        "fontWeight": "600",
                        "cursor": rx.cond(PipelineState.is_loading, "wait", "pointer"),
                        "opacity": rx.cond(PipelineState.is_loading, "0.7", "1")
                    }
                ),
                justify="end",
                width="100%"
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
