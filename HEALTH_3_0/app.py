# --- TRAZA VERDE AGUA: RUMBO META 31 DIC (119.9 kg) ---
fig.add_trace(
    go.Scatter(
        x=[df_p['Fecha'].iloc[-1], pd.to_datetime("2026-12-31")],
        y=[df_p['Peso'].iloc[-1], 119.9],
        name="Rumbo 31 Dic (119.9 kg)",
        mode="lines+markers+text",
        line=dict(color="#00FFD1", width=3, dash="dash"),
        marker=dict(size=9, symbol="star", color="#00FFD1"),
        text=["", "119.9 kg"],
        textposition="top left",
        textfont=dict(color="#00FFD1", size=12)
    )
)
