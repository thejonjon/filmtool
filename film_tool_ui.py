#!/usr/bin/python
import sys,os
from PyQt4 import QtCore, QtGui, uic
import time

from datetime import datetime, date, timedelta

class GlobalTimer(QtCore.QThread):
    def __init__(self,parent=None,command='python',path='.', silent=False,args=[]):
        QtCore.QThread.__init__(self,parent)
        self.myParent = parent
        self.start_time = 0
        self.cur_time = 0
        self.running = True
    
    def stop_timer(self):
        self.running = False
        
    def run(self):
        self.start_time = time.time()
        while self.running:
            time.sleep(.05)
            self.cur_time = time.time() - self.start_time
            self.emit(QtCore.SIGNAL("update_global_timer_callback ( PyQt_PyObject )"),self.cur_time)
            
class FilmToolUI(QtGui.QMainWindow):

    def __init__(self,parent=None,to_version=None):
        QtGui.QMainWindow.__init__(self, parent)
        w = QtGui.QWidget()
        self.setCentralWidget(w)
        
        topFiller = QtGui.QWidget()
        topFiller.setSizePolicy(QtGui.QSizePolicy.Expanding,
                                                        QtGui.QSizePolicy.Expanding)
        
        #Remove maximize and minimize buttons onwindow
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowMaximizeButtonHint)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowMinimizeButtonHint)
        
        #Get actual path and set it to load the ui file
        self.mypath = os.path.realpath(sys.argv[0])
        if not os.path.isdir(self.mypath):
            self.mypath = os.path.dirname(self.mypath)
        
        #Load the ui
        self.ui = uic.loadUi(os.path.join(self.mypath,'layouts','main_window.ui'), self)
        self.setFixedSize(self.size())
        
        QtCore.QObject.connect(self.ui.btn_sequence_start, QtCore.SIGNAL("clicked()"), self.on_start_sequence_click)
        QtCore.QObject.connect(self.ui.btn_sequence_stop, QtCore.SIGNAL("clicked()"), self.on_stop_sequence_click)
        QtCore.QObject.connect(self.ui.btn_make_mark, QtCore.SIGNAL("clicked()"), self.on_make_mark_click)
        QtCore.QObject.connect(self.ui.btn_end_mark, QtCore.SIGNAL("clicked()"), self.on_end_mark_click)
        QtCore.QObject.connect(self.ui.btn_submark, QtCore.SIGNAL("clicked()"), self.on_sub_mark_click)
        QtCore.QObject.connect(self.ui.btn_submark_directions, QtCore.SIGNAL("clicked()"), self.on_submark_directions_click)
        QtCore.QObject.connect(self.ui.btn_ignore_last_submark, QtCore.SIGNAL("clicked()"), self.on_crapbeans_click)

        
        self.global_timer_value = 0
        self.submark_counter = 0
        self.last_mark = 0
        self.output_filename = 'nothingyet'
        
        self.mark_history = []
        self.output_columns = ['real_time_readable','sequence_name','sequence_time_readable','event','mark_note','submark#','EMPTY','real_time','real_sequence_time',]
    
        
    def ready_output_file(self):
        desc = str(self.ui.txt_sequence_title.text())
        self.output_filename = "vidoelog-"+str(time.time()).split(".")[0]+"-"+desc.replace(" ","_")+'.csv'
        
        with open(os.path.join(os.path.join(self.mypath,'output'),self.output_filename),'a') as f:
            f.write('\t'.join(self.output_columns)+"\n" )
            
    def append_log(self,data):
        with open(os.path.join(os.path.join(self.mypath,'output'),self.output_filename),'a') as f:
            f.write(  '\t'.join([str(data[x]) for x in self.output_columns]) + "\n")
        
    def log_event(self,_type):
        if _type in ['mark_start','mark_end']:
            mark_note = str(self.ui.txt_mark_note.text())
            submark = '--'
        else:
            mark_note = '--'
            if 'ignore' in _type:
                submark = 'diapers'
            else:
                submark = str(self.submark_counter)
            
        sq= self.global_timer_value
        now = time.time()
        event = {
            'real_time':now,
            'real_time_readable':datetime.fromtimestamp(int(now)).strftime('%Y-%m-%d %H:%M:%S'),
            'sequence_name':unicode(self.ui.txt_sequence_title.text()),
            'event':_type,
            'mark_note':mark_note,
            'submark#':submark,
            'real_sequence_time':sq,
            'sequence_time_readable': self.make_readable_time(sq),
            'EMPTY':' -->-~~>=(|}PIEFACESPLAT'
        }
        self.append_log(event)
        self.mark_history.append(event)
        
        #real_time, sequence_name, event, mark_note, submark#, sequence_timer
        
    def make_readable_time(self,time_stamp):
        m, s = divmod(time_stamp, 60)
        h, m = divmod(m, 60)
        mm =  int(str(time_stamp).split('.')[-1]) if '.' in str(time_stamp) else 0
        return "%d:%02d:%02d.%d" % (h, m, s, mm)

    def on_start_sequence_click(self):
        self.ready_output_file()
        self.log_event('sequence_start')
        self.GlobalSequenceTimer = GlobalTimer(parent=self)
        self.connect(self.GlobalSequenceTimer,QtCore.SIGNAL("update_global_timer_callback ( PyQt_PyObject ) "), self.update_global_timer_callback)
        self.GlobalSequenceTimer.start()
        
        #Update Buttons
        #Sequence buttons 
        self.ui.btn_sequence_stop.setEnabled(True)
        self.ui.txt_sequence_title.setEnabled(False)
        self.ui.btn_sequence_start.setEnabled(False)
        
        #Mark buttons
        self.ui.btn_make_mark.setEnabled(True)
        self.ui.btn_end_mark.setEnabled(False)
        self.ui.btn_submark.setEnabled(False)
        self.ui.txt_mark_note.setEnabled(True)
    def on_submark_directions_click(self):
        self.log_event('submark_directions')
    def on_crapbeans_click(self):
        self.log_event('ignore_last_submark')
        self.submark_counter-=1
        self.update_submark_counter()
        
    def on_stop_sequence_click(self):
        self.log_event('sequence_stop')
        self.GlobalSequenceTimer.stop_timer()
        
        #Update Buttons
        self.ui.btn_sequence_stop.setEnabled(False)
        self.ui.btn_sequence_start.setEnabled(True)
        self.ui.txt_sequence_title.setEnabled(True)
        self.ui.btn_make_mark.setEnabled(False)
        self.ui.btn_end_mark.setEnabled(False)
        self.ui.btn_submark.setEnabled(False)
        self.ui.txt_mark_note.setEnabled(False)
    
    def on_make_mark_click(self):
        self.log_event('mark_start')
        self.last_mark = self.global_timer_value
        self.update_last_mark()
        
        #Update Buttons
        self.ui.btn_make_mark.setEnabled(False)
        self.ui.btn_end_mark.setEnabled(True)
        self.ui.btn_submark.setEnabled(True)
        self.ui.btn_submark_directions.setEnabled(True)
        self.ui.txt_mark_note.setEnabled(False)
        
    def on_end_mark_click(self):
        self.log_event('mark_end')
        self.ui.btn_make_mark.setEnabled(True)
        self.ui.btn_end_mark.setEnabled(False)
        self.ui.btn_submark.setEnabled(False)
        self.ui.btn_submark_directions.setEnabled(False)
        self.ui.txt_mark_note.setEnabled(True)
        
        self.submark_counter = 0
        self.last_mark = 0
        self.update_last_mark()
        self.update_submark_counter()

    def on_sub_mark_click(self):
        self.log_event('submark')
        self.submark_counter+=1
        self.update_submark_counter()
    
    def update_submark_counter(self):
        self.ui.lbl_submark_counter.setText(str(self.submark_counter))
    
    def update_last_mark(self):
        self.ui.lbl_last_mark_timestamp.setText(self.make_readable_time(self.last_mark))
        
    
    def update_last_mark_timer(self):
        self.ui.lbl_cur_mark_time.setText(self.make_readable_time(self.global_timer_value - self.last_mark))
        
        
    def update_global_timer(self):
        self.ui.lbl_global_time.setText(self.make_readable_time(self.global_timer_value))
        
    def update_global_timer_callback(self,time_stamp):
        self.global_timer_value = time_stamp
        
        self.update_global_timer()
        if self.last_mark:
            self.update_last_mark_timer()

if __name__ == "__main__":
    
    app = QtGui.QApplication(sys.argv)
    mainwindow = FilmToolUI()

    mainwindow.show()
    sys.exit(app.exec_())
