from fpdf import FPDF

class PDF_MC_Table(FPDF):
    def __init__(self):
        super().__init__()
        self.widths = None
        self.aligns = None

    def set_widths(self, w):
        # Set the array of column widths
        self.widths = w

    def set_aligns(self, a):
        # Set the array of column alignments
        self.aligns = a

    def row(self, data, fill=False, fill_color=None):
        # Calcular la altura de la fila
        nb = 0
        for i in range(len(data)):
            # Convertir el dato a string si no lo es
            cell_data = str(data[i]) if not isinstance(data[i], str) else data[i]
            nb = max(nb, self.nb_lines(self.widths[i], cell_data))
        h = 5 * nb
        # Verificar si se necesita un salto de página
        self.check_page_break(h)
        # Calcular la posición x para centrar la tabla
        total_width = sum(self.widths)
        x = (self.w - total_width) / 2  # Centrar horizontalmente
        self.set_x(x)  # Mover la posición actual a la x calculada
        # Dibujar las celdas de la fila
        for i in range(len(data)):
            w = self.widths[i]
            a = self.aligns[i] if self.aligns else 'L'
            # Guardar la posición actual
            x = self.get_x()
            y = self.get_y()
            # Dibujar el borde
            self.rect(x, y, w, h)
            # Aplicar color de fondo si se especifica
            if fill and fill_color:
                self.set_fill_color(*fill_color)
                self.rect(x, y, w, h, style='F')  # Rellenar el rectángulo
            # Convertir el dato a string si no lo es
            cell_data = str(data[i]) if not isinstance(data[i], str) else data[i]
            # Imprimir el texto
            self.multi_cell(w, 5, cell_data, 0, a)
            # Mover la posición a la derecha de la celda
            self.set_xy(x + w, y)
        # Ir a la siguiente línea
        self.ln(h)

    def header_row(self, data, fill_color=(200, 200, 200)):
        self.set_font('Arial', 'B', 12)  # Fuente en negrita para el encabezado
        self.row(data, fill=True, fill_color=fill_color)
        self.set_font('Arial', '', 12)  # Restaurar la fuente normal

    def check_page_break(self, h):
        # Si la altura h causaría un desbordamiento, añadir una nueva página
        if self.get_y() + h > self.page_break_trigger:
            self.add_page(self.cur_orientation)

    def nb_lines(self, w, txt):
        # Calcular el número de líneas que ocupará un texto en una celda de ancho w
        cw = self.current_font['cw']
        if w == 0:
            w = self.w - self.r_margin - self.x
        wmax = (w - 2 * self.c_margin) * 1000 / self.font_size
        s = str(txt).replace("\r", '')
        nb = len(s)
        if nb > 0 and s[nb-1] == "\n":
            nb -= 1
        sep = -1
        i = 0
        j = 0
        l = 0
        nl = 1
        while i < nb:
            c = s[i]
            if c == "\n":
                i += 1
                sep = -1
                j = i
                l = 0
                nl += 1
                continue
            if c == ' ':
                sep = i
            l += cw.get(c, 0)
            if l > wmax:
                if sep == -1:
                    if i == j:
                        i += 1
                else:
                    i = sep + 1
                sep = -1
                j = i
                l = 0
                nl += 1
            else:
                i += 1
        return nl