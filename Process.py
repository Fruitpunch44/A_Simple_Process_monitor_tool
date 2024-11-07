import sys
import time
from socket import AF_INET
from socket import AF_INET6
from socket import SOCK_DGRAM
from socket import SOCK_STREAM
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from itertools import count
import psutil
from psutil._common import bytes2human
import argparse
import subprocess
from tabulate import tabulate
import logging
import os
import schedule

# create log file
log_file = "process_Log.txt"
log_dir = "Process_log_directory"
file_path = os.path.join(log_dir, log_file)

# check if logging directory already exists
if not os.path.exists(log_dir):
    os.mkdir(log_dir)
    print('Have successfully created the logging directory')

# create log options
logging.basicConfig(filename=file_path, level=logging.INFO,
                    format="%(asctime)s:%(filename)s:%(message)s")

# create options to use
parse = argparse.ArgumentParser(description='A simple process monitoring tool')

# various arguments that can be used
parse.add_argument('-K', '--Kill', type=str, help='Select the process you want to kill')
parse.add_argument('-S', '--Search', type=str, help='search for a given process')
parse.add_argument('-St', '--Start', type=str, help='start a given process')
parse.add_argument('-L', '--List', help='list all currently running process ', action='store_true')
parse.add_argument('-F', '--Filter', type=str, help='filter out particular process')
parse.add_argument('-M', '--Memory', help='check memory information', action='store_true')
parse.add_argument('-MON', '--Monitor', help='Display all methods continuously i.e enter monitor mode'
                   , action='store_true')
parse.add_argument('-C', '--Graph', help='display cpu utilization in real time', action='store_true')
# parse the arguments
args = parse.parse_args()


def display_banner() -> None:
    Banner = """
   ╔═══════════════════════════════════════════════════════════════════╗
   ║                                                                   ║
   ║                                                                   ║
   ║                                                                   ║   
   ║    _____                __  __             _ _                    ║   
   ║    |  __ \              |  \/  |           (_) |                  ║   
   ║    | |__) | __ ___   ___| \  / | ___  _ __  _| |_ ___  _ __       ║   
   ║    |  ___/ '__/ _ \ / __| |\/| |/ _ \| '_ \| | __/ _ \| '__|      ║   
   ║    | |   | | | (_) | (__| |  | | (_) | | | | | || (_) | |         ║   
   ║    |_|   |_|  \___/ \___|_|  |_|\___/|_| |_|_|\__\___/|_|         ║          
   ║                                                                   ║   
   ║                                                                   ║   
   ║                                                                   ║    
   ║     Process & Network Monitor - View processes and network        ║
   ║                                 connections                       ║
   ║                                                                   ║
   ╚═══════════════════════════════════════════════════════════════════╝
"""
    print(Banner)


