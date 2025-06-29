import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tkinter as tk
from tkinter import ttk
from tkintermapview import TkinterMapView
import ttkbootstrap as tb
import pandas as pd
import math
import joblib

def formatar_reais(valor):
    try:
        return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    except Exception:
        return f"R$ {valor}"

# Aplicativo principal para visualização e análise de imóveis com interface gráfica e mapa interativo
class ImovelApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Propriedades com Mapa")

        # Carrega o dataset de imóveis e prepara a lista de imóveis para exibição
        csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/dataset_com_gbm.csv"))
        self.df = pd.read_csv(csv_path)
        if self.df['Preço'].dtype != float:
            self.df['Preço'] = (
                self.df['Preço']
                .astype(str)
                .str.replace(r'[^\d.]', '', regex=True)
                .replace('', '0')
                .astype(float)
            )
        self.lista_imoveis = self.df.copy()

        # Monta a interface gráfica principal (combobox, botões, frames)
        frame_top = tk.Frame(root)
        frame_top.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        control_frame = tk.Frame(frame_top)
        control_frame.pack(expand=True)

        self.combo_imovel = ttk.Combobox(
            control_frame,
            values=[f"Imovel {i+1}" for i in range(len(self.lista_imoveis))],
            width=30
        )
        self.combo_imovel.set("Selecione o imóvel")
        self.combo_imovel.pack(side=tk.LEFT, padx=5)

        self.btn_detalhes = tk.Button(
            control_frame,
            text="Mostrar Detalhes",
            command=self.exibir_detalhes
        )
        self.btn_detalhes.pack(side=tk.LEFT, padx=5)

        self.btn_recomendar = tk.Button(
            control_frame,
            text="Recomendar Bairro e Imóvel",
            command=self.abrir_formulario_recomendacao
        )
        self.btn_recomendar.pack(side=tk.LEFT, padx=5)

        self.btn_avaliar = tk.Button(
            control_frame,
            text="Avaliar Preço de Imóvel",
            command=self.abrir_formulario_avaliacao
        )
        self.btn_avaliar.pack(side=tk.LEFT, padx=5)

        # Área do mapa interativo
        frame_map = tk.Frame(root)
        frame_map.pack(fill=tk.BOTH, expand=True)
        self.map_widget = TkinterMapView(frame_map, corner_radius=0)
        self.map_widget.set_position(-37.8136, 144.9631)
        self.map_widget.set_zoom(10)
        self.map_widget.pack(fill=tk.BOTH, expand=True)

        # Área para exibir informações detalhadas do imóvel selecionado
        self.info_frame = tk.Frame(root)                 
        self.info_frame.pack(fill=tk.BOTH, padx=10, pady=5)

    # Exibe detalhes do imóvel selecionado e destaca no mapa
    def exibir_detalhes(self):
        escolha = self.combo_imovel.get()
        if not escolha.startswith("Imovel "):
            self.label_info.config(text="Selecione um imóvel válido.")
            return

        idx = int(escolha.replace("Imovel ", "")) - 1
        dados = self.lista_imoveis.iloc[idx]
        lat = dados.get("Latitude", "")
        lon = dados.get("Longitude", "")

        def safe_str(val):
            return "N/A" if pd.isnull(val) else str(val)

        info = [
            f"Subúrbio: {safe_str(dados.get('Subúrbio'))}",
            f"Endereço: {safe_str(dados.get('Endereço'))}",
            f"Salas: {safe_str(dados.get('Salas'))}",
            f"Tipo: {safe_str(dados.get('Tipo'))}",
            f"Preço real: {formatar_reais(dados.get('Preço real', dados.get('Preço')))}",
            f"Preço Previsto LightGBM: {safe_str(dados.get('Preço Previsto LightGBM'))}",
            f"Distância: {safe_str(dados.get('Distância'))}",
            f"Código postal: {safe_str(dados.get('Código postal'))}",
            f"Quartos: {safe_str(dados.get('Quartos'))}",
            f"Banheiros: {safe_str(dados.get('Banheiros'))}",
            f"Garagem: {safe_str(dados.get('Garagem'))}",
            f"Tamanho do Terreno: {safe_str(dados.get('Tamanho do Terreno'))}",
            f"Área Construída: {safe_str(dados.get('Área Construída'))}",
            f"Ano de Construção: {safe_str(dados.get('Ano de Construção'))}",
            f"Latitude: {safe_str(lat)}",
            f"Longitude: {safe_str(lon)}",
            f"Nome da Região: {safe_str(dados.get('Nome da Região'))}",
            f"Quantidade de Imóveis na Região: {safe_str(dados.get('Quantidade de Imóveis na Região'))}",
            "",
        ]

        for w in self.info_frame.winfo_children():
            w.destroy()

        cols = 3
        rows = math.ceil(len(info) / cols)
        for idx, txt in enumerate(info):
            r = idx % rows
            c = idx // rows
            lbl = tk.Label(
                self.info_frame,
                text=txt,
                font=("Arial", 11, "bold"),   
                justify="center",
            )
            lbl.grid(row=r, column=c, sticky="w", padx=10, pady=2)

        if lat and lon:
            self.map_widget.set_position(lat, lon)
            self.map_widget.set_zoom(14)
            self.map_widget.delete_all_marker()
            self.map_widget.set_marker(lat, lon, text=escolha)

    # Abre popup para recomendar bairro e imóvel, destaca resultados no mapa
    def abrir_formulario_recomendacao(self):
        form = tk.Toplevel(self.root)
        form.title("Recomendação de Bairro e Imóvel")
        frame = ttk.Frame(form, padding=20)
        frame.pack(fill="both", expand=True)

        msg = (
            "O imóvel recomendado será destacado com um marcador especial no mapa.\n"
            "Os demais imóveis do bairro aparecerão como círculos vermelhos claros."
        )
        tk.Label(frame, text=msg, justify="left", font=("Segoe UI", 9, "italic"), foreground="#b00").grid(
            row=5, column=0, columnspan=2, pady=(0, 10), sticky="w"
        )

        tk.Label(frame, text="Quantidade de carros:").grid(row=0, column=0, sticky="w", pady=2)
        entry_carros = ttk.Entry(frame)
        entry_carros.grid(row=0, column=1, pady=2)

        tk.Label(frame, text="Quantidade de quartos:").grid(row=1, column=0, sticky="w", pady=2)
        entry_quartos = ttk.Entry(frame)
        entry_quartos.grid(row=1, column=1, pady=2)

        tk.Label(frame, text="Preço máximo (R$):").grid(row=2, column=0, sticky="w", pady=2)
        entry_preco = ttk.Entry(frame)
        entry_preco.grid(row=2, column=1, pady=2)

        resultado_label = tk.Label(frame, text="", justify=tk.LEFT, font=("Segoe UI", 10))
        resultado_label.grid(row=4, column=0, columnspan=2, pady=10)

        # Lista para armazenar os círculos desenhados no mapa
        drawn_circles = []

        # Busca e recomenda o melhor imóvel de acordo com os critérios do usuário
        def buscar_melhor_bairro():
            # Checagem de campos obrigatórios
            if not entry_carros.get().strip() or not entry_quartos.get().strip() or not entry_preco.get().strip():
                resultado_label.config(text="Preencha todos os campos obrigatórios (carros, quartos e preço máximo).")
                return
            try:
                carros = int(entry_carros.get())
                quartos = int(entry_quartos.get())
                preco_max = float(entry_preco.get())
                # Checagem de faixa
                if not (0 <= carros <= 30):
                    raise ValueError("Carros deve ser inteiro entre 0 e 30.")
                if not (0 <= quartos <= 30):
                    raise ValueError("Quartos deve ser inteiro entre 0 e 30.")
            except ValueError as e:
                resultado_label.config(text=str(e) if str(e) else "Preencha todos os campos corretamente.")
                return

            df_filtrado = self.df[
                (self.df['Preço'] <= preco_max) &
                (self.df['Quartos'] >= quartos) &
                (self.df['Garagem'] >= carros)
            ].copy()
            if df_filtrado.empty:
                resultado_label.config(text="Nenhum imóvel encontrado dentro do preço e requisitos informados.")
                return

            df_filtrado['distancia'] = (
                abs(df_filtrado['Garagem'] - carros) +
                abs(df_filtrado['Quartos'] - quartos)
            )
            melhor = df_filtrado.sort_values(['distancia', 'Preço']).iloc[0]
            # Descobrir o número do imóvel recomendado (índice + 1)
            num_imovel = melhor.name + 1 if hasattr(melhor, 'name') else 'N/A'
            info = [
                f"Melhor bairro para você: {melhor['Subúrbio']}",
                f"Imóvel recomendado (nº {num_imovel}):",
                f"  Endereço: {melhor.get('Endereço', 'N/A')}",
                f"  Preço: {formatar_reais(melhor['Preço'])}",
                f"  Quartos: {melhor['Quartos']}",
                f"  Garagem: {melhor['Garagem']}",
                f"  Tipo: {melhor.get('Tipo', 'N/A')}",
            ]
            resultado_label.config(text="\n".join(info) + "\n\n(Imóveis do bairro destacados no mapa)")

            # Destaca o imóvel recomendado no mapa
            lat = melhor.get("Latitude", None)
            lon = melhor.get("Longitude", None)
            self.map_widget.delete_all_marker()
            if pd.notnull(lat) and pd.notnull(lon):
                self.map_widget.set_position(lat, lon)
                self.map_widget.set_zoom(14)
                self.map_widget.set_marker(lat, lon, text=f"Imóvel recomendado (nº {num_imovel})")

            # Desenhar círculos vermelhos para os demais imóveis do bairro
            bairro = melhor['Subúrbio']
            similares_bairro = self.df[self.df['Subúrbio'] == bairro]
            for idx, row in similares_bairro.iterrows():
                lat_b = row.get('Latitude', None)
                lon_b = row.get('Longitude', None)
                if pd.notnull(lat_b) and pd.notnull(lon_b) and idx != melhor.name:
                    # Gerar pontos para um círculo de raio ~120m
                    raio = 0.0011  # Aproximadamente 120m em latitude/longitude
                    pontos = [
                        (lat_b + math.cos(2*math.pi/36*x)*raio, lon_b + math.sin(2*math.pi/36*x)*raio)
                        for x in range(37)
                    ]
                    self.map_widget.set_path(pontos, color="#ff8888", width=2)

        ttk.Button(frame, text="Buscar", command=buscar_melhor_bairro)\
            .grid(row=3, column=0, columnspan=2, pady=10)

        # Limpa o mapa e reseta ao fechar o popup de recomendação
        def resetar_mapa():
            self.map_widget.delete_all_marker()
            for path in list(drawn_circles):
                try:
                    if hasattr(path, "delete"):
                        path.delete()
                    else:
                        self.map_widget.delete_path(path)
                except Exception:
                    pass
                drawn_circles.remove(path)
            self.map_widget.set_position(-37.8136, 144.9631)
            self.map_widget.set_zoom(10)

        form.protocol("WM_DELETE_WINDOW", lambda: (resetar_mapa(), form.destroy()))

    # Abre popup para avaliação de preço de imóvel com base em critérios do usuário
    def abrir_formulario_avaliacao(self):

        form = tk.Toplevel(self.root)
        form.title("Avaliação de Preço de Imóvel")
        frame = ttk.Frame(form, padding=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Subúrbio (obrigatório):").grid(row=0, column=0, sticky="w", pady=2)
        suburbios = sorted(self.df['Subúrbio'].dropna().unique())
        combo_suburbio = ttk.Combobox(frame, values=suburbios, state="readonly")
        combo_suburbio.grid(row=0, column=1, pady=2)

        tk.Label(frame, text="Quartos (obrigatório):").grid(row=1, column=0, sticky="w", pady=2)
        entry_quartos = ttk.Entry(frame)
        entry_quartos.grid(row=1, column=1, pady=2)

        tk.Label(frame, text="Banheiros (obrigatório):").grid(row=2, column=0, sticky="w", pady=2)
        entry_banheiros = ttk.Entry(frame)
        entry_banheiros.grid(row=2, column=1, pady=2)

        tk.Label(frame, text="Garagem (opcional):").grid(row=3, column=0, sticky="w", pady=2)
        entry_garagem = ttk.Entry(frame)
        entry_garagem.grid(row=3, column=1, pady=2)

        tk.Label(frame, text="Ano de Construção (opcional):").grid(row=4, column=0, sticky="w", pady=2)
        entry_ano = ttk.Entry(frame)
        entry_ano.grid(row=4, column=1, pady=2)

        resultado_label = tk.Label(frame, text="", justify=tk.LEFT, font=("Segoe UI", 10))
        resultado_label.grid(row=6, column=0, columnspan=2, pady=10)

        # Carrega o modelo LightGBM treinado
        modelo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../modelo_lgb.pkl"))
        try:
            modelo = joblib.load(modelo_path)
        except Exception as e:
            resultado_label.config(text=f"Erro ao carregar modelo: {e}")
            return

        # Calcula e exibe o preço médio dos imóveis similares e a previsão do modelo
        def avaliar_preco():
            suburbio = combo_suburbio.get()
            quartos = entry_quartos.get()
            banheiros = entry_banheiros.get()
            garagem = entry_garagem.get()
            ano = entry_ano.get()

            if not suburbio or not quartos or not banheiros:
                resultado_label.config(text="Preencha Subúrbio, Quartos e Banheiros.")
                return
            try:
                quartos = int(quartos)
                banheiros = int(banheiros)
                if not (0 <= quartos <= 30 and 0 <= banheiros <= 30):
                    raise ValueError
            except ValueError:
                resultado_label.config(text="Quartos e Banheiros devem ser inteiros entre 0 e 30.")
                return

            try:
                garagem = int(garagem) if garagem.strip() else None
                if garagem is not None and not (0 <= garagem <= 30):
                    raise ValueError
            except ValueError:
                resultado_label.config(text="Garagem deve ser um inteiro entre 0 e 30.")
                return

            try:
                ano = int(ano) if ano.strip() else None
                if ano is not None and not (1900 <= ano <= 2025):
                    raise ValueError
            except ValueError:
                resultado_label.config(text="Ano de Construção deve ser um inteiro entre 1900 e 2025.")
                return

            filtro = (
                (self.df['Subúrbio'] == suburbio) &
                (self.df['Quartos'] >= quartos) &
                (self.df['Banheiros'] >= banheiros)
            )
            if garagem is not None:
                filtro &= (self.df['Garagem'] >= garagem)
            if ano is not None:
                filtro &= (self.df['Ano de Construção'] >= ano)

            similares = self.df[filtro]
            mostrar_similares = True
            if similares.empty:
                mostrar_similares = False

            if mostrar_similares:
                preco_medio = similares['Preço'].mean()
                # Marcar imóveis semelhantes no mapa
                self.map_widget.delete_all_marker()
                lats = []
                lons = []
                for idx, row in similares.iterrows():
                    lat = row.get('Latitude', None)
                    lon = row.get('Longitude', None)
                    if pd.notnull(lat) and pd.notnull(lon):
                        lats.append(lat)
                        lons.append(lon)
                        num_similar = idx + 1
                        self.map_widget.set_marker(lat, lon, text=f"Imóvel nº{num_similar}: {formatar_reais(row['Preço'])}")
                # Centralizar e dar zoom na região dos similares
                if lats and lons:
                    lat_centro = sum(lats) / len(lats)
                    lon_centro = sum(lons) / len(lons)
                    self.map_widget.set_position(lat_centro, lon_centro)
                    self.map_widget.set_zoom(14)
            else:
                preco_medio = None
                self.map_widget.delete_all_marker()
            # Prepara os dados para o modelo
            X_pred = pd.DataFrame([{
                'Subúrbio': suburbio,
                'Quartos': quartos,
                'Banheiros': banheiros,
                'Garagem': garagem if garagem is not None else self.df['Garagem'].mode()[0],
                'Ano de Construção': ano if ano is not None else self.df['Ano de Construção'].mode()[0]
            }])

            # Se o modelo foi treinado com dummies, alinhe as colunas
            X_pred = pd.get_dummies(X_pred)
            if hasattr(modelo, 'feature_names_in_'):
                faltantes = [col for col in modelo.feature_names_in_ if col not in X_pred.columns]
                if faltantes:
                    X_pred = pd.concat([X_pred, pd.DataFrame(0, index=X_pred.index, columns=faltantes)], axis=1)
                X_pred = X_pred[modelo.feature_names_in_]

            try:
                preco_previsto = modelo.predict(X_pred)[0]
            except Exception as e:
                resultado_label.config(text=f"Erro ao prever com o modelo: {e}")
                return


            if mostrar_similares:
                resultado_label.config(
                    text=f"Preço médio: {formatar_reais(preco_medio)}\n"
                         f"({len(similares)} encontrado(s))\n"
                         f"Preço estimado pelo modelo: {formatar_reais(preco_previsto)}\n"
                         f"Imóveis similares estão destacados no mapa com seu número e preço."
                )
            else:
                resultado_label.config(
                    text=f"Nenhum imóvel similar encontrado.\n"
                         f"Preço estimado pelo modelo: {formatar_reais(preco_previsto)}"
                )

            # Marcar imóveis semelhantes no mapa
            self.map_widget.delete_all_marker()
            for _, row in similares.iterrows():
                lat = row.get('Latitude', None)
                lon = row.get('Longitude', None)
                if pd.notnull(lat) and pd.notnull(lon):
                    self.map_widget.set_marker(lat, lon, text=f"Similar: {formatar_reais(row['Preço'])}")

        ttk.Button(frame, text="Avaliar", command=avaliar_preco)\
            .grid(row=5, column=0, columnspan=2, pady=10)

        # Limpa o mapa e reseta ao fechar o popup de avaliação
        def resetar_mapa_avaliacao():
            self.map_widget.delete_all_marker()
            self.map_widget.set_position(-37.8136, 144.9631)
            self.map_widget.set_zoom(10)

        form.protocol("WM_DELETE_WINDOW", lambda: (resetar_mapa_avaliacao(), form.destroy()))


if __name__ == "__main__":
    app = tb.Window(themename="flatly")
    app.geometry("1024x768")
    ImovelApp(app)
    app.mainloop()