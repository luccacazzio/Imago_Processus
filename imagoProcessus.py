import cv2
import time
import random
import numpy as np
from tkinter import *
from imageio import imread
import tkinter.font as font
from PIL import ImageTk, Image
from scipy.spatial import distance
from os import chdir, getcwd, listdir
from tkinter import ttk, filedialog, messagebox
from skimage.feature import greycomatrix, greycoprops
from skimage.measure import moments_hu, shannon_entropy

###################################################################

class TelaCaracteristicas(Frame):
    def __init__(self, master=None, titulo='', texto=''):
        Frame.__init__(self, master)
        self.master = master
        self.titulo = titulo
        # Define o título da imagem
        self.master.title(titulo)
        # Define as dimenções da janela
        tela_largura, tela_altura = self.getResolucaoTela()
        janela_largura = round(tela_largura/6)
        janela_altura = round(tela_altura/2)
        # Aplica as dimenções e posição da janela
        self.master.geometry(str(janela_largura) + 'x' + str(janela_altura) + '+' + str(round(janela_largura/4)) + '+' + str(round(janela_altura/4)))
        self.printCaracteristicas(texto)

    def getResolucaoTela(self):
        # Obtêm as dimenções da tela
        tela_largura = self.master.winfo_screenwidth()
        tela_altura = self.master.winfo_screenheight()
        return (tela_largura, tela_altura)


    def printCaracteristicas(self, texto):
        self.textoTituloDir = Label(self.master, text=self.titulo, justify=CENTER, wraplength = 220, font="-weight bold -size 10")
        self.textoTituloDir.pack(pady = (20, 0), padx = (10, 0), anchor=W)
        self.textoDir = Label(self.master, text=texto, justify=CENTER, wraplength = 220)
        self.textoDir.pack(padx = (10, 0), anchor=W)

##############################################################################

class AutoScrollbar(ttk.Scrollbar):
    ''' A scrollbar that hides itself if it's not needed.
        Works only if you use the grid geometry manager '''
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
            ttk.Scrollbar.set(self, lo, hi)

    def pack(self, **kw):
        raise TclError('Cannot use pack with this widget')

    def place(self, **kw):
        raise TclError('Cannot use place with this widget')

###############################################################################

