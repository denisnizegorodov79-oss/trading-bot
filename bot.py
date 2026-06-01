import os
import telebot
from telebot.types import ReplyKeyboardMarkup
import yfinance as yf
import time
import threading
import csv
import io
import json
import os
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

TOKEN = "8948879603:TOKEN = os.environ.get("TOKEN")"
bot = telebot.TeleBot(TOKEN)

INITIAL_BALANCE = 500.0
balance = INITIAL_BALANCE

CSV_TRADES = "trades_log.csv"
CSV_LEARNING = "learning_data.csv"
file_lock = threading.Lock()
trading_active = True

SYMBOLS_LIST = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD"]

CONFIG = {
    "max_daily_trades": 10,
    "risk_per_trade": 0.02,
    "min_confidence": 0.6,
    "learning_mode": True,
    "symbols": SYMBOLS_LIST
}

class TradingAgent:
    def __init__(self):
        self.learning_data = []
        self.successful_patterns = {}
        self.failed_patterns = {}
        self.daily_trades = 0
        self.last_trade_day = datetime.now().day
        self.load_learning_data()
    
    def load_learning_data(self):
        if os.path.exists(CSV_LEARNING):
            df = pd.read_csv(CSV_LEARNING)
            self.learning_data = df.to_dict('records')
            for trade in self.learning_data:
                key = f"{trade.get('symbol')}_{trade.get('direction')}_{trade.get('rsi_range')}_{trade.get('trend')}"
                if trade.get('result') == 'WIN':
                    self.successful_patterns[key] = self.successful_patterns.get(key, 0) + 1
                elif trade.get('result') == 'LOSS':
                    self.failed_patterns[key] = self.failed_patterns.get(key, 0) + 1
    
    def _get_rsi_range(self, rsi):
        if rsi < 30: return "oversold"
        elif rsi > 70: return "overbought"
        elif rsi < 45: return "weak"
        elif rsi > 55: return "strong"
        return "neutral"
    
    def _get_trend(self, ema_diff):
        if ema_diff > 0.02: return "strong_up"
        elif ema_diff > 0: return "up"
        elif ema_diff < -0.02: return "strong_down"
        elif ema_diff < 0: return "down"
        return "sideways"
    
    def analyze_and_decide(self, signal_data):
        direction = signal_data.get('direction')
        details = signal_data.get('details', {})
        rsi = details.get('rsi', 50)
        volume_ratio = details.get('volume_ratio', 1)
        pinbar = details.get('pinbar')
        
        confidence = 0.5
        reason_parts = []
        
        if direction == "LONG":
            confidence += 0.15
            reason_parts.append("бычий сигнал")
            if rsi < 40:
                confidence += 0.1
                reason_parts.append(f"RSI {rsi:.0f} (хорошо для покупки)")
            if volume_ratio > 1.2:
                confidence += 0.1
                reason_parts.append(f"объём выше среднего в {volume_ratio:.1f}x")
            if pinbar == 'bullish':
                confidence += 0.15
                reason_parts.append("бычий пин-бар")
        elif direction == "SHORT":
            confidence += 0.15
            reason_parts.append("медвежий сигнал")
            if rsi > 60:
                confidence += 0.1
                reason_parts.append(f"RSI {rsi:.0f} (хорошо для продажи)")
            if volume_ratio > 1.2:
                confidence += 0.1
                reason_parts.append(f"объём выше среднего в {volume_ratio:.1f}x")
            if pinbar == 'bearish':
                confidence += 0.15
                reason_parts.append("медвежий пин-бар")
        
        reason = ", ".join(reason_parts) if reason_parts else "нейтральные условия"
        
        decision = {
            "action": "HOLD" if confidence < CONFIG["min_confidence"] or direction not in ["LONG", "SHORT"] else direction,
            "confidence": round(confidence, 2),
            "reason": reason
        }
        return decision
    
    def reset_daily_counter(self):
        today = datetime.now().day
        if today != self.last_trade_day:
            self.daily_trades = 0
            self.last_trade_day = today

agent = TradingAgent()

def get_hourly_data(symbol, period="60d", interval="1h"):
    df = yf.Ticker(symbol).history(period=period, interval=interval)
    return df if not df.empty else None

def get_daily_data(symbol, period="1y", interval="1d"):
    df = yf.Ticker(symbol).history(period=period, interval=interval)
    return df if not df.empty else None

def calculate_poc(df, bars=100):
    if df is None or len(df) < bars:
        return None
    sub = df.iloc[-bars:].copy()
    prices = sub['Close'].values
    volumes = sub['Volume'].values
    if volumes.sum() == 0:
        return None
    hist, bins = np.histogram(prices, bins=50, weights=volumes)
    max_idx = np.argmax(hist)
    return (bins[max_idx] + bins[max_idx+1]) / 2.0

