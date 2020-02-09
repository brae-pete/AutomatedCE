import time
from datetime import datetime
import sys
import os
from skimage import io
import cv2

try:
    from hardware import ImageControl
    import CESystems
except:
    sys.path.append(os.path.relpath('..'))
    from hardware import ImageControl
    import CESystems



import threading
from tkinter import filedialog
import tkinter as tk


class Application(tk.Frame):

    message_header = "Please enter the number for the option below and press 'Send Command' \n"

    def __init__(self, master=None, controller=None, default='Simple UI'):
        super().__init__(master)
        self.master = master
        self.root = tk.Tk()
        self.pack()
        self.create_widgets(default)
        self.controller = controller

    def create_widgets(self, msg = None):
        self.message = tk.Text(self)
        if msg is None:
            msg = ""

        self.message.insert(tk.INSERT, self.message_header + msg)
        self.message.pack()

        self.input = tk.Entry(self)
        self.input.pack()

        self.send_button = tk.Button(self)
        self.send_button['command'] = self.send_command
        self.send_button['text'] = 'Send Command'
        self.master.bind('<Return>', self.send_command)

        self.send_button.pack()


    def send_command(self, *args):
        self.controller.send_command(self.input.get())
        self.input.delete(0, 'end')


class Controller:

    def __init__(self):
        self.root=tk.Tk()
        self.model = Model(controller=self)
        self.view = Application(master=self.root, controller=self, default=self.model.default_text)

        self.view.mainloop()

    def send_command(self, text):
        self.model.interpret(text)

    def send_response(self, msg):
        self.view.message.delete(2.0, tk.END)
        self.view.message.insert(tk.INSERT, msg)

    def update(self):
        self.view.master.after(1000, self.model.run_update)