class TelaImagem(Frame):
    def __init__(self, master=None, titulo='', inverso=[], media=[], caracteristicasSelecionadas=[]):
        Frame.__init__(self, master)
        self.master = master
        self.inverso = inverso
        self.media = media
        self.caracteristicasSelecionadas = caracteristicasSelecionadas
        # Define o título da imagem
        self.master.title(titulo)
        # Define as dimenções da janela
        tela_largura, tela_altura = self.getResolucaoTela()
        janela_largura = round(tela_largura/2)
        janela_altura = round(tela_altura/2)
        # Aplica as dimenções e posição da janela
        self.master.geometry(str(janela_largura) + 'x' + str(janela_altura) + '+' + str(round(tela_largura/4)) + '+' + str(round(tela_altura/4)-200))
        self.master.state('zoomed')
        # Implementa o menu e seus componentes na janela
        self.criarMenu()
        # Instancia a imagem da class como None
        self.imagemOriginal = None
        self.newImg = None
        self.canvas = None
        self.container = None
        #Define a area selecionada
        self.areaSelecionada = None
        self.open_img()

    def open_img(self):

        if(self.canvas!=None): 
            self.canvas.destroy()

        # Vertical and horizontal scrollbars for canvas
        vbar = AutoScrollbar(self.master, orient='vertical')
        hbar = AutoScrollbar(self.master, orient='horizontal')
        vbar.grid(row=0, column=1, sticky='ns')
        hbar.grid(row=1, column=0, sticky='we')
        # Create canvas and put image on it
        self.canvas = Canvas(self.master, highlightthickness=0, xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        self.canvas.update()  # wait till canvas is created
        vbar.configure(command=self.scroll_y)  # bind scrollbars to the canvas
        hbar.configure(command=self.scroll_x)
        # Make the canvas expandable
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)
        # Bind events to the Canvas
        self.canvas.bind('<Configure>', self.show_image)  # canvas is resized
        self.canvas.bind('<ButtonPress-1>', self.move_from)
        self.canvas.bind('<B1-Motion>', self.move_to)
        self.canvas.bind('<MouseWheel>', self.wheel)  # with Windows and MacOS, but not Linux
        self.canvas.bind('<Button-5>', self.wheel)  # only with Linux, wheel scroll down
        self.canvas.bind('<Button-4>', self.wheel)  # only with Linux, wheel scroll up

        # Abre caixa de diálogo para seleção do arquivo
        fname = filedialog.askopenfilename(title='open')
        inicio = time.time()
        # Instancia a imagem selecionada
        self.imagemOriginal = Image.open(fname)
        self.img = self.imagemOriginal
        self.width, self.height = self.imagemOriginal.size
        self.imscale = 1.0  # scale for the canvaas image
        self.delta = 1.3  # zoom magnitude
        # Put image into container rectangle and use it to set proper coordinates to the image
        self.container = self.canvas.create_rectangle(0, 0, self.width, self.height, width=0)
        self.show_image()

        final = time.time()
        print(final - inicio)

    def scroll_y(self, *args, **kwargs):
        ''' Scroll canvas vertically and redraw the image '''
        self.canvas.yview(*args, **kwargs)  # scroll vertically
        self.show_image()  # redraw the image

    def scroll_x(self, *args, **kwargs):
        ''' Scroll canvas horizontally and redraw the image '''
        self.canvas.xview(*args, **kwargs)  # scroll horizontally
        self.show_image()  # redraw the image

    def move_from(self, event):
        ''' Remember previous coordinates for scrolling with the mouse '''
        self.canvas.scan_mark(event.x, event.y)

    def move_to(self, event):
        ''' Drag (move) canvas to the new position '''
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.show_image()  # redraw the image

    def wheel(self, event):
        ''' Zoom with mouse wheel '''
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        bbox = self.canvas.bbox(self.container)  # get image area
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]: pass  # Ok! Inside the image
        else: return  # zoom only inside image area
        scale = 1.0
        # Respond to Linux (event.num) or Windows (event.delta) wheel event
        if (self.imscale > 0.05 and event.delta == -120):  # scroll down
            i = min(self.width, self.height)
            if int(i * self.imscale) < 30: return  # image is less than 30 pixels
            self.imscale /= self.delta
            scale        /= self.delta
        if (self.imscale < 9 and event.delta == 120):  # scroll up
            i = min(self.canvas.winfo_width(), self.canvas.winfo_height())
            if i < self.imscale: return  # 1 pixel is bigger than the visible area
            self.imscale *= self.delta
            scale        *= self.delta
        self.canvas.scale('all', x, y, scale, scale)  # rescale all canvas objects
        self.show_image()

    def show_image(self, event=None):
        ''' Show image on the Canvas '''
        if(self.container !=None):
            bbox1 = self.canvas.bbox(self.container)  # get image area
            # Remove 1 pixel shift at the sides of the bbox1
            bbox1 = (bbox1[0] + 1, bbox1[1] + 1, bbox1[2] - 1, bbox1[3] - 1)
            bbox2 = (self.canvas.canvasx(0),  # get visible area of the canvas
                    self.canvas.canvasy(0),
                    self.canvas.canvasx(self.canvas.winfo_width()),
                    self.canvas.canvasy(self.canvas.winfo_height()))
            bbox = [min(bbox1[0], bbox2[0]), min(bbox1[1], bbox2[1]),  # get scroll region box
                    max(bbox1[2], bbox2[2]), max(bbox1[3], bbox2[3])]
            if bbox[0] == bbox2[0] and bbox[2] == bbox2[2]:  # whole image in the visible area
                bbox[0] = bbox1[0]
                bbox[2] = bbox1[2]
            if bbox[1] == bbox2[1] and bbox[3] == bbox2[3]:  # whole image in the visible area
                bbox[1] = bbox1[1]
                bbox[3] = bbox1[3]
            self.canvas.configure(scrollregion=bbox)  # set scroll region
            x1 = max(bbox2[0] - bbox1[0], 0)  # get coordinates (x1,y1,x2,y2) of the image tile
            y1 = max(bbox2[1] - bbox1[1], 0)
            x2 = min(bbox2[2], bbox1[2]) - bbox1[0]
            y2 = min(bbox2[3], bbox1[3]) - bbox1[1]
            if int(x2 - x1) > 0 and int(y2 - y1) > 0:  # show image if it in the visible area
                x = min(int(x2 / self.imscale), self.width)   # sometimes it is larger on 1 pixel...
                y = min(int(y2 / self.imscale), self.height)  # ...and sometimes not
                self.img = self.imagemOriginal.crop((int(x1 / self.imscale), int(y1 / self.imscale), x, y))
                img = self.img.resize((int(x2 - x1), int(y2 - y1)))
                imagetk = ImageTk.PhotoImage(img)
                imageid = self.canvas.create_image(max(bbox2[0], bbox1[0]), max(bbox2[1], bbox1[1]),
                                                anchor='nw', image=imagetk)
                self.canvas.lower(imageid)  # set image into background
                self.canvas.imageid = imageid
                self.canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection

    def getResolucaoTela(self):
        # Obtêm as dimenções da tela
        tela_largura = self.master.winfo_screenwidth()
        tela_altura = self.master.winfo_screenheight()
        return (tela_largura, tela_altura)

    def mouseBotaoEsquerdoPressionado(self, event):
        if(self.areaSelecionada != None):
            self.canvas.delete(self.areaSelecionada)

        bbox = self.canvas.bbox(self.container)  # get image area
        # Remove 1 pixel shift at the sides of the bbox1
        bbox1 = (bbox[0] + 1, bbox[1] + 1, bbox[2] -1, bbox[3] - 1)
        bbox2 = (self.canvas.canvasx(0), self.canvas.canvasy(0)) # get visible area of the canvas

        x1 = max(bbox2[0] - bbox1[0], 0)  # get coordinates (x1,y1,x2,y2) of the image tile
        y1 = max(bbox2[1] - bbox1[1], 0)

        if(bbox1[0] < bbox2[0]):
            width = event.x
        else:
            width = event.x + bbox2[0] - bbox1[0]
        width = (self.width*width)/(bbox1[2] - bbox1[0])
        if(bbox1[1] < bbox2[1]):
            height = event.y
        else:
            height = event.y + bbox2[1] - bbox1[1]
        height = (self.height*height)/(bbox1[3] - bbox1[1])
        self.areaSelecionada = self.canvas.create_rectangle(event.x+bbox2[0]-round(64*self.imscale), event.y+bbox2[1]-round(64*self.imscale), event.x+bbox2[0]+round(64*self.imscale), event.y+bbox2[1]+round(64*self.imscale), outline="green")
        self.newImg = self.imagemOriginal
        self.newImg.crop((width-64+(int(x1/self.imscale)), height-64+(int(y1/self.imscale)), width+64+(int(x1/self.imscale)), height+64+(int(y1/self.imscale)))).save('teste.png')

    def crop_img(self):
        if(self.areaSelecionada != None):
            self.canvas.delete(self.areaSelecionada)
        self.newImg = self.imagemOriginal.save('teste.png')
        self.canvas.bind('<Button-3>', self.mouseBotaoEsquerdoPressionado) 

    def caracterizar(self):
        inicio = time.time()
        im = cv2.imread('teste.png', 0)
        
        data = np.array((im/8), 'int')
        g = greycomatrix(data, [1, 2, 4, 8, 16], [0, np.pi/4, np.pi/2, 3*np.pi/4], levels=32,
                 normed=True, symmetric=True)
        
        texto = ''
        contrast = []
        if(self.caracteristicasSelecionadas[3].get()):
            contrast = greycoprops(g, 'contrast')
            contrast = [sum(i) for i in contrast]
            texto += 'Contraste: ' + str(round(contrast[0], 3)) + '\n\n'
        
        homogeneity = []
        if(self.caracteristicasSelecionadas[0].get()):
            homogeneity = greycoprops(g, 'homogeneity')
            homogeneity = [sum(i) for i in homogeneity]
            texto += 'Homogeneidade: ' + str(round(homogeneity[0], 3)) + '\n\n'

        energy = []
        if(self.caracteristicasSelecionadas[2].get()):
            energy = greycoprops(g, 'energy')
            energy = [sum(i) for i in energy]
            texto += 'Energia: ' + str(round(energy[0], 3)) + '\n\n'

        entropy = []
        if(self.caracteristicasSelecionadas[1].get()):
            entropy = shannon_entropy(data)
            texto += 'Entropia: ' + str(round(entropy, 3)) + '\n\n'

        hu = moments_hu(data)
        texto += 'Hu: ' + str([round(i, 3) for i in hu]) + '\n\n'
        self.caracteristicasImagem = [contrast, homogeneity, energy, entropy, hu]

        final = time.time()
        print(final - inicio)

        root3 = Toplevel()
        app2 = TelaCaracteristicas(root3, 'Caracteristicas', texto)

    def desenrolar(self, caracteristicas):
        c = list()

        if(self.caracteristicasSelecionadas[3].get()):
            j=0
            while j<5:
                c.append(caracteristicas[0][j])
                j+=1

        if(self.caracteristicasSelecionadas[0].get()):
            j=0
            while j<5:
                c.append(caracteristicas[1][j])
                j+=1

        if(self.caracteristicasSelecionadas[2].get()):
            j=0
            while j<5:
                c.append(caracteristicas[2][j])
                j+=1
        
        if(self.caracteristicasSelecionadas[1].get()):
            c.append(caracteristicas[3])

        j=0
        while j<7:
            c.append(caracteristicas[4][j])
            j+=1
        return c

    def classificar(self):
        inicio = time.time()

        A = self.desenrolar(self.caracteristicasImagem)
        B = self.desenrolar(self.media[0])
        dif = np.subtract(A, B)
        dist1 = np.dot(np.dot(np.array(dif).T, self.inverso[0]), np.array(dif))
        menor = 0
        menorValor = dist1

        B = self.desenrolar(self.media[1])
        dif = np.subtract(A, B)
        dist2 = np.dot(np.dot(np.array(dif).T, self.inverso[1]), np.array(dif))
        if(dist2 < menorValor):
            menor = 1
            menorValor = dist2
        
        B = self.desenrolar(self.media[2])
        dif = np.subtract(A, B)
        dist3 = np.dot(np.dot(np.array(dif).T, self.inverso[2]), np.array(dif))
        if(dist3 < menorValor):
            menor = 2
            menorValor = dist3
        
        B = self.desenrolar(self.media[3])
        dif = np.subtract(A, B)
        dist4 = np.dot(np.dot(np.array(dif).T, self.inverso[3]), np.array(dif))
        if(dist4 < menorValor):
            menor = 3
            menorValor = dist4

        final = time.time()
        print(final - inicio)

        root3 = Toplevel()
        app2 = TelaCaracteristicas(root3, 'Classificacao', str(menor+1))

    def criarMenu(self):
        menubar = Menu(self.master)
        menubar.add_command(label="Nova imagem", command=self.open_img)
        menubar.add_command(label="Recortar", command=self.crop_img)
        menubar.add_command(label="Caracterizar", command=self.caracterizar)
        menubar.add_command(label="Classificar", command=self.classificar)
        self.master.config(menu=menubar)


