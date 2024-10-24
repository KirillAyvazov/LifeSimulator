from threading import Thread
from tkinter import Tk, Label, Button, Entry, Frame, Canvas
from functools import partial
from typing import Dict, Tuple, List, Any
import time
import re

from life_simulator import LifeSimulator, Cell


class Visualizer(Tk):
    """Класс - модель визуализатора симуляции"""

    def __init__(self):
        super().__init__()
        self.title("Life Simulator")
        #self.attributes('-zoomed', True)
        self.geometry('1800x1200')
        self.__tile_size: int = 20

        self.__world_size: int = 20
        self.__simulator_delay: float = 0.75
        self.__button_field: Dict[Tuple[int, int], Button] = dict()
        self.__tail_field: Dict[Any, Any] = dict()
        self.__list_living_cells = []


        self.__create_start_widgets()

    def __create_start_widgets(self):
        """Метод создает стартовые виджеты"""
        self.frame_start = Frame()
        self.frame_start.pack(anchor='n', padx=5, pady=5)

        self.label_size = Label(self.frame_start, text=f"Размер мира: {self.__world_size}")
        self.label_size.pack()

        self.entry_size = Entry(self.frame_start, name="size_world")
        self.entry_size.pack()

        self.button_size = Button(self.frame_start, name="set_size", text="Установить размер мира", command=self.__set_world_size)
        self.button_size.pack()

        self.label_delay = Label(self.frame_start, text=f"Задержка времени: {self.__simulator_delay}")
        self.label_delay.pack()

        self.entry_delay = Entry(self.frame_start, name="delay")
        self.entry_delay.pack()

        self.button_delay = Button(self.frame_start, name="set_delay", text="Установить длительность одного шага симуляции", command=self.__set_delay)
        self.button_delay.pack()

        self.button_placement = Button(self.frame_start, name="start_placement", text="Начать расстановку", command=self.__start_placement)
        self.button_placement.pack()

    def __set_delay(self):
        """Метод устанавливает значение задержки каждого шага симуляции"""
        result = self.entry_delay.get()

        if isinstance(result, str) and (result.isdigit() or re.search(r'^[0-9]*[.,][0-9]+$', result)):
            self.__simulator_delay = float(result)
            self.label_delay.config(text=f"Задержка времени: {self.__simulator_delay}")

        else:
            self.label_delay.config(text="Временная задержка должна быть числом!")

    def __set_world_size(self):
        """Метод устанавливает значение размера мира симуляции"""
        new_size = self.entry_size.get()
        if isinstance(new_size, str) and new_size.isdigit():
            self.__world_size = int(new_size)
            self.label_size.config(text=f"Размер мира: {self.__world_size}")
        else:
            self.label_size.config(text=f"Размер мира должен быть числом!")

    def __set_live_cell(self, x, y):
        """Метод - обработчик нажатия кнопки при стартовой расстановке клеток - помечает клетку живой"""
        if (x, y) not in self.__list_living_cells:
            self.__list_living_cells.append((x, y))
            button: Button = self.__button_field.get((x, y))
            button.config(background='black', activebackground="black", command=partial(self.__set_empty_cell, x, y))

    def __set_empty_cell(self, x, y):
        """Метод - обработчик нажатия кнопки при стартовой расстановке клеток - помечает клетку пустой"""
        self.__list_living_cells.remove((x, y))
        button: Button = self.__button_field.get((x, y))
        button.config(background='white', activebackground="green", command=partial(self.__set_live_cell, x, y))

    def __start_placement(self):
        """Метод отрисовки интерфейса для создания стартовой расстановки клеток"""
        self.frame_start.destroy()
        max_size_win = int(self.geometry().split("x")[0])
        start_point = max_size_win / 2 - int(self.__tile_size * self.__world_size / 2)

        for x in range(self.__world_size):
            for y in range(self.__world_size):
                button_cell = Button(self, height=self.__tile_size, width=self.__tile_size, background='white',
                                     activebackground="green", command=partial(self.__set_live_cell, x, y))
                button_cell.place(x=x*self.__tile_size+start_point, y=y*self.__tile_size,
                                  height=self.__tile_size, width=self.__tile_size)
                self.__button_field[(x, y)] = button_cell

        self.button_start = Button(self, text="Начать симуляцию", command=self.__start_simulation)
        self.button_start.pack(anchor="nw")
        self.button_back = Button(self, text="Вернуться к настройкам", command=self.__back)
        self.button_back.pack(anchor="nw")

    def __back(self):
        """Метод возврата к настройкам мира"""
        self.button_start.destroy()
        self.button_back.destroy()

        for i_button in self.__button_field.values():
            i_button.destroy()

        self.__create_start_widgets()

    def __create_cell_field(self):
        """Метод создает в окне клетки игрового поля"""
        max_size_win = int(self.geometry().split("x")[0])
        start_point = max_size_win / 2 - int(self.__tile_size * self.__world_size / 2)
        widht = self.__tile_size*self.__world_size
        self.canvas = Canvas(self, width = widht, height = widht)
        self.canvas.place(x=start_point, y=0)

        for x in range(self.__world_size):
            for y in range(self.__world_size):
                cell = self.canvas.create_rectangle(x*self.__tile_size, y*self.__tile_size,
                                                    x*self.__tile_size+self.__tile_size,
                                                    y*self.__tile_size+self.__tile_size, fill='white')
                self.__tail_field[(x, y)] = cell

        self.update()

    def __start_simulation(self):
        """Метод запускает симуляцию"""
        self.button_start.destroy()
        self.button_back.destroy()

        for i_button in self.__button_field.values():
            i_button.destroy()

        self.__create_cell_field()

        self.simulator = LifeSimulator(self.__list_living_cells, self.__world_size, self.__simulator_delay)
        new_thread = Thread(target=self.simulator.start, daemon=True)
        time.sleep(1)
        new_thread.start()

        self.__control_matrix()


    def __control_matrix(self):
        while True:
            for x in range(self.__world_size):
                for y in range(self.__world_size):
                    cell: Cell = self.simulator.matrix[x][y]
                    tail_id: int = self.__tail_field.get((x, y))

                    if cell.alive:
                        self.canvas.itemconfig(tail_id, fill='black')
                    else:
                        self.canvas.itemconfig(tail_id, fill='white')

            self.update()
