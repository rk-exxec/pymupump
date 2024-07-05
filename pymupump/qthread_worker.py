
#     MAEsure is a program to measure the surface energy of MAEs via contact angle
#     Copyright (C) 2021  Raphael Kriegl

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.

#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

from PySide6.QtCore import QThread,Slot, QWaitCondition, QMutex

class Worker(QThread):
    """executes function in qthread
    """
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.args = args
        self.kwargs = kwargs
        self.fn = fn

    @Slot()
    def run(self):
        self.fn(*self.args, **self.kwargs)


class PerpetualWorker(QThread):
    """ similar to callback worker, executes fn with args and kwargs, then waits until stop is called, then executes fn_on_stop in thread"""
    def __init__(self, fn, *args, fn_on_stop=None,  **kwargs):
        super().__init__()
        self.args = args
        self.kwargs = kwargs
        self.fn = fn
        self.fn_on_stop = fn_on_stop
        self.wait_condition = QWaitCondition()
        self.mutex = QMutex()

    @Slot()
    def run(self):
        self.fn(*self.args, **self.kwargs)
        self.mutex.lock()
        self.wait_condition.wait(self.mutex)
        self.mutex.unlock()
        if self.fn_on_stop: self.fn_on_stop()

    def stop(self):
        self.wait_condition.wakeAll()

class CallbackWorker(QThread):
    """ Thread with callback function on exit """
    def __init__(self, target, *args, slotOnFinished=None, **kwargs):
        super(CallbackWorker, self).__init__()
        self.args = args
        self.kwargs = kwargs
        self.target = target
        if slotOnFinished:
            self.finished.connect(slotOnFinished)

    def run(self):
        self.target(*self.args, **self.kwargs)