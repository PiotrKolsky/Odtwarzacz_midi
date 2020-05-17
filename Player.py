#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: pi
"""
from tkinter import *
from tkinter.ttk import Progressbar, Style
from tkinter.filedialog import askopenfilename
from pygame import mixer as pmixer
from mido import MidiFile
from music21 import *
import scipy.io.wavfile as wav
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
from numpy import array
import os


class Player(Frame):
    
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.geometry('470x190')
        self.master.title("Odtwarzacz")
        self.master.columnconfigure(0, minsize=250)
        self.file = str()
        self.is_pause = 0
        self.duration_secs = 100
        self.batch = 5000
        self.frames = 1
        self.music_freq = array([0 for x in range(self.batch)])
        self.create_widgets()
        

    def file_inp(self):
        self.file = askopenfilename(initialdir= os.getcwd(), filetypes = (("Mid files","*.mid"),
                                                                                ("Wav files","*.wav"),
                                                                                ("all files","*.*")))
        if str(self.file).strip('()') != str():
            self.lbl_title = Label(self.master, text=self.file.split('/')[-1][:25], font=("Arial", 10), width=20)
            self.lbl_title.grid(column=3, row=0, sticky="ew")
        
            if self.file.split('.')[-1] == 'mid':
                duration_secs = int(MidiFile(self.file).length)

            elif self.file.split('.')[-1] == 'wav':
                source_rate, source_sig = wav.read(self.file)
                duration_secs = int(len(source_sig) / float(source_rate))

            else: pass
        
            self.progressbar.config(mode = 'determinate', maximum = duration_secs*2+1, value = 0)
            self.progressbar.step(0)
           
            if self.file.split('.')[-1] == 'wav': 
                self.batch = 5000
                _, self.music_freq = wav.read(self.file)
                
            elif self.file.split('.')[-1] == 'mid':
                mid_file = converter.parse(self.file)
                self.music_freq = [0, ]
                
                for e in mid_file:
                    for f in e:
                        if type(f)==note.Note: 
                            self.music_freq = self.music_freq + [int(f.pitch.frequency)]
                            
                        elif type(f)==note.Rest: 
                            self.music_freq = self.music_freq + [0]
                            
                        elif type(f)==chord.Chord:
                            for g in f.pitches:
                                self.music_freq = self.music_freq + [int(g.frequency)]
                                
                        elif type(f)==stream.Voice:
                            for g in f.notes:
                                
                                if type(g)==note.Note: 
                                    self.music_freq = self.music_freq + [int(g.pitch.frequency)]
                                    
                                elif type(g)==note.Rest: 
                                    self.music_freq = self.music_freq + [0]
                                    
                                elif type(g)==chord.Chord:
                                    for h in g.pitches:
                                        self.music_freq = self.music_freq + [int(h.frequency)]
                                else: pass
                        else: pass
                
                lgth = len(self.music_freq)
                
                for i in range(1, lgth):
                    self.music_freq.insert(lgth-i+1, -self.music_freq[lgth-i])
                
                duration = int(MidiFile(self.file).length)
                self.batch = int(len(self.music_freq) / duration / 2)
                
            else: 
                self.batch = 5000
                self.music_freq = array([0 for x in range(self.batch)])
        
        else: pass

    
    def start(self):
        if str(self.file).strip('()') != str():
            pmixer.music.load(self.file)
            pmixer.music.play()
            self.lbl_status.configure(text="Playing", fg='green')
            self.progressbar.config(value = 0)
            self.progressbar.start(500)
            frames = int(len(self.music_freq)/self.batch)
            self.ax.set_xlim(0, self.batch)
            self.ax.set_ylim(min(self.music_freq), max(self.music_freq))
            self.anima = animation.FuncAnimation(self.fig, self.animate, 
        							frames=frames, interval=500, blit=True, repeat=False) 
        else: 
            self.file_inp()

    
    def pause(self):
        if pmixer.music.get_busy():
            if self.is_pause == 0:
                pmixer.music.pause()
                self.lbl_status.configure(text="Paused", fg='orange')
                self.anima.event_source.stop()
                self.progressbar.stop()
                self.progressbar.step(int(pmixer.music.get_pos()/500))
                self.is_pause = 1
                
            else:
                pmixer.music.unpause()
                self.lbl_status.configure(text="Playing", fg='green')
                self.anima.event_source.start()
                self.progressbar.start(500)
                self.is_pause = 0
                
        else: pass
    
      
    def stop(self):
        self.is_pause = 0
        pmixer.music.stop()
        self.progressbar.stop()
        self.lbl_status.configure(text="Stopped", fg='black')
        if pmixer.music.get_busy() == 0:
            self.anima.event_source.start()
    
    
    def animate(self, i): 
        if pmixer.music.get_busy(): 
            xdata = range(self.batch)
            ydata = self.music_freq[i*self.batch:(i+1)*self.batch]
        else: 
            xdata = ydata = array([0 for x in range(self.batch)])
            self.progressbar.stop()
            self.anima.event_source.stop()
            self.lbl_status.configure(text="Stopped", fg='black')
        self.line.set_data(xdata, ydata) 
        return self.line, 
    
    
    def volume(self, vol):
        pmixer.music.set_volume(float(vol)/100)
        

    def create_widgets(self):
        self.style = Style()
        self.style.configure("black.Horizontal.TProgressbar", background='green')
        self.progressbar = Progressbar(self.master, length=200, style='black.Horizontal.TProgressbar')
        self.progressbar.grid(column=0, row=4, sticky="s")

        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(4,1), dpi=50)
        self.ax = plt.axes(xlim=(0, self.batch))
        self.line, = self.ax.plot([], [], c=(1.0, 0.4, 0.0)) 
        plt.axis('off')
        
        self.display = FigureCanvasTkAgg(self.fig, self.master)
        self.display.get_tk_widget().grid(column=0, row=1) 
                
        self.scale_vol = Scale(orient='horizontal', length=200, from_=0, to=100, command=self.volume)
        self.scale_vol.set(50)
        self.scale_vol.grid(column=0, row=7, sticky="s") 

        
        self.menu = Menu(self.master)
        self.new_item = Menu(self.menu)
        self.new_item.add_command(label='New', command=self.file_inp)
        self.new_item.add_separator()
        self.new_item.add_command(label='Start', command=self.start)
        self.new_item.add_separator()
        self.new_item.add_command(label='Stop', command=self.stop)
        self.menu.add_cascade(label='File', menu=self.new_item)
        self.master.config(menu=self.menu)
        
        
        self.lbl_status = Label(self.master, text="Silent", font=("Arial Bold", 14))
        self.lbl_status.grid(column=0, row=0) 
        
        self.btn_start = Button(self.master, text='Start', bg="green", fg="black", height=2, width=20, command=self.start)
        self.btn_start.grid(column=3, row=1, sticky="nsew")
        
        self.btn_pause = Button(self.master, text="Pause", bg="yellow", fg="black", height=2, width=20, command=self.pause)
        self.btn_pause.grid(column=3, row=4, sticky="nsew")
        
        self.btn_stop = Button(self.master, text="Stop", bg="red", fg="black", height=2, width=20, command=self.stop)
        self.btn_stop.grid(column=3, row=7, sticky="nsew")
 
       
if __name__ == '__main__':
    root = Tk()
    pmixer.init()
    plr = Player(master=root)
    plr.mainloop()
    pmixer.quit()