# create monitor class that takes arguments from args
class Monitor:
    plt.style.use('Solarize_Light2')

    def __init__(self, args) -> None:
        # set init variables for the arguments to the passed and
        # for the plots
        self.args = args
        self.fig, (self.ax_cpu, self.ax_memory) = plt.subplots(2, 1, figsize=(8, 8))
        self.y_axis_cpu = []
        self.x_axis_cpu = []
        self.y_axis_memory = []
        self.x_axis_memory = []
        self.set_up_plot_cpu()
        self.set_up_plot_memory_usage()
        # do not know if this is doing anything
        self.index = count()

    @staticmethod
    # convert from bytes to readable size such as kb,mb,gb
    # gotten from docs
    def convert_bytes(byte):
        for name in byte._fields:
            value = getattr(byte, name)
            if name != 'percent':
                value = bytes2human(value)
                print('%-10s : %7s' % (name.capitalize(), value))

    # search for processes
    def search_process(self) -> any:
        list_of_processes = []
        for process in psutil.process_iter():
            try:
                if process.name() == self.args.Search:
                    list_of_processes.append(process)
                    logging.info(f'{args.Search} successfully found')
                    print(f'found process {args.Search} with pid: {process.pid}\n'
                          f'user:{process.username()}'
                          f'status:{process.status()}')
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f'error in searching for process {args.Search} {e}')
                logging.info(f'error in searching for process {args.Search} {e}')
        return self.args.Search

    @staticmethod
    def list_all_processes() -> None:
        # list all process and return their pids,name and memory usage
        while True:
            data = []
            try:
                for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'status']):
                    # append all process to the data list
                    data.append([proc.pid, proc.name(), bytes2human(proc.memory_info().rss), proc.status()])
                try:
                    # create a simple tabular display for processes
                    # clears the terminal every time the table is printed to
                    # simulate a live menu screen
                    print("\033c", end='')

                    table = tabulate(data,
                                     headers=["PID", "NAME", "MEMORY USAGE", "STATUS"],
                                     tablefmt="fancy_grid",
                                     numalign="right")

                    print(table)
                    time.sleep(2)

                except KeyboardInterrupt:
                    print(f'monitoring was stopped')
                    logging.info(f'monitoring was stopped')
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f'could not list process {e}')
                logging.error(f'could not list process {e}')

    def kill_process(self):
        # select the process you want to kill
        for proc in psutil.process_iter():
            try:
                if proc.name() == self.args.Kill:
                    option = input('Are you sure you want to kill this process \n'
                                   '1 -Yes\n'
                                   '2-No\n')
                    if option == '1':
                        proc.kill()
                        print(f'killed {self.args.Kill} successfully with the pid {proc.pid}')
                        return
                    else:
                        print('Cancelled by user')
            except psutil.NoSuchProcess:
                print(f'could not find process {self.args.Kill} error in terminating')
                logging.error(f'could not find process {self.args.Kill} error in terminating')

    def start_process(self) -> None:
        # use sub process to create a particular process
        try:
            process = subprocess.Popen([self.args.Start], shell=True, stderr=subprocess.PIPE, text=True)
            print(f'successfully started {self.args.Start} with PID:{process.pid}')
        except subprocess.SubprocessError as e:
            print(f'unable to start process {self.args.Start} : {e}')
            logging.error(f'unable to start process {self.args.Start} : {e}')

    def check_memory_info(self):
        # print out the memory info in human-readable form
        # convert_bytes was gotten from the docs
        print('Memory info *********')
        return self.convert_bytes(psutil.virtual_memory())

    @staticmethod
    def check_disk_info():
        # show all physical disk partitions available
        data = []
        for part in psutil.disk_partitions(all=False):
            usage = psutil.disk_usage(part.mountpoint)
            data.append([part.device, bytes2human(usage.total),
                         bytes2human(usage.used),
                         bytes2human(usage.free)])
        table = tabulate(data,
                         headers=['Device', 'Total Space', 'Used', 'free'],
                         tablefmt='fancy_grid',
                         numalign='right')
        print(table)

    def set_up_plot_cpu(self) -> None:
        # create label,title and set the y-axis limit
        # crate grid so the graph is easier to look at
        self.ax_cpu.set_xlabel('Seconds (s)')
        self.ax_cpu.set_ylabel('CPU Utilization (%)')
        self.ax_cpu.set_title('CPU')
        self.ax_cpu.set_ylim(0, 100)
        self.ax_cpu.grid(True, linewidth=1)

    def set_up_plot_memory_usage(self) -> None:
        # create label,title and set the yaxis limit
        self.ax_memory.set_xlabel('Seconds (s)')
        self.ax_memory.set_ylabel('Memory (GB)')
        self.ax_memory.set_title('Memory')
        self.ax_memory.set_ylim(0, psutil.virtual_memory().total / (1024 * 1024 * 1024))  # max ram limit in gb
        self.ax_memory.grid(True, linewidth=1)

    def animate_memory_usage(self, frame) -> list:
        # set the used memory to be converted from bytes to gb
        used_mem = psutil.virtual_memory().used / (1024 * 1024 * 1024)  # current ram being used in gb
        self.y_axis_memory.append(used_mem)
        self.x_axis_memory.append(next(self.index))  # 1 second increment in the x-axis

        line2 = self.ax_memory.plot(self.x_axis_memory, self.y_axis_memory, color='g', linewidth=1)

        # display legend
        self.ax_cpu.legend(['CPU utilization'])

        # set_limit_size
        size_limit = 20
        self.x_axis_memory = self.x_axis_memory[-size_limit:]
        self.y_axis_memory = self.y_axis_memory[-size_limit:]

        # line object to be passed to the funcAnimation function
        return line2

    def animate_cpu(self, frame) -> list:

        cpu_uti = psutil.cpu_percent(interval=1)
        self.y_axis_cpu.append(cpu_uti)
        self.x_axis_cpu.append(next(self.index))
        # plot the line with the given info from cpu_util and the timer(1sec)
        line = self.ax_cpu.plot(self.x_axis_cpu, self.y_axis_cpu, color='b', linewidth=1)

        self.ax_memory.legend(['Memory Usage'])  # display legend

        # set_limit_size
        size_limit = 20
        self.x_axis_cpu = self.x_axis_cpu[-size_limit:]
        self.y_axis_cpu = self.y_axis_cpu[-size_limit:]

        # line object to be passed to the funcAnimation function
        return line

    def all_plots(self, frame):
        # combine both the plots of the cpu and memory so it can be rendered together
        cpu_use = self.animate_cpu(frame)
        memory_use = self.animate_memory_usage(frame)
        return cpu_use + memory_use

    def start_animation_both(self):
        # animate both plots with a single FuncAnimation
        # set rendering interval to 500ms
        ani = animation.FuncAnimation(self.fig, self.all_plots, interval=500)
        plt.tight_layout()
        plt.show()

    def filter(self):
        # filter by actively running processes
        if self.args.Filter == 'Filter Running':
            running_filter = []
            for p in psutil.process_iter(['name', 'status']):
                if p.status() == psutil.STATUS_RUNNING:
                    running_filter.append([p.pid, p.name(), p.status()])
            table = tabulate(running_filter,
                             headers=["PID", "NAME", "MEMORY USAGE", "STATUS"],
                             tablefmt="fancy_grid",
                             numalign="right")
            print(table)

        # filter by memory usage
        elif self.args.Filter == 'Filter Memory Usage':
            # set threshold
            threshold = 100 * 1024 * 1024  # 100mb limit
            mem_filter = []
            for p in psutil.process_iter(['pid', 'name', 'memory_info']):
                if p.memory_info().rss > threshold:
                    mem_filter.append([p.pid, p.name(), bytes2human(p.memory_info().rss)])
                    logging.info(
                        f'pid:{p.pid} name:{p.name()} is using {bytes2human(p.memory_info().rss)} '
                        f'which is more than the threshold:{bytes2human(threshold)}')
            table = tabulate(mem_filter,
                             headers=["PID", "NAME", "MEMORY USAGE", "STATUS"],
                             tablefmt="fancy_grid",
                             numalign="right")
            print(table)

        elif self.args.Filter == 'Filter Zombie':
            zombie_filter = []
            # filter by actively running processes
            for p in psutil.process_iter(['pid', 'name', 'status']):
                try:
                    if p.status() == psutil.STATUS_ZOMBIE:
                        zombie_filter.append([p.pid, p.name(), p.status()])
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    logging.error(f'an error occurred {e}')
            table = tabulate(zombie_filter,
                             headers=["PID", "NAME", "MEMORY USAGE", "STATUS"],
                             tablefmt="fancy_grid",
                             numalign="right")

            print(table)

        elif self.args.Filter == 'Filter Sleeping':
            # filter by actively running processes
            sleeping_filter = []
            for p in psutil.process_iter(['pid', 'name', 'status']):
                try:
                    if p.status() == psutil.STATUS_SLEEPING:
                        sleeping_filter.append([p.pid, p.name(), p.status()])
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    logging.error(f'an error occurred {e}')

            table = tabulate(sleeping_filter,
                             headers=["PID", "NAME", "MEMORY USAGE", "STATUS"],
                             tablefmt="fancy_grid",
                             numalign="right")
            print(table)

        elif self.args.Filter == 'Filter Cpu Usage':
            cpu_filter = []
            threshold = int(input('enter the threshold you wish to use: '))
            for p in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    # generally must process don't consume more than 10% while idle
                    # but under intense load it's a different case
                    if p.cpu_percent() > threshold:
                        cpu_filter.append([p.pid, p.name(), p.cpu_percent(interval=1)])
                        logging.info(f'PID:{p.pid} NAME:{p.name()} has high cpu usage {p.cpu_percent(interval=1)}')
                    else:
                        # if no process surpasses the threshold the loop is terminated
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    logging.error(f'an error occurred{e}')
            table = tabulate(cpu_filter,
                             headers=["PID", "NAME", "CPU_PERCENT(%)"],
                             tablefmt="fancy_grid",
                             numalign="right")
            print(table)

    # display process that have network connection
    @staticmethod
    def network():
        # create protocol map to make the protocol being returned by
        # connection type and connect family to be readable
        proto_map = {
            (AF_INET, SOCK_STREAM): 'TCP',
            (AF_INET, SOCK_DGRAM): 'UDP',
            (AF_INET6, SOCK_STREAM): 'TCP6',
            (AF_INET6, SOCK_DGRAM): 'UDP6'
        }
        try:
            data = []
            for proc in psutil.process_iter(['pid', 'name', 'status']):
                connections = proc.connections()
                for connection in connections:
                    # check to see if the process is connecting to a remote address
                    # if not return N/A
                    if connection.raddr:
                        remote_addr = connection.raddr
                    else:
                        remote_addr = 'N/A'
                    data.append([proc.pid, proc.name(), proc.status(), proto_map[(connection.family, connection.type)],
                                 connection.laddr, remote_addr])
                    # show process information pid,name,status
            table = tabulate(data,
                             headers=["PID", "NAME", "STATUS", "PROTOCOL", "LOCAL ADDRESS", "REMOTE ADDRESS "],
                             numalign='right',
                             tablefmt='fancy_grid'
                             )
            print(table)
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.Error) as e:
            logging.error(f'an error occurred {e}')

    @staticmethod
    def show_windows_services():
        data = []
        # loop through all Windows services and display info about them
        for services in list(psutil.win_service_iter()):
            try:
                service_info = services.as_dict()
                data.append([service_info['name'], service_info['binpath'][:60],
                             service_info['status'], service_info['start_type'],
                             service_info['description'][:300]])  # why are some descriptions so long this limit is fine
            except (psutil.AccessDenied, psutil.NoSuchProcess) as e:
                logging.error(f'an error occurred {e}')
                print(f'ERROR{e}')

        table = tabulate(data,
                         headers=["NAME", "BINPATH", "STATUS", "START TYPE", "DESCRIPTION"],
                         numalign='left',
                         tablefmt='fancy_grid')
        print(table)

    @staticmethod
    def search_for_service(name):
        data = []
        try:
            search = psutil.win_service_get(name)
            service_info = search.as_dict()  # shows all the information of the service as a dictionary
            data.append([service_info['name'], service_info['binpath'][:60],
                         service_info['status'], service_info['start_type'],
                         service_info['description'][:300]])  # to manage excess spaces on the table
            table = tabulate(data,
                             headers=["NAME", "BINPATH", "STATUS", "START TYPE", "DESCRIPTION"],
                             numalign='left',
                             tablefmt='fancy_grid')
            print(table)
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            print(f'error{e}')

    def loop(self) -> None:
        # loop function if no other arguments are provided besides monitor
        if self.args.Monitor:
            print(f'**Entering monitor mode')
            while True:
                display_banner()
                try:
                    # don't know if I show just make a map for this
                    print(f'**enter what you want to monitor \n'
                          f'1:Show all Processes\n'
                          f'2:Filter Processes\n'
                          f'3:Start Process\n'
                          f'4:Kill Process\n'
                          f'5:Search For Process\n'
                          f'6:Provide Memory info\n'
                          f'7:Display cpu utilization/Memory usage\n'
                          f'8:Show Process network connections\n'
                          f'9:Show Disk usage\n'
                          f'10:Exit\n'
                          )
                    user = input('enter your option: ')

                    if user == '1':
                        self.list_all_processes()

                    elif user == '2':
                        # filter map
                        # dictionary keys for filter options
                        filter_options = {
                            '1': 'Filter Running',
                            '2': 'Filter Memory Usage',
                            '3': 'Filter Zombie',
                            '4': 'Filter Sleeping',
                            '5': 'Filter Cpu Usage'
                        }
                        print('these are your filter options\n'
                              '1-Filter Running\n'
                              '2-Filter memory usage\n'
                              '3-Filter Zombie\n'
                              '4-Filter Sleeping\n'
                              '5-Filter Cpu Usage\n')

                        filter_option: str = input('enter a filter option: ')
                        if filter_option in filter_options:
                            self.args.Filter = filter_options[filter_option]
                            self.filter()
                        else:
                            print('nothing was selected or user chose an invalid input')
                            logging.info(f'The user did not choose any filter option'
                                         f' or selected the wrong one {filter_option}')

                    elif user == '3':
                        Process_name: str = input('enter a Process to Start: ')
                        self.args.Start = Process_name
                        self.start_process()

                    elif user == '4':
                        Process_name: str = input('enter a Process to Terminate: ')
                        self.args.Kill = Process_name
                        self.kill_process()

                    elif user == '5':
                        Process_name: str = input('enter a Process to search for: ')
                        self.args.Search = Process_name
                        self.search_process()

                    elif user == '6':
                        self.check_memory_info()

                    elif user == '7':
                        self.start_animation_both()

                    elif user == '8':
                        print('****show connections***')
                        self.network()

                    elif user == '9':
                        print('Disk Usage')
                        self.check_disk_info()

                    elif user == '10':
                        print('****Close Program***')
                        sys.exit(1)

                    else:
                        print('no input was provided ')
                        break
                except KeyboardInterrupt as e:
                    print(f'{e}')
                    logging.info(f'{e}')

