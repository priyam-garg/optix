"""Options pricer: Black-Scholes (closed form) and Monte Carlo simulation.

Inputs used throughout:
    S     current price of the underlying
    K     strike price
    T     time to expiry in years (30 days -> 30/365)
    r     risk-free interest rate (e.g. 0.07)
    sigma volatility (e.g. 0.15 for 15%)
"""
import numpy as np
from scipy.stats import norm


def _d1_d2(S, K, T, r, sigma):
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return d1, d2


def black_scholes_call(S, K, T, r, sigma):
    """Return (fair price, delta) of a European call."""
    d1, d2 = _d1_d2(S, K, T, r, sigma)
    price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    delta = norm.cdf(d1)
    return price, delta


def black_scholes_put(S, K, T, r, sigma):
    """Return (fair price, delta) of a European put."""
    d1, d2 = _d1_d2(S, K, T, r, sigma)
    price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    delta = norm.cdf(d1) - 1
    return price, delta


def monte_carlo(S, K, T, r, sigma, n=10_000, kind="call", seed=None):
    """Simulate n prices at expiry, average the payoff, discount to today."""
    rng = np.random.default_rng(seed)
    Z = rng.standard_normal(n)
    ST = S * np.exp((r - 0.5 * sigma**2) * T + sigma * np.sqrt(T) * Z)
    if kind == "call":
        payoff = np.maximum(ST - K, 0)
    else:
        payoff = np.maximum(K - ST, 0)
    return np.exp(-r * T) * payoff.mean()


def monte_carlo_call(S, K, T, r, sigma, n=10_000, seed=None):
    return monte_carlo(S, K, T, r, sigma, n, "call", seed)


def monte_carlo_put(S, K, T, r, sigma, n=10_000, seed=None):
    return monte_carlo(S, K, T, r, sigma, n, "put", seed)


def put_call_parity_gap(S, K, T, r, sigma):
    """(call - put) - (S - K*exp(-rT)). Should be ~0."""
    call, _ = black_scholes_call(S, K, T, r, sigma)
    put, _ = black_scholes_put(S, K, T, r, sigma)
    return (call - put) - (S - K * np.exp(-r * T))


def payoff_profit(prices_at_expiry, K, premium, kind="call"):
    """Profit at expiry for a long option = intrinsic value - premium paid."""
    ST = np.asarray(prices_at_expiry, dtype=float)
    if kind == "call":
        return np.maximum(ST - K, 0) - premium
    return np.maximum(K - ST, 0) - premium


def straddle_profit(prices_at_expiry, K, call_premium, put_premium):
    """Long call + long put at the same strike -> V-shaped profit."""
    return (payoff_profit(prices_at_expiry, K, call_premium, "call")
            + payoff_profit(prices_at_expiry, K, put_premium, "put"))


def plot_payoff(K, call_premium, put_premium, kind="call", low=None, high=None, ax=None):
    """Plot profit vs price at expiry. kind: 'call', 'put' or 'straddle'."""
    import matplotlib.pyplot as plt

    low = low if low is not None else K * 0.9
    high = high if high is not None else K * 1.1
    prices = np.linspace(low, high, 400)
    if kind == "straddle":
        profit = straddle_profit(prices, K, call_premium, put_premium)
    elif kind == "put":
        profit = payoff_profit(prices, K, put_premium, "put")
    else:
        profit = payoff_profit(prices, K, call_premium, "call")

    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 4.5))
    else:
        fig = ax.figure
    ax.plot(prices, profit, color="#1f6feb", linewidth=2)
    ax.fill_between(prices, profit, 0, where=profit >= 0, color="#2da44e", alpha=0.15)
    ax.fill_between(prices, profit, 0, where=profit < 0, color="#cf222e", alpha=0.12)
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.axvline(K, color="gray", linestyle="--", linewidth=0.8, label=f"Strike {K:,.0f}")
    ax.set_xlabel("Price at expiry")
    ax.set_ylabel("Profit / loss")
    ax.set_title(f"Long {kind} payoff at expiry")
    ax.legend(frameon=False)
    ax.grid(alpha=0.3)
    return fig


if __name__ == "__main__":
    # Example: index at 24,000, strike 24,000, 30 days, 7% rate, 15% vol
    S, K, T, r, sigma = 24_000, 24_000, 30 / 365, 0.07, 0.15

    call, call_delta = black_scholes_call(S, K, T, r, sigma)
    put, put_delta = black_scholes_put(S, K, T, r, sigma)
    print(f"Black-Scholes call: {call:.2f}  delta {call_delta:.3f}")
    print(f"Black-Scholes put : {put:.2f}  delta {put_delta:.3f}")
    print(f"Put-call parity gap: {put_call_parity_gap(S, K, T, r, sigma):.2e}")

    print("\nMonte Carlo vs Black-Scholes (call):")
    print(f"{'paths':>8} {'MC price':>10} {'gap %':>8}")
    for n in (100, 1_000, 10_000, 100_000):
        mc = monte_carlo_call(S, K, T, r, sigma, n=n, seed=42)
        print(f"{n:>8,} {mc:>10.2f} {abs(mc - call) / call * 100:>7.2f}%")

    fig = plot_payoff(K, call, put, kind="straddle", low=22_000, high=26_000)
    fig.savefig("payoff.png", dpi=150, bbox_inches="tight")
    print("\nSaved payoff.png")