class Model:
    main_menu = """
        1: Set Directory
        2: Set Exposure
        3: Set Time
        4: Set Voltage
        5: Start LiveView
        6: Snap Image
        7: Run CE
        """
    voltage_menu = """
    
    1: Set Electrode 1 
    2: Set Electrode 2 
    3: Set Electrode 3 
    4: Set Electrode 4 
    """
    exposure_menu = """
    \n \n \n \n
    Enter the exposure setting in milliseconds: 
    """
    time_menu = """
    \n \n \n \n
    Enter the total time to run voltage & acquire images in seconds: 
    """

    electrode_menu = """
    \n \n \n \n 
    Enter the new voltage for the electrode in Volts:
    """

    running_menu = """
    CE is Running: {} seconds remaining of {} second run time. 
    Enter 1 to stop
    """

    def __init__(self, controller):


        self.controller = controller
        self.hardware = CESystems.Chip_TiEclipseSeattle()

        # Menu Variables
        self.menu_choice = 'Main'
        self.default_text = self.main_menu
        self.voltage_menu = "\n"
        for idx, _ in enumerate(self.hardware.power_supply_control.channels):
            self.voltage_menu += "{}: Set Electrode {} \n".format(idx, idx)

        # Parameters
        self.run_time = 10 # Time to acquire images and run voltage in seconds
        self.save_dir = None # Save directory
        self.im_num = 0 # integer vaue that increases with every image taken

        #Threading Parameters
        self._threads = {}
        self.is_running=threading.Event()
        self._remaining_time = 0



    def interpret(self, text):

        if self.menu_choice == 'Main':
            msg = self.main_menu_options(text)

        elif self.menu_choice == 'Voltage':
            msg = self.voltage_menu_options(text)

        elif self.menu_choice=='Exposure':
            msg = self.exposure_menu_options(text)

        elif self.menu_choice=='Time':
            msg = self.time_menu_options(text)

        elif self.menu_choice=='Electrode':
            msg = self.electrode_menu_options(text)

        elif self.menu_choice=='Running':
            self.running_menu_options(text)
            return
        self.controller.send_response(msg)

    def main_menu_options(self, text):
        """
        :param text:
        :return:
        """
        resp = int(text)

        if resp == 1:
            dir_path = filedialog.askdirectory()
            self.save_dir = dir_path
            return self.main_menu
        elif resp == 2:
            self.menu_choice='Exposure'
            pre_msg = "\n Current Exposure is {:.2f} \n".format(self.hardware.get_exposure())
            return pre_msg + self.exposure_menu
        elif resp == 3:
            self.menu_choice='Time'
            pre_msg = "\n Current run time is {:.2f} \n ".format(self.run_time)
            return pre_msg + self.time_menu
        elif resp == 4:
            self.menu_choice = 'Voltage'
            pre_msg = "\n\n"
            for idx, _ in enumerate(self.hardware.power_supply_control.channels):
                pre_msg += "  Electrode {}: {:.1f} Volts \n".format(idx, self.hardware.get_voltage_setting(idx))
            return pre_msg + self.voltage_menu
        elif resp == 5:
            self.hardware.start_live_feed()

        elif resp == 6:
            self.snap_and_save()

        elif resp == 7:
            self.menu_choice='Running'
            # Start the CE Run program
            self._threads['run'] = threading.Thread(target =self.run_CE, name='CERUN').start()
            # Create a Timer program
            self._remaining_time=self.run_time
            self.controller.update()
            #self._threads['update']=threading.Timer(1, self._run_update).start()
            return self.running_menu.format(self._remaining_time, self.run_time)

        return self.main_menu

    def exposure_menu_options(self, text):
        exp = float(text)
        self.hardware.set_exposure(exp)
        self.menu_choice='Main'
        pre_message = "\n Exposure set to {:.2f} ms \n".format(exp)
        return pre_message + self.main_menu

    def time_menu_options(self, text):
        run_time = float(text)
        self.run_time = run_time
        self.menu_choice = 'Main'
        pre_message = "\n Run time set to {:.2f} s \n".format(self.run_time)
        return pre_message + self.main_menu

    def voltage_menu_options(self, text):
        electrode = int(text)
        if electrode>=len(self.hardware.power_supply_control.channels):
            pre_msg = "\n\n  Electrode {} does not exist\n\n".format(electrode)
            self.menu_choice='Main'
            return pre_msg + self.main_menu
        self.electrode_choice = electrode
        self.menu_choice = 'Electrode'
        return self.electrode_menu

    def electrode_menu_options(self, text):
        voltage = float(text)
        pre_msg = "\n Electrode {} set to {:.1f}".format(self.electrode_choice, voltage)
        self.hardware.set_voltage(voltage/1000, self.electrode_choice)
        self.menu_choice= 'Main'
        return pre_msg + self.main_menu

    def running_menu_options(self, text):
        """ User can choose to end the run early. The is running event will trigger, and the
        CE run code will exit theloop.
        """
        if int(text)==1:
            self.hardware.stop_voltage()
            self.is_running.set()


    def snap_and_save(self):
        """ Snap and image and save the details

        ImageName =
        YYYYMMDD_HHMM_filter_obj_exposure_0000.tiff

        Directory specified by user, if directory has not been selected
        user will be prompted for one.

        """
        if self.save_dir is None:
            self.save_dir = filedialog.askdirectory()
        # Create the image name
        now = datetime.now()
        str_time = now.strftime("%H%M%S")
        filt = self.hardware.filter_get()
        exp = self.hardware.get_exposure()
        obj = 1 #todo need to iplment objective info class
        img_name = "{}_F{}_O{}_E{:.0f}_{:04d}.tiff".format(str_time, filt, obj, exp, self.im_num)
        file_path = os.path.join(self.save_dir, img_name)
        self.hardware.save_raw_image(file_path)
        self.log_data(img_name)
        self.im_num+=1

    def log_data(self, img_name):
        """ Logs the data to a CSV
        img_name, filter, objective, exposure, x, y, obj_z

        """
        # Log the data
        data_path = os.path.join(self.save_dir, 'Data.csv')
        if not os.path.exists(data_path):
            headers = True
        else:
            headers=False

        with open(data_path, 'a') as fout:
            if headers:
                fout.write('img_name,img_number,filter,objective,exposure,x_pos, y_pos,objective_z\n')
            xy = self.hardware.get_xy()
            obj_z = self.hardware.get_objective()
            obj = 1
            filt = self.hardware.filter_get()
            exp = self.hardware.get_exposure()
            fout.write('{},{},{},{},{},{},{},{}\n'.format(img_name,self.im_num, filt, obj, exp, xy[0],xy[1], obj_z))


    def run_CE(self):
        """
        Run The Microchip Electrophoresis Sequence.

        #todo While loop may need to be update to avoid frame skipping.

        :return:
        """

        # Set up the ADC channels for getting data, Start reading ADC

        # Make sure the camera is acquiring
        self.hardware.start_feed()
        # We will use the exposure to get our timing
        exposure = self.hardware.get_exposure()

        # Keep our images in arrays for now
        adjusted_imgs = []
        raw_imgs = []
        times = []

        #Create a reference timepoint
        self.hardware.clear_data()
        start_time = time.time()
        target_time = start_time + exposure / 1000
        self.hardware.power_supply_control.apply_changes()
        while time.time() - start_time < self.run_time and not self.is_running.is_set():
            # Get an image
            adjusted_imgs.append(self.hardware.get_image())
            raw_imgs.append(self.hardware.image_control.raw_img)
            # Record the time
            times.append(time.time()-start_time)
            # Sleep for a little bit
            target_time = better_sleep(target_time, exposure / 1000)
            print('Snap')

        # Save the data
        self._old_data=[raw_imgs, adjusted_imgs]
        self.hardware.power_supply_control.stop_voltage()
        if self.save_dir is None:
            self.save_dir = filedialog.askdirectory()
        now = datetime.now()
        save_image_data(self.save_dir, adjusted_imgs, raw_imgs, times, now, raw_vid=False, adj_folder=False)
        csv_data = '{}_voltage_current.csv'.format(now.strftime("%H%M%S"))
        self.hardware.save_data(os.path.join(self.save_dir, csv_data))

    def run_update(self):
        self._remaining_time -= 1
        if self._remaining_time>0 and not self.is_running.is_set():
            msg = self.running_menu.format(self._remaining_time, self.run_time)
            self.controller.send_response(msg)
            self.controller.update()
        else:
            self.menu_choice = 'Main'
            pre_message = '\n Run finished. \n'
            self.controller.send_response(pre_message + self.main_menu)