###############################################################################


class MenuPrincipal(Frame):
    def __init__(self, master=None, titulo=''):
        super().__init__(master)
        self.master = master
        # Define o título da imagem
        self.master.title(titulo)

        tela_largura, tela_altura = self.getResolucaoTela()
        janela_largura = round(tela_largura/6)
        janela_altura = round(tela_altura/3) + 50
        # Aplica as dimenções e posição da janela
        self.master.geometry(str(janela_largura) + 'x' + str(janela_altura) + '+' + str(round(tela_largura/4)) + '+' + str(round(tela_altura/4)-200))
        self.textoDir = NONE
        self.listaCaracteristicas = ['Homogeneidade', 'Entropia', 'Energia', 'Contraste']
        self.caracteristicasLabel = NONE
        self.textoCaracteristicas = NONE
        self.textoTreinador = NONE
        self.textoTabela = NONE
        # Implementa o menu e seus componentes na janela
        self.criarMenu()

    def getResolucaoTela(self):
        # Obtêm as dimenções da tela
        tela_largura = self.master.winfo_screenwidth()
        tela_altura = self.master.winfo_screenheight()
        return (tela_largura, tela_altura)

    def lerArquivo(self):

        self.imagensDir1 = list()
        self.imagensDir2 = list()
        self.imagensDir3 = list()
        self.imagensDir4 = list()
        # Abre caixa de diálogo para seleção do arquivo
        self.diretorio = filedialog.askdirectory()
        inicio = time.time()

        chdir(self.diretorio + '/1')
        print(getcwd())
        for c in listdir():
            self.imagensDir1.append(cv2.imread(c, 0))
        print(self.imagensDir1.__len__())

        chdir(self.diretorio + '/2')
        print(getcwd())
        for c in listdir():
            self.imagensDir2.append(cv2.imread(c, 0))
        print(self.imagensDir2.__len__())

        chdir(self.diretorio + '/3')
        print(getcwd())
        for c in listdir():
            self.imagensDir3.append(cv2.imread(c, 0))
        print(self.imagensDir3.__len__())

        chdir(self.diretorio + '/4')
        print(getcwd())
        for c in listdir():
            self.imagensDir4.append(cv2.imread(c, 0))
        print(self.imagensDir4.__len__())

        chdir(self.diretorio)
 
        if(self.textoDir != NONE):
            self.textoTituloDir.destroy()
            self.textoDir.destroy()
            if(self.textoCaracteristicas != NONE):        
                self.textoTituloCaracteristicas.destroy()
                self.textoCaracteristicas.destroy()
                if(self.textoTreinador != NONE):
                    self.textoTituloTreinador.destroy()
                    self.textoTreinador.destroy()
                    if(self.textoTabela != NONE):
                        self.textoTabela.destroy()
                        self.textoTituloTabela.destroy()

        tela_largura, tela_altura = self.getResolucaoTela()
        janela_largura = round(tela_largura/6)
        janela_altura = round(tela_altura/2)
        # Aplica as dimenções e posição da janela
        self.master.geometry(str(janela_largura) + 'x' + str(janela_altura) + '+' + str(round(tela_largura/4)) + '+' + str(round(tela_altura/4)-200))
        self.textoTituloDir = Label(self.menu, text='Pasta lida:', justify=CENTER, wraplength = 220, font="-weight bold -size 10")
        self.textoTituloDir.pack(pady = (20, 0), padx = (10, 0), anchor=W)
        self.textoDir = Label(self.menu, text=self.diretorio, justify=CENTER, wraplength = 220)
        self.textoDir.pack(padx = (10, 0), anchor=W)

        final = time.time()
        print(final - inicio)

    def salvarCaracteristicas(self):
        inicio = time.time()

        self.caracteristicasImagens1 = list()
        for im in self.imagensDir1:
            data = np.array((im/8), 'int')
            g = greycomatrix(data, [1, 2, 4, 8, 16], [0, np.pi/4, np.pi/2, 3*np.pi/4], levels=32,
                    normed=True, symmetric=True)
            
            contrast = []
            if(self.caracteristicas[3].get()):
                contrast = greycoprops(g, 'contrast')
                contrast = [sum(i) for i in contrast]
            
            homogeneity = []
            if(self.caracteristicas[0].get()):
                homogeneity = greycoprops(g, 'homogeneity')
                homogeneity = [sum(i) for i in homogeneity]

            energy = []
            if(self.caracteristicas[2].get()):
                energy = greycoprops(g, 'energy')
                energy = [sum(i) for i in energy]
            
            entropy = 0
            if(self.caracteristicas[1].get()):
                entropy = shannon_entropy(data)
            
            hu = moments_hu(data)
            self.caracteristicasImagens1.append([contrast, homogeneity, energy, entropy, hu])

        self.caracteristicasImagens2 = list()
        for im in self.imagensDir2:
            data = np.array((im/8), 'int')
            g = greycomatrix(data, [1, 2, 4, 8, 16], [0, np.pi/4, np.pi/2, 3*np.pi/4], levels=32,
                    normed=True, symmetric=True)
            contrast = []
            if(self.caracteristicas[3].get()):
                contrast = greycoprops(g, 'contrast')
                contrast = [sum(i) for i in contrast]
            
            homogeneity = []
            if(self.caracteristicas[0].get()):
                homogeneity = greycoprops(g, 'homogeneity')
                homogeneity = [sum(i) for i in homogeneity]

            energy = []
            if(self.caracteristicas[2].get()):
                energy = greycoprops(g, 'energy')
                energy = [sum(i) for i in energy]
            
            entropy = 0
            if(self.caracteristicas[1].get()):
                entropy = shannon_entropy(data)
            
            hu = moments_hu(data)
            self.caracteristicasImagens2.append([contrast, homogeneity, energy, entropy, hu])

        self.caracteristicasImagens3 = list()
        for im in self.imagensDir3:
            data = np.array((im/8), 'int')
            g = greycomatrix(data, [1, 2, 4, 8, 16], [0, np.pi/4, np.pi/2, 3*np.pi/4], levels=32,
                    normed=True, symmetric=True)
            contrast = []
            if(self.caracteristicas[3].get()):
                contrast = greycoprops(g, 'contrast')
                contrast = [sum(i) for i in contrast]
            
            homogeneity = []
            if(self.caracteristicas[0].get()):
                homogeneity = greycoprops(g, 'homogeneity')
                homogeneity = [sum(i) for i in homogeneity]

            energy = []
            if(self.caracteristicas[2].get()):
                energy = greycoprops(g, 'energy')
                energy = [sum(i) for i in energy]
            
            entropy = 0
            if(self.caracteristicas[1].get()):
                entropy = shannon_entropy(data)
            
            hu = moments_hu(data)
            self.caracteristicasImagens3.append([contrast, homogeneity, energy, entropy, hu])

        self.caracteristicasImagens4 = list()
        for im in self.imagensDir4:
            data = np.array((im/8), 'int')
            g = greycomatrix(data, [1, 2, 4, 8, 16], [0, np.pi/4, np.pi/2, 3*np.pi/4], levels=32,
                    normed=True, symmetric=True)
            contrast = []
            if(self.caracteristicas[3].get()):
                contrast = greycoprops(g, 'contrast')
                contrast = [sum(i) for i in contrast]
            
            homogeneity = []
            if(self.caracteristicas[0].get()):
                homogeneity = greycoprops(g, 'homogeneity')
                homogeneity = [sum(i) for i in homogeneity]

            energy = []
            if(self.caracteristicas[2].get()):
                energy = greycoprops(g, 'energy')
                energy = [sum(i) for i in energy]
            
            entropy = 0
            if(self.caracteristicas[1].get()):
                entropy = shannon_entropy(data)
            
            hu = moments_hu(data)
            
            self.caracteristicasImagens4.append([contrast, homogeneity, energy, entropy, hu])
            

        self.caracteristicasSelecionadas()

        final = time.time()
        print(final - inicio)

    def caracteristicasWidget(self):

        self.caracteristicas = [IntVar(), IntVar(), IntVar(), IntVar()]
        if(self.caracteristicasLabel != NONE):
            self.caracteristicasLabel.destroy()
            if(self.textoTreinador != NONE):
                self.textoTituloTreinador.destroy()
                self.textoTreinador.destroy()
                if(self.textoTabela != NONE):
                    self.textoTabela.destroy()
                    self.textoTituloTabela.destroy()
    
        self.caracteristicasLabel = Label(self.master)
        self.caracteristicasLabel.grid(column=1, row=0)

        tela_largura, tela_altura = self.getResolucaoTela()
        janela_largura = round(tela_largura/6) + 300
        janela_altura = round(tela_altura/2) - 10
        # Aplica as dimenções e posição da janela
        self.master.geometry(str(janela_largura) + 'x' + str(janela_altura) + '+' + str(round(tela_largura/4)) + '+' + str(round(tela_altura/4)-200))
        
        self.tituloCaracteristicas = Label(self.caracteristicasLabel, text='Selecione as caracteristicas:', wraplength = 220, font="-weight bold -size 10")
        self.tituloCaracteristicas.pack(pady = (20, 0), padx = (30, 0), anchor=N)

        c = [NONE, NONE, NONE, NONE]
        i=0
        while i < len(self.caracteristicas):
            c[i] = Checkbutton(self.caracteristicasLabel, text=self.listaCaracteristicas[i], variable=self.caracteristicas[i], onvalue=1, offvalue=0)
            c[i].pack()
            i+=1

        botao = Button(self.caracteristicasLabel, text='Salvar caracteristicas', command = self.salvarCaracteristicas, width=20, height=2, font=font.Font(size=10))    
        botao.pack(pady = (30, 0), padx = (20, 0))

    def caracteristicasSelecionadas(self):
        if(self.caracteristicasLabel != NONE):
            self.caracteristicasLabel.destroy()
        if(self.textoCaracteristicas != NONE):
            self.textoTituloCaracteristicas.destroy()
            self.textoCaracteristicas.destroy()

        tela_largura, tela_altura = self.getResolucaoTela()
        janela_largura = round(tela_largura/6)
        janela_altura = round(tela_altura/2) + 60
        # Aplica as dimenções e posição da janela
        self.master.geometry(str(janela_largura) + 'x' + str(janela_altura) + '+' + str(round(tela_largura/4)) + '+' + str(round(tela_altura/4)-200))
        self.textoTituloCaracteristicas = Label(self.menu, text='Caracteristicas selecionadas:', justify=CENTER, wraplength = 220, font="-weight bold -size 10")
        self.textoTituloCaracteristicas.pack(pady = (20, 0), padx = (10, 0), anchor=W)
        texto = ''
        i=0
        while i < len(self.caracteristicas):
            if self.caracteristicas[i].get() :
                texto+=self.listaCaracteristicas[i]+' - '
            i+=1
        self.textoCaracteristicas = Label(self.menu, text=texto, justify=CENTER, wraplength = 220)
        self.textoCaracteristicas.pack(padx = (10, 0), anchor=W)

    def media(self):
        
        mediaContrast1 = [0, 0, 0, 0, 0]
        mediaHomogeneity1 = [0, 0, 0, 0, 0]
        mediaEnergy1 = [0, 0, 0, 0, 0]
        mediaEntropy1 = 0
        mediaHu1 = [0,0,0,0,0,0,0]
        mediaContrast2 = [0, 0, 0, 0, 0]
        mediaHomogeneity2 = [0, 0, 0, 0, 0]
        mediaEnergy2 = [0, 0, 0, 0, 0]
        mediaEntropy2 = 0
        mediaHu2 = [0,0,0,0,0,0,0]
        mediaContrast3 = [0, 0, 0, 0, 0]
        mediaHomogeneity3 = [0, 0, 0, 0, 0]
        mediaEnergy3 = [0, 0, 0, 0, 0]
        mediaEntropy3 = 0
        mediaHu3 = [0,0,0,0,0,0,0]
        mediaContrast4 = [0, 0, 0, 0, 0]
        mediaHomogeneity4 = [0, 0, 0, 0, 0]
        mediaEnergy4 = [0, 0, 0, 0, 0]
        mediaEntropy4 = 0
        mediaHu4 = [0,0,0,0,0,0,0]
        i=0
        while i<75:
            if(self.caracteristicas[3].get()):
                mediaContrast1 = np.add(mediaContrast1, self.caracteristicasImagens1[self.sorteio[i]][0])
                mediaContrast2 = np.add(mediaContrast2, self.caracteristicasImagens2[self.sorteio[i]][0])
                mediaContrast3 = np.add(mediaContrast3, self.caracteristicasImagens3[self.sorteio[i]][0])
                mediaContrast4 = np.add(mediaContrast4, self.caracteristicasImagens4[self.sorteio[i]][0])

            if(self.caracteristicas[0].get()):
                mediaHomogeneity1 = np.add(mediaHomogeneity1, self.caracteristicasImagens1[self.sorteio[i]][1])
                mediaHomogeneity2 = np.add(mediaHomogeneity2, self.caracteristicasImagens2[self.sorteio[i]][1])
                mediaHomogeneity3 = np.add(mediaHomogeneity3, self.caracteristicasImagens3[self.sorteio[i]][1])
                mediaHomogeneity4 = np.add(mediaHomogeneity4, self.caracteristicasImagens4[self.sorteio[i]][1])

            if(self.caracteristicas[2].get()):
                mediaEnergy1 = np.add(mediaEnergy1, self.caracteristicasImagens1[self.sorteio[i]][2])
                mediaEnergy2 = np.add(mediaEnergy2, self.caracteristicasImagens2[self.sorteio[i]][2])
                mediaEnergy3 = np.add(mediaEnergy3, self.caracteristicasImagens3[self.sorteio[i]][2])
                mediaEnergy4 = np.add(mediaEnergy4, self.caracteristicasImagens4[self.sorteio[i]][2])

            if(self.caracteristicas[1].get()):
                mediaEntropy1 += self.caracteristicasImagens1[self.sorteio[i]][3]
                mediaEntropy2 += self.caracteristicasImagens2[self.sorteio[i]][3]
                mediaEntropy3 += self.caracteristicasImagens3[self.sorteio[i]][3]
                mediaEntropy4 += self.caracteristicasImagens4[self.sorteio[i]][3]

            mediaHu1 = np.add(mediaHu1, self.caracteristicasImagens1[self.sorteio[i]][4])
            mediaHu2 = np.add(mediaHu2, self.caracteristicasImagens2[self.sorteio[i]][4])
            mediaHu3 = np.add(mediaHu3, self.caracteristicasImagens3[self.sorteio[i]][4]) 
            mediaHu4 = np.add(mediaHu4, self.caracteristicasImagens4[self.sorteio[i]][4])
            i+=1
        
        if(self.caracteristicas[3].get()):
            mediaContrast1 /= 75
            mediaContrast2 /= 75
            mediaContrast3 /= 75
            mediaContrast4 /= 75

        if(self.caracteristicas[0].get()):
            mediaHomogeneity1 /= 75
            mediaHomogeneity2 /= 75
            mediaHomogeneity3 /= 75
            mediaHomogeneity4 /= 75

        if(self.caracteristicas[2].get()):
            mediaEnergy1 /= 75
            mediaEnergy2 /= 75
            mediaEnergy3 /= 75
            mediaEnergy4 /= 75

        if(self.caracteristicas[1].get()):
            mediaEntropy1 /= 75
            mediaEntropy2 /= 75
            mediaEntropy3 /= 75
            mediaEntropy4 /= 75

        mediaHu1 /= 75
        mediaHu2 /= 75
        mediaHu3 /= 75      
        mediaHu4 /= 75

        self.mediaImagens1 = [mediaContrast1, mediaHomogeneity1, mediaEnergy1, mediaEntropy1, mediaHu1]
        self.mediaImagens2 = [mediaContrast2, mediaHomogeneity2, mediaEnergy2, mediaEntropy2, mediaHu2]
        self.mediaImagens3 = [mediaContrast3, mediaHomogeneity3, mediaEnergy3, mediaEntropy3, mediaHu3]
        self.mediaImagens4 = [mediaContrast4, mediaHomogeneity4, mediaEnergy4, mediaEntropy4, mediaHu4]

    def centrarNaMedia(self):
        i=0
        while i<75:
            if(self.caracteristicas[3].get()):
                self.caracteristicasImagens1[self.sorteio[i]][0] = np.subtract(self.caracteristicasImagens1[self.sorteio[i]][0], self.mediaImagens1[0])
                self.caracteristicasImagens2[self.sorteio[i]][0] = np.subtract(self.caracteristicasImagens2[self.sorteio[i]][0], self.mediaImagens2[0])
                self.caracteristicasImagens3[self.sorteio[i]][0] = np.subtract(self.caracteristicasImagens3[self.sorteio[i]][0], self.mediaImagens3[0])
                self.caracteristicasImagens4[self.sorteio[i]][0] = np.subtract(self.caracteristicasImagens4[self.sorteio[i]][0], self.mediaImagens4[0])

            if(self.caracteristicas[0].get()):
                self.caracteristicasImagens1[self.sorteio[i]][1] = np.subtract(self.caracteristicasImagens1[self.sorteio[i]][1], self.mediaImagens1[1])
                self.caracteristicasImagens2[self.sorteio[i]][1] = np.subtract(self.caracteristicasImagens2[self.sorteio[i]][1], self.mediaImagens2[1])
                self.caracteristicasImagens3[self.sorteio[i]][1] = np.subtract(self.caracteristicasImagens3[self.sorteio[i]][1], self.mediaImagens3[1])
                self.caracteristicasImagens4[self.sorteio[i]][1] = np.subtract(self.caracteristicasImagens4[self.sorteio[i]][1], self.mediaImagens4[1])

            if(self.caracteristicas[2].get()):
                self.caracteristicasImagens1[self.sorteio[i]][2] = np.subtract(self.caracteristicasImagens1[self.sorteio[i]][2], self.mediaImagens1[2])
                self.caracteristicasImagens2[self.sorteio[i]][2] = np.subtract(self.caracteristicasImagens2[self.sorteio[i]][2], self.mediaImagens2[2])
                self.caracteristicasImagens3[self.sorteio[i]][2] = np.subtract(self.caracteristicasImagens3[self.sorteio[i]][2], self.mediaImagens3[2])
                self.caracteristicasImagens4[self.sorteio[i]][2] = np.subtract(self.caracteristicasImagens4[self.sorteio[i]][2], self.mediaImagens4[2])

            if(self.caracteristicas[1].get()):
                self.caracteristicasImagens1[self.sorteio[i]][3] -=  self.mediaImagens1[3]
                self.caracteristicasImagens2[self.sorteio[i]][3] -=  self.mediaImagens2[3]
                self.caracteristicasImagens3[self.sorteio[i]][3] -=  self.mediaImagens3[3]
                self.caracteristicasImagens4[self.sorteio[i]][3] -=  self.mediaImagens4[3]

            self.caracteristicasImagens1[self.sorteio[i]][4] = np.subtract(self.caracteristicasImagens1[self.sorteio[i]][4], self.mediaImagens1[4])
            self.caracteristicasImagens2[self.sorteio[i]][4] = np.subtract(self.caracteristicasImagens2[self.sorteio[i]][4], self.mediaImagens2[4])
            self.caracteristicasImagens3[self.sorteio[i]][4] = np.subtract(self.caracteristicasImagens3[self.sorteio[i]][4], self.mediaImagens3[4])    
            self.caracteristicasImagens4[self.sorteio[i]][4] = np.subtract(self.caracteristicasImagens4[self.sorteio[i]][4], self.mediaImagens4[4])
            i+=1

    def covariancia(self):
        #Fazer a covariancia e inverter?
        c1 = list()
        c2 = list()
        c3 = list()
        c4 = list()

        #Imagens 1
        if(self.caracteristicas[3].get()):
            j=0
            while j<5:
                c1.append([i[0][j] for i in self.caracteristicasImagens1])
                j+=1

        if(self.caracteristicas[0].get()):
            j=0
            while j<5:
                c1.append([i[1][j] for i in self.caracteristicasImagens1])
                j+=1

        if(self.caracteristicas[2].get()):
            j=0
            while j<5:
                c1.append([i[2][j] for i in self.caracteristicasImagens1])
                j+=1

        if(self.caracteristicas[1].get()):        
            c1.append(i[3] for i in self.caracteristicasImagens1)

        j=0
        while j<7:
            c1.append([i[4][j] for i in self.caracteristicasImagens1])
            j+=1

        #Imagens 2
        if(self.caracteristicas[3].get()):
            j=0
            while j<5:
                c2.append([i[0][j] for i in self.caracteristicasImagens2])
                j+=1

        if(self.caracteristicas[0].get()):
            j=0
            while j<5:
                c2.append([i[1][j] for i in self.caracteristicasImagens2])
                j+=1
        
        if(self.caracteristicas[2].get()):
            j=0
            while j<5:
                c2.append([i[2][j] for i in self.caracteristicasImagens2])
                j+=1

        if(self.caracteristicas[1].get()):
            c2.append(i[3] for i in self.caracteristicasImagens2)

        j=0
        while j<7:
            c2.append([i[4][j] for i in self.caracteristicasImagens2])
            j+=1

        #Imagens 3
        if(self.caracteristicas[3].get()):
            j=0
            while j<5:
                c3.append([i[0][j] for i in self.caracteristicasImagens3])
                j+=1

        if(self.caracteristicas[0].get()):
            j=0
            while j<5:
                c3.append([i[1][j] for i in self.caracteristicasImagens3])
                j+=1
        
        if(self.caracteristicas[2].get()):
            j=0
            while j<5:
                c3.append([i[2][j] for i in self.caracteristicasImagens3])
                j+=1

        if(self.caracteristicas[1].get()):
            c3.append(i[3] for i in self.caracteristicasImagens3)

        j=0
        while j<7:
            c3.append([i[4][j] for i in self.caracteristicasImagens3])
            j+=1

        #Imagens 4
        if(self.caracteristicas[3].get()):
            j=0
            while j<5:
                c4.append([i[0][j] for i in self.caracteristicasImagens4])
                j+=1

        if(self.caracteristicas[0].get()):
            j=0
            while j<5:
                c4.append([i[1][j] for i in self.caracteristicasImagens4])
                j+=1

        if(self.caracteristicas[2].get()):
            j=0
            while j<5:
                c4.append([i[2][j] for i in self.caracteristicasImagens4])
                j+=1
        
        if(self.caracteristicas[1].get()):
            c4.append(i[3] for i in self.caracteristicasImagens4)

        j=0
        while j<7:
            c4.append([i[4][j] for i in self.caracteristicasImagens4])
            j+=1
        
        matrizCovariancia1 = np.cov([list(i) for i in c1])
        matrizCovariancia2 = np.cov([list(i) for i in c2])
        matrizCovariancia3 = np.cov([list(i) for i in c3])
        matrizCovariancia4 = np.cov([list(i) for i in c4])
        
        self.inversoM1 = np.linalg.inv(matrizCovariancia1)
        self.inversoM2 = np.linalg.inv(matrizCovariancia2)
        self.inversoM3 = np.linalg.inv(matrizCovariancia3)
        self.inversoM4 = np.linalg.inv(matrizCovariancia4)

    def treinarClassificador(self):

        if(self.textoTreinador != NONE):
            self.textoTituloTreinador.destroy()
            self.textoTreinador.destroy()
            if(self.textoTabela != NONE):
                self.textoTabela.destroy()
                self.textoTituloTabela.destroy()
        inicio = time.time()
        
        sorteio = list(range(0, 100))
        random.shuffle(sorteio)
        self.sorteio = sorteio

        self.media()
        self.centrarNaMedia()
        self.covariancia()

        final = time.time()
        print(final - inicio)

        tela_largura, tela_altura = self.getResolucaoTela()
        janela_largura = round(tela_largura/6)
        janela_altura = round(tela_altura/2) + 110
        # Aplica as dimenções e posição da janela
        self.master.geometry(str(janela_largura) + 'x' + str(janela_altura) + '+' + str(round(tela_largura/4)) + '+' + str(round(tela_altura/4)-200))
        self.textoTituloTreinador = Label(self.menu, text='Tempo de treinamento:', justify=CENTER, wraplength = 220, font="-weight bold -size 10")
        self.textoTituloTreinador.pack(pady = (20, 0), padx = (10, 0), anchor=W)

        self.textoTreinador = Label(self.menu, text=str(round((final-inicio), 4)) + ' segundos', justify=CENTER, wraplength = 220)
        self.textoTreinador.pack(padx = (10, 0), anchor=W)

    def printTabela(self):
        if(self.textoTabela != NONE):
            self.textoTabela.destroy()
            self.textoTituloTabela.destroy()

        tela_largura, tela_altura = self.getResolucaoTela()
        janela_largura = round(tela_largura/6)
        janela_altura = round(tela_altura/2) + 250
        # Aplica as dimenções e posição da janela
        self.master.geometry(str(janela_largura) + 'x' + str(janela_altura) + '+' + str(round(tela_largura/4)) + '+' + str(round(tela_altura/4)-200))
        self.textoTituloTabela = Label(self.menu, text='Matriz de confusão:', justify=CENTER, wraplength = 220, font="-weight bold -size 10")
        self.textoTituloTabela.pack(pady = (20, 0), padx = (10, 0), anchor=W)

        acuracia = sum(self.tabela[i][i]for i in range(4))/100
        especificidade = 1 - sum(25 - self.tabela[i][i]for i in range(4))/300
        texto = ''
        for i in self.tabela:
            for j in i:
                texto += str(j) + '  '
            texto+='\n'
        texto += 'Acurácia = ' + str(acuracia) + '\n'
        texto += 'Especificidade = ' + str(round(especificidade, 3)) + '\n'
        self.textoTabela = Label(self.menu, text=texto, justify=CENTER, wraplength = 220)
        self.textoTabela.pack(padx = (10, 0), anchor=W)

    def desenrolar(self, caracteristicas):
        c = list()

        if(self.caracteristicas[3].get()):
            j=0
            while j<5:
                c.append(caracteristicas[0][j])
                j+=1

        if(self.caracteristicas[0].get()):
            j=0
            while j<5:
                c.append(caracteristicas[1][j])
                j+=1
        
        if(self.caracteristicas[2].get()):
            j=0
            while j<5:
                c.append(caracteristicas[2][j])
                j+=1

        if(self.caracteristicas[1].get()):
            c.append(caracteristicas[3])

        j=0
        while j<7:
            c.append(caracteristicas[4][j])
            j+=1
        return c

    def classificarImagem(self):
        inicio = time.time()
        #Calcular a distancia da mahalanobis para os ultimos 25% dos grupos
        tabela = [[0,0,0,0], [0,0,0,0], [0,0,0,0], [0,0,0,0]]
        i=75
        while i<100:
            #fazer mahalanobis para os 4 grupos
            A = self.desenrolar(self.caracteristicasImagens1[self.sorteio[i]])
            B = self.desenrolar(self.mediaImagens1)
            dif = np.subtract(A, B)
            dist1 = np.dot(np.dot(np.array(dif).T, self.inversoM1), np.array(dif))
            menor = 0
            menorValor = dist1

            B = self.desenrolar(self.mediaImagens2)
            dif = np.subtract(A, B)
            dist2 = np.dot(np.dot(np.array(dif).T, self.inversoM2), np.array(dif))
            if(dist2 < menorValor):
                menor = 1
                menorValor = dist2
            
            B = self.desenrolar(self.mediaImagens3)
            dif = np.subtract(A, B)
            dist3 = np.dot(np.dot(np.array(dif).T, self.inversoM3), np.array(dif))
            if(dist3 < menorValor):
                menor = 2
                menorValor = dist3
            
            B = self.desenrolar(self.mediaImagens4)
            dif = np.subtract(A, B)
            dist4 = np.dot(np.dot(np.array(dif).T, self.inversoM4), np.array(dif))
            if(dist4 < menorValor):
                menor = 3
                menorValor = dist4

            tabela[0][menor]+=1

            A = self.desenrolar(self.caracteristicasImagens2[self.sorteio[i]])
            B = self.desenrolar(self.mediaImagens1)
            dif = np.subtract(A, B)
            dist1 = np.dot(np.dot(np.array(dif).T, self.inversoM1), np.array(dif))
            menor = 0
            menorValor = dist1

            B = self.desenrolar(self.mediaImagens2)
            dif = np.subtract(A, B)
            dist2 = np.dot(np.dot(np.array(dif).T, self.inversoM2), np.array(dif))
            if(dist2 < menorValor):
                menor = 1
                menorValor = dist2
            
            B = self.desenrolar(self.mediaImagens3)
            dif = np.subtract(A, B)
            dist3 = np.dot(np.dot(np.array(dif).T, self.inversoM3), np.array(dif))
            if(dist3 < menorValor):
                menor = 2
                menorValor = dist3
            
            B = self.desenrolar(self.mediaImagens4)
            dif = np.subtract(A, B)
            dist4 = np.dot(np.dot(np.array(dif).T, self.inversoM4), np.array(dif))
            if(dist4 < menorValor):
                menor = 3
                menorValor = dist4

            tabela[1][menor]+=1

            A = self.desenrolar(self.caracteristicasImagens3[self.sorteio[i]])
            B = self.desenrolar(self.mediaImagens1)
            dif = np.subtract(A, B)
            dist1 = np.dot(np.dot(np.array(dif).T, self.inversoM1), np.array(dif))
            menor = 0
            menorValor = dist1

            B = self.desenrolar(self.mediaImagens2)
            dif = np.subtract(A, B)
            dist2 = np.dot(np.dot(np.array(dif).T, self.inversoM2), np.array(dif))
            if(dist2 < menorValor):
                menor = 1
                menorValor = dist2
            
            B = self.desenrolar(self.mediaImagens3)
            dif = np.subtract(A, B)
            dist3 = np.dot(np.dot(np.array(dif).T, self.inversoM3), np.array(dif))
            if(dist3 < menorValor):
                menor = 2
                menorValor = dist3
            
            B = self.desenrolar(self.mediaImagens4)
            dif = np.subtract(A, B)
            dist4 = np.dot(np.dot(np.array(dif).T, self.inversoM4), np.array(dif))
            if(dist4 < menorValor):
                menor = 3
                menorValor = dist4

            tabela[2][menor]+=1

            A = self.desenrolar(self.caracteristicasImagens4[self.sorteio[i]])
            B = self.desenrolar(self.mediaImagens1)
            dif = np.subtract(A, B)
            dist1 = np.dot(np.dot(np.array(dif).T, self.inversoM1), np.array(dif))
            menor = 0
            menorValor = dist1

            B = self.desenrolar(self.mediaImagens2)
            dif = np.subtract(A, B)
            dist2 = np.dot(np.dot(np.array(dif).T, self.inversoM2), np.array(dif))
            if(dist2 < menorValor):
                menor = 1
                menorValor = dist2
            
            B = self.desenrolar(self.mediaImagens3)
            dif = np.subtract(A, B)
            dist3 = np.dot(np.dot(np.array(dif).T, self.inversoM3), np.array(dif))
            if(dist3 < menorValor):
                menor = 2
                menorValor = dist3
            
            B = self.desenrolar(self.mediaImagens4)
            dif = np.subtract(A, B)
            dist4 = np.dot(np.dot(np.array(dif).T, self.inversoM4), np.array(dif))
            if(dist4 < menorValor):
                menor = 3
                menorValor = dist4

            tabela[3][menor]+=1

            i+=1
        print(dif)
        print(dist4)
                
        self.tabela = tabela
        self.printTabela()

        final = time.time()
        print(final - inicio)

    def telaImagem(self):
        root2 = Toplevel()
        inverso = [self.inversoM1, self.inversoM2, self.inversoM3, self.inversoM4]
        media = [self.mediaImagens1, self.mediaImagens2, self.mediaImagens3, self.mediaImagens4]
        app2 = TelaImagem(root2, 'Visualizar Imagem', inverso, media, self.caracteristicas)

    def criarMenu(self):

        self.menu = Label(self.master)
        self.menu.grid(column=0, row=0)
        botao = Button(self.menu, text='Ler imagens treino', command = self.lerArquivo, width=25, height=2, font=font.Font(size=12))    
        botao.pack(pady = (30, 0), padx = (10, 0), anchor=W)
        botao = Button(self.menu, text='Selecionar características', command = self.caracteristicasWidget, width=25, height=2, font=font.Font(size=12))    
        botao.pack(pady = (6, 0), padx = (10, 0), anchor=W)
        botao = Button(self.menu, text='Treinar classificador', command = self.treinarClassificador, width=25, height=2, font=font.Font(size=12))    
        botao.pack(pady = (6, 0), padx = (10, 0), anchor=W)
        botao = Button(self.menu, text='Classificar imagens', command = self.classificarImagem, width=25, height=2, font=font.Font(size=12))
        botao.pack(pady = (6, 0), padx = (10, 0), anchor=W)
        botao = Button(self.menu, text='Abrir imagem', command = self.telaImagem, width=25, height=2, font=font.Font(size=12))
        botao.pack(pady = (6, 0), padx = (10, 0), anchor=W)

def main():
    root = Tk() # Instancia a janela principal

    app = MenuPrincipal(root, 'ImagoProcessus')

    app.mainloop() # Chama o loop principal da instância de Tk

# Chama a função main
if __name__ == '__main__':
    main()