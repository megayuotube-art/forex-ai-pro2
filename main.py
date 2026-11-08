import flet as ft
import pandas as pd
import numpy as np
import yfinance as yf
import requests

def main(page: ft.Page):
    page.title = "Forex AI Signals"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 20
    page.theme_mode = ft.ThemeMode.DARK

    # Sarlavha
    title_text = ft.Text("Forex AI Pro Signals", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_400)
    
    # Ma'lumot chiqarish maydoni
    status_text = ft.Text("Ma'lumotlar yuklanmoqda...", size=16, color=ft.colors.WHITE70)
    
    # Valyuta juftligi bo'yicha tahlil qilish funksiyasi
    def fetch_data(e):
        status_text.value = "Tahlil qilinmoqda, iltimos kuting..."
        page.update()
        try:
            # yfinance orqali EURUSD ma'lumotlarini olish sinovi
            ticker = yf.Ticker("EURUSD=X")
            df = ticker.history(period="5d")
            
            if not df.empty:
                current_price = df['Close'].iloc[-1]
                sma = df['Close'].rolling(window=3).mean().iloc[-1]
                
                # Oddiy NumPy/Pandas mantiqi
                change = ((current_price - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
                
                signal = "SOTIB OLISH (BUY)" if current_price > sma else "SOTISH (SELL)"
                
                status_text.value = (
                    f"Juftlik: EUR/USD\n"
                    f"Joriy narx: {current_price:.5f}\n"
                    f"O'zgarish: {change:.2f}%\n"
                    f"AI Tavsiyasi: {signal}"
                )
            else:
                status_text.value = "Ma'lumot topilmadi!"
        except Exception as ex:
            status_text.value = f"Xatolik yuz berdi: {str(ex)}"
        
        page.update()

    # Tugma
    analyze_btn = ft.ElevatedButton(
        text="Bozorni tahlil qilish",
        icon=ft.icons.analytics,
        on_click=fetch_data
    )

    # Interfeysni sahifaga qo'shish
    page.add(
        ft.Column(
            [
                title_text,
                ft.Divider(height=20, color=ft.colors.TRANSPARENT),
                status_text,
                ft.Divider(height=20, color=ft.colors.TRANSPARENT),
                analyze_btn
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )

# Dasturni ishga tushirish qismi (AttributeError chiqmasligi uchun eng muhim joyi)
if __name__ == "__main__":
    ft.app(main)