def save_image_data(save_dir, imgs, raw_imgs, times, now, raw_vid=False, adj_folder=False):
    """

    :param save_dir:
    :param imgs:
    :param raw_imgs:
    :param times:
    :param raw_vid:
    :param adj_folder:
    :return:
    """

    str_now = now.strftime("%H%M%S")
    labels = ['raw_', 'adjusted_']
    video_flags = [raw_vid, True]
    dir_flags = [True, adj_folder]

    for lbl, dataset, vid_flag, dir_flag in zip(labels, [raw_imgs, imgs], video_flags, dir_flags):
        if vid_flag:
            video_file = os.path.join(save_dir, lbl + str_now + '.avi')
            width, height = dataset[-1].shape
            # output the data to a video
            video = cv2.VideoWriter(video_file, 0, 5, (width, height))
            for frame in dataset:
                video.write(frame)
            video.release()
        if dir_flag:
            capture_folder = os.path.join(save_dir, lbl + str_now)
            os.mkdir(capture_folder)
            idx=0
            with open(os.path.join(save_dir,'times'+lbl+str_now+'.csv'), 'a') as fout:
                fout.write('time(ms), file_name\n')
                for frame,time_point in zip(dataset, times):
                    time_point = int(time_point*1000) # Convert to milliseconds
                    fname = os.path.join(capture_folder, lbl+"{:d}_{:05d}.tiff".format(time_point, idx))
                    io.imsave(fname, frame)
                    fout.write('{},{}\n'.format(time_point, fname))
                    idx+=1


def better_sleep(target, sample_time):
    """
    This is a more accurate sleep call, it takes into account time that has elapsed while gathering data
    :param moment: a object from time.time(), the last time better_sleep was run.
    :param SAMPLE_FREQ: The sampling frequency you wish to sample at
    :return:
    """
    while time.time() < target+(sample_time):
        #Sleep 1 milliseconds and check again
        time.sleep(0.01)
    return target + sample_time

ctl = Controller()
