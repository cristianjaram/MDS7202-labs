import gradio as gr
import requests
import json

API_URL = "http://backend:8000"

def load_customers():
    try:
        response = requests.get(f"{API_URL}/customers", timeout=10)
        if response.status_code == 200:
            data = response.json()
            customers = [f"{c['customer_id']} ({c['customer_type']})" for c in data['customers']]
            print(f"Clientes cargados: {len(customers)}")
            return customers
        print(f"Error al cargar clientes: status {response.status_code}")
        return ["Error: No se pudieron cargar los clientes"]
    except Exception as e:
        print(f"Excepción al cargar clientes: {e}")
        return ["Error: No se pudo conectar con el backend"]

def load_customer_products(customer_display):
    if not customer_display or customer_display.startswith("Error"):
        return gr.update(choices=[], value=None)

    try:
        customer_id = customer_display.split()[0]
        print(f"Cargando productos para cliente: {customer_id}")
        response = requests.get(f"{API_URL}/customers/{customer_id}/products", timeout=10)
        if response.status_code == 200:
            data = response.json()
            products = [
                f"{p['product_id']} - {p['brand']} {p['sub_category']}"
                for p in data['products']
            ]
            print(f"Productos cargados: {len(products)}")
            return gr.update(choices=products, value=products[0] if products else None)
        print(f"Error al cargar productos: status {response.status_code}")
        return gr.update(choices=["Error: No se encontraron productos"], value=None)
    except Exception as e:
        print(f"Excepción al cargar productos: {e}")
        return gr.update(choices=["Error: No se pudo cargar"], value=None)

def predict_purchase(customer_display, product_display):
    if not customer_display or not product_display:
        return "⚠️ Por favor selecciona un cliente y un producto"

    try:
        customer_id = customer_display.split()[0]
        product_id = product_display.split()[0]

        response = requests.get(
            f"{API_URL}/predict/customer/{customer_id}/product/{product_id}",
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            probability = result["probability"]
            will_purchase = result["will_purchase"]
            prediction_date = result["prediction_date"]

            if result["prediction"] == 1:
                color = "🟢"
                message = f"""{color} **{will_purchase}**

**Probabilidad de compra:** {probability:.2%}

**Cliente:** {customer_id}
**Producto:** {product_id}
**Fecha predicción:** {prediction_date}
"""
            else:
                color = "🔴"
                message = f"""{color} **{will_purchase}**

**Probabilidad de compra:** {probability:.2%}

**Cliente:** {customer_id}
**Producto:** {product_id}
**Fecha predicción:** {prediction_date}
"""

            return message
        elif response.status_code == 404:
            return f"❌ No se encontró predicción para esta combinación cliente-producto"
        else:
            return f"❌ Error: {response.status_code} - {response.text}"

    except requests.exceptions.ConnectionError:
        return "❌ No se puede conectar con el servidor. Verifica que el backend esté corriendo."
    except Exception as e:
        return f"❌ Error: {str(e)}"

def show_top_predictions(n):
    try:
        response = requests.get(f"{API_URL}/predictions/top/{n}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            top_preds = data['top_predictions']

            if not top_preds:
                return "No hay predicciones disponibles"

            table = "| Cliente | Producto | Probabilidad | Predicción |\n"
            table += "|---------|----------|--------------|------------|\n"
            for pred in top_preds[:20]:
                table += f"| {pred['customer_id']} | {pred['product_id']} | {pred['probability']:.2%} | {'✅' if pred['prediction'] == 1 else '❌'} |\n"

            return f"## Top {n} predicciones\n\n{table}\n\nTotal: {len(top_preds)} predicciones"
        else:
            return f"Error: {response.status_code}"
    except:
        return "❌ No se puede conectar con el backend"

def check_health():
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            status = "✅ Conectado" if data["model_loaded"] else "⚠️ Modelo no cargado"
            return f"{status}\n\nEstado: {data['status']}\nModelo: {data['model_path']}"
        else:
            return f"❌ Error: {response.status_code}"
    except:
        return "❌ No se puede conectar con el backend"

with gr.Blocks(title="SodAI Drinks - Predicción de Pedidos", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🥤 SodAI Drinks - Sistema de Predicción de Pedidos

    Predice si un cliente realizará un pedido de un producto específico la próxima semana.

    ## Instrucciones de uso:
    1. Selecciona un cliente de la lista
    2. Selecciona un producto que el cliente ha comprado anteriormente
    3. Haz clic en "Predecir" para obtener la probabilidad de compra
    """)

    with gr.Tab("Predicción Individual"):
        with gr.Row():
            with gr.Column():
                customer_dropdown = gr.Dropdown(
                    choices=load_customers(),
                    label="Selecciona un Cliente",
                    interactive=True
                )
                product_dropdown = gr.Dropdown(
                    choices=[],
                    label="Selecciona un Producto",
                    interactive=True
                )

        with gr.Row():
            predict_btn = gr.Button("🔮 Predecir", variant="primary", size="lg")
            health_btn = gr.Button("🔍 Verificar Conexión", size="lg")

        with gr.Row():
            output = gr.Markdown(label="Resultado")

        customer_dropdown.change(
            fn=load_customer_products,
            inputs=[customer_dropdown],
            outputs=[product_dropdown]
        )

        predict_btn.click(
            fn=predict_purchase,
            inputs=[customer_dropdown, product_dropdown],
            outputs=output
        )

        health_btn.click(fn=check_health, outputs=output)

    with gr.Tab("Top Predicciones"):
        gr.Markdown("### Muestra las predicciones con mayor probabilidad de compra")

        n_slider = gr.Slider(minimum=10, maximum=500, value=100, step=10,
                            label="Número de predicciones")
        top_btn = gr.Button("📊 Mostrar Top Predicciones", variant="primary")
        top_output = gr.Markdown()

        top_btn.click(
            fn=show_top_predictions,
            inputs=[n_slider],
            outputs=top_output
        )

    gr.Markdown("""
    ---
    ### ℹ️ Acerca del Modelo

    - **Algoritmo**: LightGBM con SMOTE para balanceo de clases
    - **Optimización**: Optuna (búsqueda bayesiana de hiperparámetros)
    - **Tracking**: MLflow para registro de experimentos

    El modelo predice la probabilidad de que un cliente compre un producto específico
    basándose en su historial de compras y características del producto.
    """)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
