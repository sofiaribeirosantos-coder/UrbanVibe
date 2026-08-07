from flask import Flask, render_template, jsonify, request, send_from_directory
from fpdf import FPDF
from flask_cors import CORS
import os, uuid, datetime

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Amostra de produtos
products = [
    {"id": "p1", "name": "Camiseta Urban Logo", "price": 79.90, "gender": "unissex", "style": "casual", "image": "https://via.placeholder.com/300x300?text=Camiseta"},
    {"id": "p2", "name": "Jaqueta Denim", "price": 229.90, "gender": "masculino", "style": "street", "image": "https://via.placeholder.com/300x300?text=Jaqueta"},
    {"id": "p3", "name": "Vestido Floral", "price": 149.90, "gender": "feminino", "style": "casual", "image": "https://via.placeholder.com/300x300?text=Vestido"},
    {"id": "p4", "name": "Calça Cargo", "price": 129.90, "gender": "masculino", "style": "urbano", "image": "https://via.placeholder.com/300x300?text=Calça"},
    {"id": "p5", "name": "Blusa Oversized", "price": 99.90, "gender": "feminino", "style": "street", "image": "https://via.placeholder.com/300x300?text=Blusa"},
    {"id": "p6", "name": "Moletom Com Capuz", "price": 189.90, "gender": "unissex", "style": "athleisure", "image": "https://via.placeholder.com/300x300?text=Moletom"},
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/products')
def api_products():
    return jsonify(products)

def format_currency(v):
    return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

@app.route('/api/checkout', methods=['POST'])
def checkout():
    data = request.json
    cart = data.get('cart', [])
    customer = data.get('customer', {})
    # Validações mínimas
    if not cart or not customer.get('name'):
        return jsonify({"success": False, "message": "Carrinho ou dados do cliente inválidos"}), 400

    # Calcula totais e gera nota
    invoice_id = str(uuid.uuid4())[:8]
    created = datetime.datetime.now()
    subtotal = 0.0
    items = []
    for it in cart:
        prod = next((p for p in products if p['id'] == it['id']), None)
        if not prod:
            continue
        qty = int(it.get('qty', 1))
        line_total = prod['price'] * qty
        subtotal += line_total
        items.append({
            "name": prod['name'],
            "qty": qty,
            "unit": prod['price'],
            "total": line_total
        })
    tax = round(subtotal * 0.10, 2)  # Exemplo: 10% imposto
    total = round(subtotal + tax, 2)

    # Gera PDF simples como nota fiscal/recibo
    os.makedirs('invoices', exist_ok=True)
    filename = f"invoice_{invoice_id}.pdf"
    filepath = os.path.join('invoices', filename)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(0, 8, "UrbanVibe - Nota Fiscal / Recibo", ln=True)
    pdf.ln(2)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 6, f"Nota ID: {invoice_id}", ln=True)
    pdf.cell(0, 6, f"Data: {created.strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.ln(4)
    pdf.cell(0, 6, "Dados do Cliente:", ln=True)
    pdf.cell(0, 6, f"Nome: {customer.get('name')}", ln=True)
    if customer.get('email'):
        pdf.cell(0, 6, f"E-mail: {customer.get('email')}", ln=True)
    if customer.get('cpf_cnpj'):
        pdf.cell(0, 6, f"CPF/CNPJ: {customer.get('cpf_cnpj')}", ln=True)
    if customer.get('address'):
        pdf.cell(0, 6, f"Endereço: {customer.get('address')}", ln=True)
    pdf.ln(4)

    # Itens
    pdf.cell(0, 6, "Itens:", ln=True)
    pdf.ln(1)
    pdf.set_font("Arial", size=9)
    pdf.cell(90, 6, "Descrição", border=1)
    pdf.cell(25, 6, "Qtd", border=1)
    pdf.cell(35, 6, "Vl. Unit.", border=1)
    pdf.cell(40, 6, "Total", border=1, ln=True)
    for it in items:
        pdf.cell(90, 6, it['name'], border=1)
        pdf.cell(25, 6, str(it['qty']), border=1)
        pdf.cell(35, 6, format_currency(it['unit']), border=1)
        pdf.cell(40, 6, format_currency(it['total']), border=1, ln=True)

    pdf.ln(4)
    pdf.cell(0, 6, f"Subtotal: {format_currency(subtotal)}", ln=True)
    pdf.cell(0, 6, f"Impostos (exemplo 10%): {format_currency(tax)}", ln=True)
    pdf.cell(0, 6, f"Total: {format_currency(total)}", ln=True)
    pdf.ln(6)
    pdf.cell(0, 6, "Observações: Esta é uma nota/recibo gerado pelo sistema UrbanVibe. Para NF-e oficial integre com um provedor fiscal (SEFAZ/PJ).", ln=True)

    pdf.output(filepath)

    invoice_url = f"/invoices/{filename}"
    return jsonify({"success": True, "invoice_url": invoice_url, "invoice_id": invoice_id})

@app.route('/invoices/<path:filename>')
def serve_invoice(filename):
    return send_from_directory('invoices', filename, as_attachment=True)

if __name__ == '__main__':
    os.makedirs('invoices', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
