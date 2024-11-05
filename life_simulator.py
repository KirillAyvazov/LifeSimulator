"""
    Данный модуль содержит описание классов - клетки матрицы и симулятора игры в жизнь
"""
import os
from sys import stdout
from dataclasses import dataclass
from typing import Tuple, Optional, List
import time
from os import cpu_count
from threading import Thread, Barrier
import logging


logging.basicConfig(level=logging.DEBUG, format= "\n%(asctime)s - %(levelname)s - thread: %(threadName)s - %(message)s",
                    datefmt="%d-%m-%Y %H:%M:%S", stream=stdout)
logger = logging.getLogger(__name__)


@dataclass
class Cell:
    """Класс - модель одной клетки в матрице игрового поля"""
    x: int
    y: int
    alive: bool
    was_alive: bool
    neighbor_counter: int = 0
    control: bool = False


class LifeSimulator:
    """
        Класс - модель игры симулятора жизни. Обеспечивает создание матрицы игрового поля, заполнение его клетками,
    осуществление итераций и контроля клеток.
    """
    def __init__(self, alive: List[Tuple[int, int]], size: int = 10, delay: float = 0.7):
        self.__matrix = tuple(tuple(Cell(x, y, (x, y) in alive, (x, y) in alive) for y in range(size))
                            for x in range(size))
        self.__size = size
        self.__delay = delay
        self.__number_threads: Optional[int]
        self.__barrier: Optional[Barrier] = None

    @property
    def matrix(self):
        """Геттер атрибута __matrix"""
        return self.__matrix

    @property
    def size(self):
        """Геттер атрибута __size"""
        return self.__size

    @property
    def delay(self):
        """Геттер атрибута __delay"""
        return self.__delay

    @delay.setter
    def delay(self, new_val: float):
        """Сеттер атрибута __delay"""
        if new_val > 0:
            self.__delay = new_val

    def __reset_control(self):
        """Данный метод перед выполнением очередного шага контроля присваивает всем клеткам значение control = False"""
        for i_line in self.__matrix:
            for i_cell in i_line:
                i_cell.control = False

        self.__barrier.wait()

    def __step(self, list_indexes: List[int]) -> None:
        """Данный метод осуществляет один шаг контроля клеток поля в строках с указанными в переданном кортеже индексами"""
        self.__reset_control()

        for i_num_line in list_indexes:
            line = self.__matrix[i_num_line]
            for i_cell in line:
                #logger.debug(f"Просматривает клетку x:{i_cell.x}, y:{i_cell.y}")
                i_cell: Cell
                i_cell.was_alive = i_cell.alive

                self.__search_neighbors(i_cell)

                if i_cell.neighbor_counter < 2 or i_cell.neighbor_counter > 3:
                    i_cell.alive = False
                elif i_cell.neighbor_counter == 3:
                    i_cell.alive = True

                i_cell.control = True

    def __search_neighbors(self, cell: Cell) -> None:
        """
            Данный метод получает на вход клетку, обнуляет её счетчик соседей и осуществляет поиск соседей заново,
        устанавливая новое значение счетчика
        """
        cell.neighbor_counter = 0

        coordinates = ((x, y,) for x in range(cell.x-1, cell.x+2) for y in range(cell.y-1, cell.y+2)
                       if 0 <= x < self.__size and 0 <= y < self.__size and (x, y) != (cell.x, cell.y))

        for i_coord in coordinates:
            i_coord: Tuple[int, int]
            neighbour: Cell = self.__matrix[i_coord[0]][i_coord[1]]

            if neighbour.control:

                if neighbour.was_alive:
                    cell.neighbor_counter += 1

            else:
                if neighbour.alive:
                    cell.neighbor_counter += 1


    def __row_allocation(self) -> List[List[int]]:
        """
            Данный метод возвращает список списков целых чисел, где каждый список - это номера строк которые
        должен просмотреть отдельный поток
        """
        thread_count = os.cpu_count() - 1

        list_index = [list((range(self.__size)))[thread_num * (self.__size // thread_count) : thread_num * (self.__size // thread_count) + (self.__size // thread_count)]
                           for thread_num in range(thread_count)]

        last_index = list_index[thread_count-1][len(list_index[thread_count-1])-1]

        for index, elem in enumerate(range(last_index+1, self.__size)):
            list_index[index].append(elem)

        return list_index

    def __control(self, list_indexes: List[int]) -> None:
        """
            Данный метод осуществляет контроль клеток поля в заданных строках в бесконечном цикле путем вызова метода
        __step с установленным интервалом времени
        """
        while True:
            time.sleep(self.__delay)
            self.__step(list_indexes)

            if self.__barrier:
                self.__barrier.wait()

    def start(self) -> None:
        """
            Данный метод осуществляет запуск симуляции жизни, а именно выполняет метод __control в доступном количестве
        потоков с определенным интервалом времени.
        """
        # TODO: автор данного кода понимает всю нецелесообразность выполнения данного кода в нескольких потоках, однако
        # TODO: пошел на этот шаг в учебных целях :)

        if  2 < cpu_count() <= self.__size:
            list_index = self.__row_allocation()
            self.__barrier = Barrier(len(list_index))
            thread_pool = [Thread(target=self.__control, args=(i_list_index,), daemon=True) for i_list_index in list_index[:-1]]

            for i_thread in thread_pool:
                i_thread.start()

            self.__control(list_index[-1])

        else:
            self.__control(list(range(self.__size)))
