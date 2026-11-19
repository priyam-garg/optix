import streamlit as st

from pricer import (black_scholes_call, black_scholes_put, monte_carlo,
                    plot_payoff, put_call_parity_gap)

st.set_page_config(page_title="Options Pricer", layout="wide")
st.title("Options Pricer")
st.caption("Black-Scholes vs Monte Carlo for European options")

with st.sidebar:
    st.header("Inputs")
    S = st.number_input("Current price (S)", value=24_000.0, min_value=0.01, step=100.0)
    K = st.number_input("Strike (K)", value=24_000.0, min_value=0.01, step=100.0)
    days = st.number_input("Days to expiry", value=30, min_value=1, step=1)
    vol_pct = st.number_input("Volatility (%)", value=15.0, min_value=0.1, step=0.5)
    r_pct = st.number_input("Interest rate (%)", value=7.0, step=0.25)
    kind = st.selectbox("Option type", ["call", "put", "straddle"])
    n = st.select_slider("Monte Carlo paths", options=[100, 1_000, 10_000, 100_000], value=10_000)

T, r, sigma = days / 365, r_pct / 100, vol_pct / 100

call, call_delta = black_scholes_call(S, K, T, r, sigma)
put, put_delta = black_scholes_put(S, K, T, r, sigma)
mc_call = monte_carlo(S, K, T, r, sigma, n, "call")
mc_put = monte_carlo(S, K, T, r, sigma, n, "put")

if kind == "call":
    bs, mc, delta = call, mc_call, call_delta
elif kind == "put":
    bs, mc, delta = put, mc_put, put_delta
else:
    bs, mc, delta = call + put, mc_call + mc_put, call_delta + put_delta

gap = abs(mc - bs) / bs * 100 if bs else 0.0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Black-Scholes price", f"{bs:,.2f}")
c2.metric("Monte Carlo price", f"{mc:,.2f}", f"{gap:.2f}% gap", delta_color="off")
c3.metric("Delta", f"{delta:.3f}")
c4.metric("Put-call parity gap", f"{put_call_parity_gap(S, K, T, r, sigma):.1e}")

fig = plot_payoff(K, call, put, kind=kind, low=min(S, K) * 0.9, high=max(S, K) * 1.1)
st.pyplot(fig)

st.caption("Assumes constant volatility, no dividends, European exercise only.")
