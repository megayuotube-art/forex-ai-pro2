import flet as ft
import flet.canvas as cv
import requests
from fundamental_radar import FundamentalRadar

# Ranglar palitrasi (Dark Institutional Theme)
BG_DARK = "#080C14"
CARD_BG = "#111827"
CARD_BORDER = "#1F2937"
ACCENT_GREEN = "#10B981"
ACCENT_RED = "#EF4444"
ACCENT_BLUE = "#3B82F6"
TEXT_PRIMARY = "#F9FAFB"
TEXT_MUTED = "#9CA3AF"


def calculate_trade_setup(closes: list, signal_type: str, pair: str):
    """
    ATR (o'rtacha tebranish) asosida aniq Entry, SL, TP1 va TP2 narxlarini hisoblaydi.
    """
    try:
        current_price = closes[-1]
        diffs = [abs(closes[i] - closes[i - 1]) for i in range(1, len(closes))]
        recent_diffs = diffs[-14:]
        atr = (sum(recent_diffs) / len(recent_diffs)) if len(recent_diffs) >= 5 else current_price * 0.002
    except Exception:
        current_price = 1.0840
        atr = 0.0020

    decimals = 2 if "XAU" in pair or "JPY" in pair else 4

    if "BUY" in signal_type:
        entry = round(current_price, decimals)
        sl = round(entry - (atr * 1.5), decimals)
        tp1 = round(entry + (atr * 2.0), decimals)
        tp2 = round(entry + (atr * 3.5), decimals)
    else:
        entry = round(current_price, decimals)
        sl = round(entry + (atr * 1.5), decimals)
        tp1 = round(entry - (atr * 2.0), decimals)
        tp2 = round(entry - (atr * 3.5), decimals)

    rr_ratio = round(abs(tp2 - entry) / max(abs(entry - sl), 1e-6), 1)
    return {
        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "rr": f"1:{rr_ratio}",
        "decimals": decimals
    }


def build_pro_chart(ohlc_data: list, setup: dict, show_sl_tp: bool = True) -> cv.Canvas:
    """
    Desktop ekran uchun kengaytirilgan shamchalar, AI prognoz konusi va Entry/SL/TP zonalarini chizadi.
    """
    width = 620
    height = 320
    pad_right = 68
    chart_w = width - pad_right
    chart_h = height - 24

    try:
        all_prices = [c["high"] for c in ohlc_data] + [c["low"] for c in ohlc_data]
        if show_sl_tp:
            all_prices.extend([setup["sl"], setup["tp2"], setup["entry"]])
        min_p = min(all_prices)
        max_p = max(all_prices)
    except Exception:
        min_p, max_p = 1.0700, 1.1000

    p_range = max(max_p - min_p, 1e-5)

    def price_to_y(p):
        return 12 + chart_h - ((p - min_p) / p_range) * chart_h

    shapes = []

    # 1. Risk va Reward zonalari
    if show_sl_tp:
        try:
            y_entry = price_to_y(setup["entry"])
            y_sl = price_to_y(setup["sl"])
            y_tp2 = price_to_y(setup["tp2"])

            shapes.append(
                cv.Rect(
                    x=0, y=min(y_entry, y_tp2), width=chart_w, height=abs(y_tp2 - y_entry),
                    paint=ft.Paint(color="#1A10B981", style=ft.PaintingStyle.FILL),
                )
            )
            shapes.append(
                cv.Rect(
                    x=0, y=min(y_entry, y_sl), width=chart_w, height=abs(y_sl - y_entry),
                    paint=ft.Paint(color="#1AEF4444", style=ft.PaintingStyle.FILL),
                )
            )
        except Exception:
            pass

    # 2. Shamchalar (Candlesticks)
    candles_count = len(ohlc_data) if ohlc_data else 1
    step_x = (chart_w * 0.78) / max(candles_count, 1)
    candle_w = max(6, step_x * 0.65)

    for idx, c in enumerate(ohlc_data):
        try:
            cx = idx * step_x + step_x / 2
            is_bull = c["close"] >= c["open"]
            col = ACCENT_GREEN if is_bull else ACCENT_RED

            y_high = price_to_y(c["high"])
            y_low = price_to_y(c["low"])
            y_open = price_to_y(c["open"])
            y_close = price_to_y(c["close"])

            shapes.append(cv.Line(cx, y_high, cx, y_low, paint=ft.Paint(color=col, stroke_width=1.4)))
            shapes.append(
                cv.Rect(
                    x=cx - candle_w / 2, y=min(y_open, y_close), width=candle_w,
                    height=max(2, abs(y_close - y_open)),
                    paint=ft.Paint(color=col, style=ft.PaintingStyle.FILL),
                )
            )
        except Exception:
            continue

    # 3. AI Prognoz Trayektoriyasi
    if ohlc_data:
        try:
            last_x = (candles_count - 1) * step_x + step_x / 2
            last_y = price_to_y(ohlc_data[-1]["close"])
            target_y = price_to_y(setup["tp1"])
            shapes.append(
                cv.Line(
                    last_x, last_y, chart_w - 8, target_y,
                    paint=ft.Paint(color="#38BDF8", stroke_width=2.2, stroke_dash_pattern=[6, 4])
                )
            )
        except Exception:
            pass

    # 4. Entry, SL, TP1, TP2 gorizontal chiziqlari va o'ng o'qdagi narx teglari
    if show_sl_tp:
        levels = [
            ("TP2", setup["tp2"], ACCENT_GREEN),
            ("TP1", setup["tp1"], "#34D399"),
            ("ENTRY", setup["entry"], ACCENT_BLUE),
            ("SL", setup["sl"], ACCENT_RED),
        ]
        for label, val, col in levels:
            try:
                ly = price_to_y(val)
                shapes.append(
                    cv.Line(0, ly, chart_w, ly, paint=ft.Paint(color=col, stroke_width=1.3, stroke_dash_pattern=[5, 3]))
                )
                shapes.append(
                    cv.Rect(
                        x=chart_w + 4, y=ly - 10, width=62, height=20, border_radius=4,
                        paint=ft.Paint(color=col, style=ft.PaintingStyle.FILL)
                    )
                )
                shapes.append(
                    cv.Text(
                        x=chart_w + 8, y=ly - 7, text=f"{val:.{setup['decimals']}f}",
                        style=ft.TextStyle(size=10, weight=ft.FontWeight.BOLD, color="#FFFFFF")
                    )
                )
            except Exception:
                pass

    return cv.Canvas(shapes=shapes, width=width, height=height)


