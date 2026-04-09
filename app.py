import textwrap
from datetime import date, datetime
import requests
from bs4 import BeautifulSoup
import customtkinter as ctk
from tkinter import messagebox
from tkcalendar import Calendar  # Necessário: pip install tkcalendar

# Configurações globais do CustomTkinter
ctk.set_appearance_mode('dark')
ctk.set_default_color_theme("dark-blue")

class LiturgyService:
    """Classe responsável por buscar e processar os dados do site."""
    
    def __init__(self):
        self.url_base = "https://sagradaliturgia.com.br/liturgia_diaria.php?date="
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36"
        }
        self.full_text = ""

    def fetch_liturgy(self, target_date=None):
        """Busca a liturgia de uma data específica (objeto date)."""
        if target_date is None:
            target_date = date.today()
            
        date_str = target_date.strftime("%d-%m-%Y")
        url = f"{self.url_base}{date_str}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            elements = soup.find_all('div', class_='ui-body ui-body-a ui-corner-all')
            if len(elements) > 1:
                self.full_text = elements[1].text
                return True
            
            self.full_text = "Conteúdo não encontrado para esta data."
            return False
        except Exception as e:
            print(f"Erro na requisição: {e}")
            return False

    def get_section(self, start_marker, end_marker):
        """Extrai uma seção específica do texto bruto."""
        if not self.full_text or "não encontrado" in self.full_text:
            return self.full_text
        
        start_idx = self.full_text.find(start_marker)
        if start_idx == -1:
            return f"Seção '{start_marker}' não disponível hoje."
            
        # Se for uma lista/tupla de marcadores finais, busca a primeira ocorrência válida
        if isinstance(end_marker, (list, tuple)):
            indices = [self.full_text.find(m, start_idx) for m in end_marker]
            valid_idx = [i for i in indices if i != -1]
            end_idx = min(valid_idx) if valid_idx else -1
        else:
            end_idx = self.full_text.find(end_marker, start_idx) if end_marker else -1
        
        if end_idx != -1:
            content = self.full_text[start_idx:end_idx].strip()
        else:
            content = self.full_text[start_idx:].strip()
            
        return content

class App(ctk.CTk):
    """Classe principal da interface gráfica."""
    
    def __init__(self):
        super().__init__()

        self.title("Liturgia Diária")
        self.geometry("1024x680")
        self.resizable(False, False)
        
        self.service = LiturgyService()
        self.current_date = date.today()
        
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Cabeçalho: Título e Botão de Data
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(10, 20))

        self.label_title = ctk.CTkLabel(
            self.header_frame, text="Liturgia Diária", 
            font=('Roboto', 32, 'bold')
        )
        self.label_title.pack(side="left", padx=20)

        self.btn_date = ctk.CTkButton(
            self.header_frame, 
            text=f"📅 {self.current_date.strftime('%d/%m/%Y')}",
            width=150,
            command=self.open_calendar
        )
        self.btn_date.pack(side="right", padx=20)

        # Display
        self.text_display = ctk.CTkTextbox(
            self.main_frame, width=900, height=380, 
            font=("Roboto", 16), wrap="word"
        )
        self.text_display.pack(pady=10)

        # Botões de navegação
        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.button_frame.pack(pady=20)

        sections = [
            ("1ª LEITURA", "Primeira", "Salmo"),
            ("SALMO", "Salmo", ("Segunda leitura:", "Evangelho de Jesus Cristo")),
            ("2ª LEITURA", "Segunda leitura:", "Evangelho de Jesus Cristo"),
            ("EVANGELHO", "Proclamação do Evangelho", "- Glória a Vós, Senhor")
        ]

        for i, (name, start, end) in enumerate(sections):
            btn = ctk.CTkButton(
                self.button_frame, text=name, 
                command=lambda s=start, e=end: self.display_section(s, e)
            )
            btn.grid(row=0, column=i, padx=10)

    def open_calendar(self):
        """Abre uma janela para selecionar a data."""
        self.cal_window = ctk.CTkToplevel(self)
        self.cal_window.title("Selecionar Data")
        self.cal_window.geometry("300x350")
        self.cal_window.grab_set() # Foca apenas nesta janela

        cal = Calendar(self.cal_window, selectmode='day', 
                       year=self.current_date.year, 
                       month=self.current_date.month, 
                       day=self.current_date.day,
                       locale='pt_BR')
        cal.pack(pady=20, padx=10)

        def confirm_date():
            # Converte a string do calendário para objeto date
            date_str = cal.get_date()
            # Formato do tkcalendar depende do locale, mas geralmente é %d/%m/%y ou %m/%d/%y
            # Para evitar erros de parse, pegamos os atributos diretamente:
            sel_date = cal.selection_get()
            self.current_date = sel_date
            self.btn_date.configure(text=f"📅 {self.current_date.strftime('%d/%m/%Y')}")
            self.load_data()
            self.cal_window.destroy()

        ctk.CTkButton(self.cal_window, text="Confirmar", command=confirm_date).pack(pady=10)

    def load_data(self):
        self.text_display.delete("1.0", "end")
        self.text_display.insert("1.0", "Carregando liturgia...")
        if not self.service.fetch_liturgy(self.current_date):
            # Se falhou mas o texto foi setado como "não encontrado", exibe ele
            self.text_display.delete("1.0", "end")
            self.text_display.insert("1.0", self.service.full_text)
        else:
            self.display_section("Primeira", "Salmo")

    def display_section(self, start, end):
        content = self.service.get_section(start, end)
        if "Evangelho" in start and "não disponível" not in content:
            content += "\n\n- Glória a Vós, Senhor"
            
        self.text_display.delete("1.0", "end")
        self.text_display.insert("1.0", content)

if __name__ == "__main__":
    app = App()
    app.mainloop()