def calculate_volume_ratio(df, period=24):
    if df is None or len(df) < period+1:
        return 1.0
    last = df['Volume'].iloc[-1]
    avg = df['Volume'].iloc[-period-1:-1].mean()
    return last / avg if avg != 0 else 1.0

def detect_pinbar(df):
    if df is None or len(df) < 1:
        return None
    last = df.iloc[-1]
    body = abs(last['Close'] - last['Open'])
    if body == 0:
        return None
    upper = last['High'] - max(last['Close'], last['Open'])
    lower = min(last['Close'], last['Open']) - last['Low']
    if upper >= 2*body and lower < body:
        return 'bearish'
    if lower >= 2*body and upper < body:
        return 'bullish'
    return None

def get_medallion_prediction(symbol=None):
    if symbol is None:
        symbol = "BTC-USD"
    
    daily = get_daily_data(symbol)
    if daily is None or len(daily) < 200:
        return "НЕТ ДАННЫХ", None, None, {}
    daily['EMA200'] = daily['Close'].ewm(span=200, adjust=False).mean()
    last_daily = daily.iloc[-1]
    trend_up = last_daily['Close'] > last_daily['EMA200']
    trend_down = last_daily['Close'] < last_daily['EMA200']
    
    hourly = get_hourly_data(symbol)
    if hourly is None or len(hourly) < 50:
        return "НЕТ ДАННЫХ", None, None, {}
    price = hourly['Close'].iloc[-1]
    
    poc = calculate_poc(hourly, bars=100)
    above_poc = price > poc if poc else False
    below_poc = price < poc if poc else False
    vol_ratio = calculate_volume_ratio(hourly)
    vol_surge = vol_ratio > 1.0
    
    closes = hourly['Close']
    delta = closes.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14, min_periods=14).mean()
    avg_loss = loss.rolling(window=14, min_periods=14).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs)).iloc[-1]
    
    rsi_ok_long = rsi < 65
    rsi_ok_short = rsi > 35
    pin = detect_pinbar(hourly)
    
    long_cond = trend_up and above_poc and vol_surge and rsi_ok_long
    short_cond = trend_down and below_poc and vol_surge and rsi_ok_short
    
    if long_cond:
        signal, direction = "LONG 🟢", "LONG"
    elif short_cond:
        signal, direction = "SHORT 🔴", "SHORT"
    else:
        signal, direction = "НАБЛЮДЕНИЕ ⏳", None
    
    details = {
        "price": price,
        "ema200": last_daily['EMA200'],
        "poc": poc,
        "volume_ratio": vol_ratio,
        "rsi": rsi,
        "pinbar": pin
    }
    return signal, direction, price, details

def calc_sl_tp(symbol, direction, entry_price):
    hourly = get_hourly_data(symbol)
    if hourly is None or len(hourly) < 20:
        sl_pct = 0.02
    else:
        returns = hourly['Close'].pct_change().dropna()
        std = returns.iloc[-20:].std() if len(returns) >= 20 else 0.02
        sl_pct = 2.0 * max(std, 0.005)
    
    if direction == "LONG":
        sl = entry_price * (1 - sl_pct)
        tp = entry_price * (1 + sl_pct * 2.5)
    else:
        sl = entry_price * (1 + sl_pct)
        tp = entry_price * (1 - sl_pct * 2.5)
    return sl, tp