def main(page: ft.Page):
    page.title = "ForexAI 2pro — Desktop Terminal"
    page.bgcolor = BG_DARK
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.window.width = 1120
    page.window.height = 760
    page.window.min_width = 900
    page.window.min_height = 650
    page.scroll = ft.ScrollMode.AUTO

    saved_key = ""
    try:
        saved_key = page.client_storage.get("finnhub_key") or ""
    except Exception:
        saved_key = ""

    state = {
        "pair": "EUR/USD",
        "tf": "1h",
        "api_key": saved_key,
        "show_sl_tp": True,
    }

    api_input = ft.TextField(
        label="Finnhub API Key (Bepul)",
        value=state["api_key"],
        password=True,
        can_reveal_password=True,
        border_color=ACCENT_BLUE,
    )

    def save_api_key(e):
        state["api_key"] = api_input.value.strip()
        try:
            page.client_storage.set("finnhub_key", state["api_key"])
        except Exception:
            pass
        settings_dialog.open = False
        refresh_ui()

    settings_dialog = ft.AlertDialog(
        title=ft.Text("API Sozlamalari", weight=ft.FontWeight.BOLD),
        content=ft.Column([
            ft.Text("Real vaqtda yangiliklar va sentiment tahlili uchun Finnhub.io kalitini kiriting:", size=12, color=TEXT_MUTED),
            api_input,
        ], tight=True),
        actions=[
            ft.TextButton("Bekor qilish", on_click=lambda e: setattr(settings_dialog, "open", False) or page.update()),
            ft.ElevatedButton("Saqlash", bgcolor=ACCENT_BLUE, color="white", on_click=save_api_key),
        ],
    )
    page.overlay.append(settings_dialog)

    content_container = ft.Column(spacing=16)

    def fetch_market_data(pair: str, tf: str):
        ticker_map = {
            "EUR/USD": "EURUSD=X",
            "GBP/USD": "GBPUSD=X",
            "XAU/USD": "GC=F",
            "USD/JPY": "JPY=X",
        }
        symbol = ticker_map.get(pair, "EURUSD=X")
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=5d&interval={tf}"
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                result = data["chart"]["result"][0]
                quote = result["indicators"]["quote"][0]
                opens = quote.get("open", [])
                highs = quote.get("high", [])
                lows = quote.get("low", [])
                closes = quote.get("close", [])

                ohlc = []
                for o, h, l, c in zip(opens, highs, lows, closes):
                    if o is not None and h is not None and l is not None and c is not None:
                        ohlc.append({
                            "open": float(o),
                            "high": float(h),
                            "low": float(l),
                            "close": float(c),
                        })
                if len(ohlc) >= 5:
                    return ohlc[-32:]
        except Exception:
            pass

        base = 1.0840 if pair == "EUR/USD" else 2645.0 if pair == "XAU/USD" else 153.20 if pair == "USD/JPY" else 1.2650
        step = 0.0006 if base < 10 else 0.15 if base < 200 else 2.5
        return [
            {
                "open": base + i * step * 0.3,
                "high": base + (i + 1) * step,
                "low": base - step * 0.5,
                "close": base + (i + 0.6) * step * 0.3,
            }
            for i in range(28)
        ]

    def set_timeframe(tf_val: str):
        state["tf"] = tf_val
        refresh_ui()

    def refresh_ui():
        try:
            content_container.controls.clear()

            radar = FundamentalRadar(state["api_key"])
            cal = radar.check_calendar_shield(state["pair"])
            sent = radar.analyze_news_sentiment(state["pair"])
            cot = radar.get_cot_institutional_flow(state["pair"])

            ohlc = fetch_market_data(state["pair"], state["tf"])
            closes = [x["close"] for x in ohlc]

            tech_prob = 74 if closes[-1] >= closes[-5] else 69
            base_dir = "BUY" if closes[-1] >= closes[-5] else "SELL"
            final_prob = max(50, min(96, tech_prob + sent["score_delta"]))

            if cal["danger"]:
                final_signal = f"KUTISH (XAVF: {cal['title']})"
                sig_color = ACCENT_RED
            else:
                final_signal = f"KUCHLI {base_dir} ({final_prob}%)"
                sig_color = ACCENT_GREEN if base_dir == "BUY" else ACCENT_RED

            setup = calculate_trade_setup(closes, base_dir, state["pair"])

            pair_dropdown = ft.Dropdown(
                value=state["pair"],
                width=140,
                border_color=CARD_BORDER,
                options=[ft.dropdown.Option(p) for p in ["EUR/USD", "GBP/USD", "XAU/USD", "USD/JPY"]],
                on_change=lambda e: state.update({"pair": e.control.value}) or refresh_ui(),
            )

            tf_row = ft.Row([
                ft.ElevatedButton(
                    tf_item.upper(),
                    bgcolor=ACCENT_BLUE if state["tf"] == tf_item else CARD_BORDER,
                    color="white",
                    on_click=lambda e, t=tf_item: set_timeframe(t)
                )
                for tf_item in ["15m", "1h", "4h", "1d"]
            ], spacing=6)

            top_bar = ft.Container(
                bgcolor=CARD_BG,
                border=ft.border.all(1, CARD_BORDER),
                border_radius=14,
                padding=16,
                content=ft.Row([
                    ft.Row([pair_dropdown, tf_row], spacing=16),
                    ft.Row([
                        ft.Text(f"Narx: {closes[-1]:.{setup['decimals']}f}", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.Container(
                            bgcolor=sig_color,
                            padding=ft.padding.symmetric(horizontal=14, vertical=8),
                            border_radius=8,
                            content=ft.Text(final_signal, size=13, weight=ft.FontWeight.BOLD, color="white")
                        )
                    ], spacing=16)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            )

            chart_card = ft.Container(
                expand=2,
                bgcolor=CARD_BG,
                border=ft.border.all(1, CARD_BORDER),
                border_radius=14,
                padding=16,
                content=ft.Column([
                    ft.Row([
                        ft.Text(f"AI Prognoz & SL/TP Grafik ({state['pair']} - {state['tf'].upper()})", size=14, weight=ft.FontWeight.BOLD),
                        ft.Switch(
                            label="SL/TP Zonalari",
                            value=state["show_sl_tp"],
                            active_color=ACCENT_GREEN,
                            on_change=lambda e: state.update({"show_sl_tp": e.control.value}) or refresh_ui()
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    build_pro_chart(ohlc, setup, state["show_sl_tp"]),
                ], spacing=12)
            )

            cal_text = (
                f"⚠️ DIQQAT: {cal['mins_left']} daqiqadan so'ng {cal['currency']} {cal['title']}!"
                if cal["danger"] else "🟢 Kalendar Tinch (Yaqin 1 soatda High Impact yo'q)"
            )

            headlines_col = ft.Column(
                [ft.Text(f"• {h}", size=11, color=TEXT_MUTED, max_lines=2) for h in sent.get("headlines", [])],
                spacing=4
            ) if sent.get("headlines") else ft.Text("Jonli yangiliklar uchun Sozlamalardan Finnhub API kalitini kiriting.", size=11, color=TEXT_MUTED)

            side_panel = ft.Column([
                ft.Container(
                    bgcolor=CARD_BG,
                    border=ft.border.all(1, CARD_BORDER),
                    border_radius=14,
                    padding=16,
                    content=ft.Column([
                        ft.Row([
                            ft.Text("SAVDO REJASI (TRADE SETUP)", size=13, weight=ft.FontWeight.BOLD, color=ACCENT_GREEN),
                            ft.Text(f"R/R: {setup['rr']}", size=13, weight=ft.FontWeight.BOLD, color=ACCENT_BLUE),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=10, color=CARD_BORDER),
                        ft.Row([
                            ft.Column([ft.Text("ENTRY", size=11, color=TEXT_MUTED), ft.Text(f"{setup['entry']}", size=14, weight=ft.FontWeight.BOLD, color=ACCENT_BLUE)]),
                            ft.Column([ft.Text("STOP LOSS", size=11, color=TEXT_MUTED), ft.Text(f"{setup['sl']}", size=14, weight=ft.FontWeight.BOLD, color=ACCENT_RED)]),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row([
                            ft.Column([ft.Text("TP 1 (50%)", size=11, color=TEXT_MUTED), ft.Text(f"{setup['tp1']}", size=14, weight=ft.FontWeight.BOLD, color=ACCENT_GREEN)]),
                            ft.Column([ft.Text("TP 2 (To'liq)", size=11, color=TEXT_MUTED), ft.Text(f"{setup['tp2']}", size=14, weight=ft.FontWeight.BOLD, color=ACCENT_GREEN)]),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ], spacing=10)
                ),
                ft.Container(
                    bgcolor="#1A1118" if cal["danger"] else CARD_BG,
                    border=ft.border.all(1, ACCENT_RED if cal["danger"] else CARD_BORDER),
                    border_radius=14,
                    padding=16,
                    content=ft.Column([
                        ft.Text("FUNDAMENTAL RADAR & HIMOYA", size=12, weight=ft.FontWeight.BOLD, color=ACCENT_BLUE),
                        ft.Text(cal_text, size=12, weight=ft.FontWeight.W_600, color=ACCENT_RED if cal["danger"] else ACCENT_GREEN),
                        ft.Text(f"📰 Yangiliklar foni: {sent['label']}", size=12, color=TEXT_PRIMARY),
                        ft.Text(f"🌍 Geopolitik xavf: {sent['geo_risk']}", size=12, color=TEXT_PRIMARY),
                        ft.Text(f"🏦 CFTC COT Oqim: {cot['long_pct']}% Long ({cot['bias']})", size=12, color=TEXT_MUTED),
                        ft.Divider(height=8, color=CARD_BORDER),
                        ft.Text("So'nggi sarlavhalar:", size=11, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        headlines_col
                    ], spacing=6)
                )
            ], expand=1, spacing=16)

            main_workspace = ft.Row([chart_card, side_panel], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, spacing=16)

            content_container.controls.extend([top_bar, main_workspace])
            page.update()
        except Exception as ex:
            content_container.controls.clear()
            content_container.controls.append(
                ft.Text(f"Xatolik yuz berdi: {ex}", color=ACCENT_RED, size=13)
            )
            page.update()

    header = ft.Row([
        ft.Row([
            ft.Icon(ft.Icons.SHOW_CHART, color=ACCENT_GREEN, size=30),
            ft.Column([
                ft.Text("ForexAI 2pro — Desktop Terminal", size=20, weight=ft.FontWeight.BOLD),
                ft.Text("Institutsional Gibrid Analitika Platformasi", size=12, color=TEXT_MUTED),
            ], spacing=0)
        ]),
        ft.Row([
            ft.IconButton(ft.Icons.REFRESH, tooltip="Yangilash", icon_color=TEXT_PRIMARY, on_click=lambda e: refresh_ui()),
            ft.IconButton(ft.Icons.SETTINGS, tooltip="API Sozlamalari", icon_color=ACCENT_BLUE, on_click=lambda e: setattr(settings_dialog, "open", True) or page.update()),
        ], spacing=4)
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    page.add(header, content_container)
    refresh_ui()


if __name__ == "__main__":
    ft.run(main)