#work in progress
class Task_Scheduler:
    def __init__(self, args):
        self.args = args

    #work in progress
    def virus_updates(self):
        pass
    #work in o
    def run_program(self):
        #script
        #exe
        pass

    @staticmethod
    def schedule():
        list_of_current_schedules = {}

        # get username and description of task
        name: str = input('what do you want to name this task: ')
        description: str = input('what is the description of the task: ')
        # specifying the time and occurrence of when to run the task
        date_map = {
            "1": "daily",
            "2": "Weekly",
            "3": "Monthly",
            "4": "One Time",
        }
        print(f'options:\n {list(date_map.items())}')
        options: str = input('Enter an option:')
        if options in date_map:
            schedule_time = date_map[options]
            # yes this is not optimal will change later
            if schedule_time == 'daily':
                frequency: int = int(input("Enter the interval frequency you want: "))
                # TIME must be in 24-hour format
                TIME: str = input("Enter the time you want to use: ")
                schedule.every(frequency).day.at(TIME).do()
                list_of_current_schedules[name]={
                    'name': name,
                    'description': description,
                    'schedule_type': frequency,
                    'scheduled_time': TIME,
                }
            elif schedule_time == 'weekly':
                # how often you want to run it weekly
                frequency: int = int(input("Enter the interval frequency you want: "))
                # TIME must be in 24-hour format
                TIME: str = input("Enter the time you want to use: ")
                schedule.every(frequency).weeks.at(TIME).do()
                list_of_current_schedules[name] = {
                    'name': name,
                    'description': description,
                    'schedule_type': frequency,
                    'scheduled_time': TIME,
                }
            elif schedule_time == 'Monthly':
                # same as above but you just want to use > 4 for the frequency
                # alongside multiple of 4 i.e 4=1 month,8=2 month
                frequency: int = int(input("Enter the interval frequency you want: "))
                # TIME must be in 24-hour format
                TIME: str = input("Enter the time you want to use: ")
                schedule.every(frequency).weeks.at(TIME).do()
                list_of_current_schedules[name] = {
                    'name': name,
                    'description': description,
                    'schedule_type': frequency,
                    'scheduled_time': TIME,
                }
            elif schedule_time == 'One Time':
                frequency: int = int(input("Enter the interval frequency you want: "))
                # TIME must be in 24-hour format
                TIME: str = input("Enter the time you want to use: ")
                schedule.every(frequency).day.at(TIME).do()
                list_of_current_schedules[name] = {
                    'name': name,
                    'description': description,
                    'schedule_type': frequency,
                    'scheduled_time': TIME,
                }
            else:
                print('Invalid Options')

        # what action should be performed
        action_map = {
            "1": "Run Program",
            "2": "Perform Virus check"
        }
        # path to the program to be executed or run
        # save the info to a file to keep track


def main():
    monitor = Monitor(args)

    # if no args are provided aside from -MON
    if args.Monitor:
        monitor.loop()
    # other arguments
    else:
        if args.Filter:
            monitor.filter()

        elif args.Memory:
            monitor.check_memory_info()

        elif args.Start:
            monitor.start_process()

        elif args.Search:
            monitor.search_process()

        elif args.Graph:
            monitor.start_animation_both()

        elif args.Kill:
            monitor.kill_process()

        else:
            print('no arguments were passed please select an argument\n'
                  'please use the -h for more assistance')


if __name__ == '__main__':
    main()

monn = Monitor(args=None)