class TradeManager:
    def __init__(self):
        self.active_trades = []
        self.trade_history = []
        self.load_trades()
    
    def load_trades(self):
        if os.path.exists(CSV_TRADES):
            df = pd.read_csv(CSV_TRADES)
            self.trade_history = df.to_dict('records')
            self.active_trades = [t for t in self.trade_history if t.get('status') == 'OPEN']
    
    def save_trade(self, trade):
        file_exists = os.path.exists(CSV_TRADES)
        with open(CSV_TRADES, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=trade.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(trade)
    
    def open_trade(self, symbol, direction, price, sl, tp, decision):
        global balance
        trade_id = len(self.trade_history) + 1
        risk_amount = balance * CONFIG["risk_per_trade"]
        risk_per_share = abs(price - sl)
        if risk_per_share <= 0:
            return None
        shares = risk_amount / risk_per_share
        max_investment = balance * 0.25
        position_value = shares * price
        if position_value > max_investment:
            shares = max_investment / price
        position_size = round(shares, 6)
        position_value = position_size * price
        
        if position_value > balance:
            position_size = balance / price * 0.9
            position_value = position_size * price
        
        if position_value <= 0 or position_size <= 0:
            return None
        
        balance -= position_value
        
        trade = {
            "id": trade_id,
            "symbol": symbol,
            "direction": direction,
            "open_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "open_price": price,
            "stop_loss": sl,
            "take_profit": tp,
            "position_size": position_size,
            "position_value": position_value,
            "status": "OPEN",
            "decision_confidence": decision.get("confidence"),
            "decision_reason": decision.get("reason")
        }
        self.trade_history.append(trade)
        self.active_trades.append(trade)
        self.save_trade(trade)
        return trade
    
    def close_trade(self, trade, close_price, reason):
        global balance
        if trade['status'] != 'OPEN':
            return None
        
        direction = trade['direction']
        entry = trade['open_price']
        size = trade['position_size']
        
        if direction == "LONG":
            pnl = (close_price - entry) * size
            pnl_pct = (close_price - entry) / entry * 100
        else:
            pnl = (entry - close_price) * size
            pnl_pct = (entry - close_price) / entry * 100
        
        balance += (entry * size) + pnl
        
        trade['status'] = "WIN" if pnl > 0 else "LOSS"
        trade['close_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        trade['close_price'] = close_price
        trade['pnl'] = pnl
        trade['pnl_pct'] = pnl_pct
        trade['close_reason'] = reason
        self.active_trades.remove(trade)
        self._update_csv()
        return trade
    
    def _update_csv(self):
        with open(CSV_TRADES, 'w', newline='') as f:
            if self.trade_history:
                writer = csv.DictWriter(f, fieldnames=self.trade_history[0].keys())
                writer.writeheader()
                writer.writerows(self.trade_history)

trade_manager = TradeManager()
ADMIN_CHAT_ID = None

def monitor_trades():
    global trading_active
    while trading_active:
        try:
            if not trade_manager.active_trades:
                time.sleep(60)
                continue
            for trade in trade_manager.active_trades[:]:
                symbol = trade['symbol']
                sl = trade['stop_loss']
                tp = trade['take_profit']
                direction = trade['direction']
                data = yf.Ticker(symbol).history(period="5m", interval="1m")
                if data.empty:
                    continue
                price = data['Close'].iloc[-1]
                closed = False
                reason = ""
                if direction == "LONG":
                    if price >= tp:
                        closed, reason = True, "TP"
                    elif price <= sl:
                        closed, reason = True, "SL"
                else:
                    if price <= tp:
                        closed, reason = True, "TP"
                    elif price >= sl:
                        closed, reason = True, "SL"
                if closed:
                    trade_manager.close_trade(trade, price, reason)
                    try:
                        msg = f"🔔 Сделка #{trade['id']} {direction} закрыта по {reason}!\n💰 PnL: {trade.get('pnl_pct', 0):.2f}%\n💵 Баланс: ${balance:.2f}"
                        bot.send_message(ADMIN_CHAT_ID, msg)
                    except:
                        pass
            time.sleep(60)
        except Exception as e:
            print(f"Monitor error: {e}")
            time.sleep(60)

def autonomous_trader():
    global trading_active, balance
    while trading_active:
        try:
            agent.reset_daily_counter()
            if agent.daily_trades >= CONFIG["max_daily_trades"]:
                time.sleep(300)
                continue
            for symbol in CONFIG["symbols"]:
                if agent.daily_trades >= CONFIG["max_daily_trades"]:
                    break
                signal, direction, price, details = get_medallion_prediction(symbol)
                if direction is None:
                    continue
                signal_data = {
                    "symbol": symbol,
                    "direction": direction,
                    "price": price,
                    "details": details
                }
                decision = agent.analyze_and_decide(signal_data)
                if decision["action"] in ["LONG", "SHORT"] and decision["confidence"] >= CONFIG["min_confidence"]:
                    sl, tp = calc_sl_tp(symbol, decision["action"], price)
                    trade = trade_manager.open_trade(symbol, decision["action"], price, sl, tp, decision)
                    if trade:
                        agent.daily_trades += 1
                        try:
                            msg = (f"🤖 *АВТОНОМНАЯ СДЕЛКА #{trade['id']}*\n"
                                   f"📌 {symbol} - {decision['action']}\n"
                                   f"💰 Цена: ${price:.2f}\n"
                                   f"🎯 SL: ${sl:.2f} | TP: ${tp:.2f}\n"
                                   f"📊 Уверенность: {decision['confidence']:.0%}\n"
                                   f"💭 Причина: {decision['reason']}\n"
                                   f"💵 Баланс: ${balance:.2f}")
                            bot.send_message(ADMIN_CHAT_ID, msg, parse_mode='Markdown')
                        except:
                            pass
                        time.sleep(10)
            time.sleep(300)
        except Exception as e:
            print(f"Trader error: {e}")
            time.sleep(60)

def main_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("📊 СИГНАЛ", "🤖 АВТО-ТРЕЙДИНГ")
    kb.add("💰 БАЛАНС", "📈 СТАТИСТИКА")
    kb.add("🏆 PERFORMANCE", "📜 ИСТОРИЯ")
    kb.add("📉 ГРАФИК", "🧠 ОБУЧЕНИЕ")
    kb.add("❌ ЗАКРЫТЬ ВСЕ", "⚙️ НАСТРОЙКИ")
    return kb

@bot.message_handler(commands=['start'])
def start_cmd(msg):
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID is None:
        ADMIN_CHAT_ID = msg.chat.id
    bot.send_message(msg.chat.id,
        "🤖 *Самообучающийся Торговый Бот*\n\n"
        f"💰 Виртуальный баланс: **${balance:.2f}**\n\n"
        "🔹 *Авто-трейдинг* — бот торгует сам\n"
        "🔹 *Сигнал* — ручной анализ\n"
        "🔹 *Обучение* — просмотр успешных паттернов",
        parse_mode='Markdown', reply_markup=main_keyboard())

@bot.message_handler(func=lambda m: m.text == "📊 СИГНАЛ")
def signal_btn(msg):
    signal, direction, price, details = get_medallion_prediction("BTC-USD")
    if signal == "НЕТ ДАННЫХ":
        text = "❌ Нет данных"
    else:
        signal_data = {"symbol": "BTC-USD", "direction": direction, "price": price, "details": details}
        decision = agent.analyze_and_decide(signal_data)
        text = (f"📊 *Сигнал для BTC-USD*\n"
                f"💰 Цена: ${details['price']:.2f}\n"
                f"📈 EMA200: ${details['ema200']:.2f}\n"
                f"🎯 POC: ${details['poc']:.2f}\n"
                f"📊 Volume Ratio: {details['volume_ratio']:.2f}\n"
                f"📉 RSI: {details['rsi']:.1f}\n\n"
                f"🧠 *Решение:* {signal}\n"
                f"🎯 *Уверенность:* {decision['confidence']:.0%}\n"
                f"💭 *Причина:* {decision['reason']}")
    bot.reply_to(msg, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "🤖 АВТО-ТРЕЙДИНГ")
def auto_trade_btn(msg):
    global trading_active
    trading_active = not trading_active
    status = "ЗАПУЩЕН" if trading_active else "ОСТАНОВЛЕН"
    bot.reply_to(msg, f"🤖 Авто-трейдинг *{status}*", parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "💰 БАЛАНС")
def balance_btn(msg):
    open_value = 0
    for trade in trade_manager.active_trades:
        data = yf.Ticker(trade['symbol']).history(period="5m", interval="1m")
        if not data.empty:
            current_price = data['Close'].iloc[-1]
            if trade['direction'] == "LONG":
                open_value += (current_price - trade['open_price']) * trade['position_size']
            else:
                open_value += (trade['open_price'] - current_price) * trade['position_size']
    total_equity = balance + open_value
    total_pnl = total_equity - INITIAL_BALANCE
    total_pnl_pct = (total_pnl / INITIAL_BALANCE) * 100
    text = (f"💰 *Виртуальный баланс*\n\n"
            f"💵 Свободные средства: **${balance:.2f}**\n"
            f"📊 Плавающая прибыль: **${open_value:+.2f}**\n"
            f"💎 Общий капитал: **${total_equity:.2f}**\n\n"
            f"📈 Общий PnL: **${total_pnl:+.2f}** ({total_pnl_pct:+.1f}%)")
    bot.reply_to(msg, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "📈 СТАТИСТИКА")
def stat_btn(msg):
    closed = [t for t in trade_manager.trade_history if t.get('status') in ['WIN', 'LOSS']]
    if not closed:
        bot.reply_to(msg, "Нет закрытых сделок.")
        return
    wins = [t for t in closed if t['status'] == 'WIN']
    winrate = len(wins) / len(closed) * 100
    total_pnl = sum(t.get('pnl', 0) for t in closed)
    text = (f"📈 *Статистика*\n\n"
            f"Всего сделок: {len(closed)}\n"
            f"✅ Выигрышей: {len(wins)}\n"
            f"❌ Проигрышей: {len(closed)-len(wins)}\n"
            f"🏆 Win Rate: {winrate:.1f}%\n"
            f"💰 Общий PnL: ${total_pnl:+.2f}")
    bot.reply_to(msg, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "🏆 PERFORMANCE")
def perf_btn(msg):
    closed = [t for t in trade_manager.trade_history if t.get('status') in ['WIN', 'LOSS']]
    if len(closed) < 2:
        bot.reply_to(msg, "Недостаточно данных.")
        return
    wins_pnl = [t.get('pnl', 0) for t in closed if t['status'] == 'WIN']
    losses_pnl = [abs(t.get('pnl', 0)) for t in closed if t['status'] == 'LOSS']
    total_win = sum(wins_pnl)
    total_loss = sum(losses_pnl)
    pf = total_win / total_loss if total_loss > 0 else float('inf')
    avg_trade = (total_win - total_loss) / len(closed)
    text = (f"🏆 *Performance*\n\n"
            f"Profit Factor: {pf:.2f}\n"
            f"Средняя сделка: ${avg_trade:+.2f}\n"
            f"Всего сделок: {len(closed)}")
    bot.reply_to(msg, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "📜 ИСТОРИЯ")
def history_btn(msg):
    last_trades = trade_manager.trade_history[-10:]
    if not last_trades:
        bot.reply_to(msg, "Нет сделок.")
        return
    text = "📜 *Последние 10 сделок:*\n\n"
    for t in reversed(last_trades):
        icon = "✅" if t.get('status') == 'WIN' else "❌" if t.get('status') == 'LOSS' else "🟡"
        pnl = t.get('pnl', 0)
        text += f"{icon} #{t['id']} {t['direction']} {t['symbol']} | PnL: ${pnl:+.2f}\n"
    bot.reply_to(msg, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "📉 ГРАФИК")
def chart_btn(msg):
    closed = [t for t in trade_manager.trade_history if t.get('status') in ['WIN', 'LOSS']]
    if len(closed) < 2:
        bot.reply_to(msg, "Недостаточно данных.")
        return
    cumulative = []
    running = 0
    for t in closed:
        running += t.get('pnl', 0)
        cumulative.append(running)
    plt.figure(figsize=(10, 5))
    plt.plot(range(len(cumulative)), cumulative, marker='o', color='blue', linewidth=2)
    plt.title("Equity Curve")
    plt.xlabel("Номер сделки")
    plt.ylabel("PnL ($)")
    plt.grid(True, alpha=0.3)
    plt.axhline(y=0, color='red', linestyle='--', alpha=0.5)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    bot.send_photo(msg.chat.id, buf)
    plt.close()

@bot.message_handler(func=lambda m: m.text == "🧠 ОБУЧЕНИЕ")
def learning_btn(msg):
    text = (f"🧠 *Обучение агента*\n\n"
            f"📊 Успешных паттернов: {len(agent.successful_patterns)}\n"
            f"📉 Неудачных паттернов: {len(agent.failed_patterns)}\n\n"
            f"🏆 *Лучшие паттерны:*\n")
    best = sorted(agent.successful_patterns.items(), key=lambda x: x[1], reverse=True)[:5]
    for pattern, count in best:
        if count > 2:
            text += f"✅ {pattern}: {count} побед\n"
    if not best:
        text += "Пока нет данных. Больше сделок = лучше обучение!"
    bot.reply_to(msg, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "❌ ЗАКРЫТЬ ВСЕ")
def close_all_btn(msg):
    for trade in trade_manager.active_trades[:]:
        data = yf.Ticker(trade['symbol']).history(period="5m", interval="1m")
        price = data['Close'].iloc[-1] if not data.empty else trade['open_price']
        trade_manager.close_trade(trade, price, "MANUAL")
    bot.reply_to(msg, "✅ Все открытые сделки закрыты.")

@bot.message_handler(func=lambda m: m.text == "⚙️ НАСТРОЙКИ")
def settings_btn(msg):
    text = (f"⚙️ *Текущие настройки*\n\n"
            f"Макс. сделок в день: {CONFIG['max_daily_trades']}\n"
            f"Риск на сделку: {CONFIG['risk_per_trade']*100:.0f}%\n"
            f"Мин. уверенность: {CONFIG['min_confidence']:.0%}")
    bot.reply_to(msg, text, parse_mode='Markdown')

def run_bot():
    print("✅ Бот запущен!")
    bot.infinity_polling()

threading.Thread(target=monitor_trades, daemon=True).start()
threading.Thread(target=autonomous_trader, daemon=True).start()
threading.Thread(target=run_bot, daemon=True).start()

print("🚀 Самообучающийся бот работает!")
print(f"💰 Начальный баланс: ${INITIAL_BALANCE}")

while True:
    time.sleep(1)
