"""Remit Check: Check One Transfer (English and Spanish)."""
import os
import sys
from datetime import date

# Let the app find the remitcheck folder when run from anywhere.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from remitcheck.cost import true_cost, annual_cost
from remitcheck.rates import get_mid_rate

CURRENCY = {"Mexico": "MXN", "India": "INR", "Philippines": "PHP"}
COUNTRY_ES = {"Mexico": "México", "India": "India", "Philippines": "Filipinas"}

# All on-screen text lives here, in both languages. Nothing is typed into the page code.
TEXT = {
    "en": {
        "title": "Remit Check",
        "intro": "Type in what your receipt says. We show what the transfer really cost.",
        "privacy": "We do not store anything you type here.",
        "country": "Which country did you send money to?",
        "date": "Date of the transfer",
        "amount": "Amount you sent, in US dollars",
        "fee": "Fee you were charged, in US dollars",
        "rate": "Exchange rate on your receipt (local currency per dollar)",
        "funding": "How did you pay?",
        "tax_line": "Did your receipt show the 1 percent federal tax as its own line?",
        "tax_amount": "Tax shown on the receipt, in US dollars",
        "freq": "How often do you send money?",
        "button": "Check this transfer",
        "funding_opts": {"cash": "Cash", "money_order": "Money order", "debit_card": "Debit card",
                         "credit_card": "Credit card", "bank_account": "Bank account"},
        "tax_opts": {"yes": "Yes", "no": "No", "unsure": "Not sure"},
        "freq_opts": {"weekly": "Every week", "twice_monthly": "Twice a month",
                      "monthly": "Every month", "few_per_year": "A few times a year"},
        "result": "This transfer cost you **${total:,.2f}**, or **{pct:.1f} percent** of the amount sent.",
        "breakdown": "Fee: ${fee:,.2f}  |  Lost in the exchange rate: ${spread:,.2f}  |  Tax: ${tax:,.2f} ({label})",
        "label_estimated": "estimated", "label_reported": "from your receipt", "label_none": "none",
        "lost": "Compared with the mid-market rate, your family received about **{lost:,.0f} {cur}** less.",
        "annual": "At this pace, about **${annual:,.2f}** a year.",
        "mid_used": "Mid-market rate used: {mid} {cur} per dollar (ECB reference rate for {day}).",
        "tax_note": "Information, not advice: paying from a bank account or debit card avoids this tax.",
        "error": "We could not check this transfer: {msg}",
        "rate_error": "We could not get the exchange rate for that date. Please try again later.",
    },
    "es": {
        "title": "Remit Check",
        "intro": "Escriba lo que dice su recibo. Le mostramos lo que realmente costó el envío.",
        "privacy": "No guardamos nada de lo que escribe aquí.",
        "country": "¿A qué país envió dinero?",
        "date": "Fecha del envío",
        "amount": "Cantidad enviada, en dólares",
        "fee": "Comisión cobrada, en dólares",
        "rate": "Tipo de cambio que aparece en su recibo (moneda local por dólar)",
        "funding": "¿Cómo pagó?",
        "tax_line": "¿Aparece en su recibo el impuesto federal del 1 por ciento como una línea aparte?",
        "tax_amount": "Impuesto que aparece en el recibo, en dólares",
        "freq": "¿Con qué frecuencia envía dinero?",
        "button": "Revisar este envío",
        "funding_opts": {"cash": "Efectivo", "money_order": "Giro postal (money order)",
                         "debit_card": "Tarjeta de débito", "credit_card": "Tarjeta de crédito",
                         "bank_account": "Cuenta bancaria"},
        "tax_opts": {"yes": "Sí", "no": "No", "unsure": "No estoy seguro(a)"},
        "freq_opts": {"weekly": "Cada semana", "twice_monthly": "Dos veces al mes",
                      "monthly": "Cada mes", "few_per_year": "Algunas veces al año"},
        "result": "Este envío le costó **${total:,.2f}**, o **{pct:.1f} por ciento** de lo enviado.",
        "breakdown": "Comisión: ${fee:,.2f}  |  Perdido en el tipo de cambio: ${spread:,.2f}  |  Impuesto: ${tax:,.2f} ({label})",
        "label_estimated": "estimado", "label_reported": "según su recibo", "label_none": "ninguno",
        "lost": "Comparado con el tipo de cambio de mercado, su familia recibió unos **{lost:,.0f} {cur}** menos.",
        "annual": "A este ritmo, unos **${annual:,.2f}** al año.",
        "mid_used": "Tipo de cambio de mercado usado: {mid} {cur} por dólar (tasa de referencia del BCE para {day}).",
        "tax_note": "Información, no consejo: pagar desde una cuenta bancaria o con tarjeta de débito evita este impuesto.",
        "error": "No pudimos revisar este envío: {msg}",
        "rate_error": "No pudimos obtener el tipo de cambio de esa fecha. Inténtelo más tarde.",
    },
}


@st.cache_data(show_spinner=False)
def mid_rate(currency, day):
    """Look up the public mid-market rate. save=False: the app never writes a file."""
    return get_mid_rate(currency, day, save=False)


lang_name = st.sidebar.radio("Language / Idioma", ["English", "Español"])
t = TEXT["en" if lang_name == "English" else "es"]
is_es = lang_name == "Español"

st.title(t["title"])
st.write(t["intro"])
st.caption(t["privacy"])

country = st.selectbox(t["country"], list(CURRENCY), format_func=lambda c: COUNTRY_ES[c] if is_es else c)
day = st.date_input(t["date"], value=date.today(), max_value=date.today())
amount = st.number_input(t["amount"], min_value=1.0, value=300.0, step=10.0)
fee = st.number_input(t["fee"], min_value=0.0, value=4.99, step=0.5)
offered = st.number_input(t["rate"], min_value=0.0001, value=17.20, format="%.4f")
funding = st.selectbox(t["funding"], list(t["funding_opts"]), format_func=lambda k: t["funding_opts"][k])
tax_line = st.selectbox(t["tax_line"], list(t["tax_opts"]), index=1, format_func=lambda k: t["tax_opts"][k])
tax_usd = None
if tax_line == "yes":
    tax_usd = st.number_input(t["tax_amount"], min_value=0.0, value=0.0, step=0.5)
freq = st.selectbox(t["freq"], list(t["freq_opts"]), index=1, format_func=lambda k: t["freq_opts"][k])

if st.button(t["button"]):
    cur = CURRENCY[country]
    try:
        mid = mid_rate(cur, day.isoformat())
    except Exception:
        st.error(t["rate_error"])
    else:
        try:
            r = true_cost(amount, fee, offered, mid, funding, tax_line, tax_usd)
        except ValueError as e:
            st.error(t["error"].format(msg=e))
        else:
            st.success(t["result"].format(total=r["total_cost_usd"], pct=r["total_cost_pct"] * 100))
            st.write(t["breakdown"].format(fee=fee, spread=r["spread_usd"], tax=r["excise_tax_usd"],
                                           label=t["label_" + r["tax_label"]]))
            st.write(t["lost"].format(lost=r["lost_local"], cur=cur))
            st.write(t["annual"].format(annual=annual_cost(r["total_cost_usd"], freq)))
            if r["tax_label"] == "estimated":
                st.info(t["tax_note"])
            st.caption(t["mid_used"].format(mid=mid, cur=cur, day=day.isoformat()))

